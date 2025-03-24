# Copyright © 2017-2023 Quantum Interface (quantuminterface@ipe.kit.edu)
# Richard Gebauer, IPE, Karlsruhe Institute of Technology
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import json
import os
import re

import pytest

import qiclib.packages.utility as util
from qiclib.code.qi_command import (
    AssignCommand,
    ParallelCommand,
    PlayCommand,
    PlayReadoutCommand,
    RecordingCommand,
    SyncCommand,
)
from qiclib.code.qi_jobs import (
    Assign,
    Else,
    ForRange,
    If,
    Parallel,
    Play,
    PlayReadout,
    QiCell,
    QiCellProperty,
    QiCells,
    QiFrequencyVariable,
    QiGate,
    QiJob,
    QiResult,
    QiSample,
    QiStateVariable,
    QiTimeVariable,
    QiVariable,
    Recording,
    RotateFrame,
    Store,
    Sync,
    Wait,
)
from qiclib.code.qi_pulse import QiPulse, ShapeLib
from qiclib.code.qi_seq_instructions import SeqTrigger


def test_no_length_inside_job():
    with QiJob():
        q = QiCells(1)
        assert isinstance(q[0]["nothing here"], QiCellProperty)


class TestQiSampleCell:
    @pytest.fixture
    def sample(self):
        sample = QiSample(1)
        sample[0].cell_id = 42
        sample[0]["recording_length"] = 400e-9
        return sample[0]

    def test_length(self, sample):
        assert sample["recording_length"] == 400e-9

    def test_no_length(self, sample):
        with pytest.raises(KeyError):
            sample["nothing here"]

    def test_new_length(self, sample):
        sample["pi_pulse"] = 48e-9
        assert sample["pi_pulse"] == 48e-9

    def test_new_recording_length(self, sample):
        sample["recording_length"] = 48e-9
        assert sample["recording_length"] == 48e-9

    def test_export_cell(self):
        new_sample = QiSample(1)[0]
        new_sample["electrical_delay"] = 42e-9
        new_sample["recording_length"] = 400e-9
        assert new_sample.get_properties() == {
            "electrical_delay": 4.2e-08,
            "recording_length": 4e-07,
        }

    def test_import_cell(self):
        new_sample = QiSample(1)
        new_sample[0].update(
            electrical_delay=200e-9, recording_length=5e-07, new_prop=42e-9
        )

        assert new_sample[0]["electrical_delay"] == 200e-9
        assert new_sample[0]["recording_length"] == 500e-9
        assert new_sample[0]["new_prop"] == 42e-9

    def test_export_qi_cells(self):
        s = QiSample(2)

        s[0]["pi_pulse"] = 42e-9

        expected = {
            "cells": [
                {
                    "pi_pulse": 4.2e-08,
                },
                {},
            ],
            "cell_map": [0, 1],
        }

        assert s.to_dict() == expected

    def test_import_qi_cells(self):
        s = QiSample.loads(
            '{"cells": [{"electrical_delay": 2.0e-7, "recording_length": 5e-07, "pi_pulse": 4.2e-08}, {"electrical_delay": 0.0, "recording_length": 4e-07}]}'
        )

        assert s[0]["electrical_delay"] == 200e-9
        assert s[0]["recording_length"] == 500e-9
        assert s[0]["pi_pulse"] == 42e-9

        assert s[1]["electrical_delay"] == 0
        assert s[1]["recording_length"] == 400e-9
        with pytest.raises(KeyError):
            s[1]["pi_pulse"]

    def test_export_file(self):
        s = QiSample(1)
        s[0]["electrical_delay"] = 42e-9
        s[0]["recording_length"] = 400e-9

        fp = os.path.join(os.path.dirname(__file__), "test_files/test_output.json")

        if os.path.exists(fp):
            os.remove(fp)

        s.save(fp)

        with open(fp) as file:
            file_data = json.load(file)

        assert file_data == {
            "cells": [
                {
                    "electrical_delay": 42e-9,
                    "recording_length": 4e-07,
                }
            ],
            "cell_map": [0],
        }

        # export again
        s[0]["electrical_delay"] = 41e-9

        with pytest.raises(FileExistsError):
            s.save(fp)

        s.save(fp, overwrite=True)

        with open(fp) as file:
            file_data = json.load(file)

        assert file_data == {
            "cells": [
                {
                    "electrical_delay": 4.1e-08,
                    "recording_length": 4e-07,
                }
            ],
            "cell_map": [0],
        }

        os.remove(fp)

    def test_load_from_file(self):
        path = os.path.join(os.path.dirname(__file__), "test_files/properties_ok.json")
        s = QiSample.load(path)

        assert s[0]["electrical_delay"] == 200e-9
        assert s[0]["recording_length"] == 500e-9
        assert s[0]["pi_pulse"] == 42e-9

    def test_load_file_error(self):
        s = QiSample(1)

        with pytest.raises(json.JSONDecodeError):
            path = os.path.join(
                os.path.dirname(__file__), "test_files/properties_error.json"
            )
            s.load(path)

    def test_import_qi_cells_error(self):
        with pytest.raises(
            ValueError, match="Imported JSON string does not contain 'cells'."
        ):
            QiSample.loads(
                '{"electrical_delay": 0.0, "recording_length": 4e-07, "pi_pulse": 4.2e-08}'
            )


class TestQiCommand:
    @pytest.fixture
    def job(self):
        with QiJob() as job:
            yield job

    @pytest.fixture
    def cell(self, job):
        cell = QiCell(42)
        cell["electrical_delay"] = 0
        cell["recording_length"] = 400e-9
        return cell

    def test_recording_length(self, cell):
        rec = RecordingCommand(
            cell,
            "result",
            None,
            length=cell["recording_length"],
            offset=cell["electrical_delay"],
        )

        assert cell["recording_length"] == rec.length

    def test_recording_error(self, cell):
        # Raises error: RecordingCommand needs state variable
        var = QiTimeVariable()
        with pytest.raises(TypeError):
            _rec = RecordingCommand(
                cell,
                None,
                var,
                length=cell["recording_length"],
                offset=cell["electrical_delay"],
            )

    def test_recording_state(self, cell):
        var = QiStateVariable()

        rec = RecordingCommand(
            cell,
            None,
            var,
            length=cell["recording_length"],
            offset=cell["electrical_delay"],
        )

        assert rec.uses_state

        # Test also with additional QiResult supplied
        rec = RecordingCommand(
            cell,
            "result",
            var,
            length=cell["recording_length"],
            offset=cell["electrical_delay"],
        )

        assert rec.uses_state

    def test_assign_error(self, job):
        # Raises error: Cannot assign to state variable
        var = QiStateVariable()
        with pytest.raises(
            TypeError,
        ):
            Assign(var, 1)

        with pytest.raises(
            TypeError, match="Target of Assign can only be a QiVariable."
        ):
            Assign(1, 1)

        with pytest.raises(
            TypeError, match="Target of Assign can only be a QiVariable."
        ):
            q = QiCell(31)
            Assign(q, 1)

    def test_ForRange_end_value_warning(self, job, cell):
        # Warns that end value 0 is not included
        var = QiTimeVariable()
        with ForRange(var, 20e-9, 0, -4e-9):
            Wait(cell, var)

        with pytest.warns(
            UserWarning, match="End value of 0 will not be included in ForRange."
        ):
            job.__exit__(None, None, None)

    def test_ForRange_var_start_end_warning(self, cell):
        # Warns that unrolling is not supported for variable start/end times
        var = QiTimeVariable()
        var2 = QiTimeVariable()
        with pytest.raises(
            RuntimeError,
            match="Loop variable can not be used as start value",
        ):
            with ForRange(var, var, var2, -4e-9):
                Wait(cell, var)

        with pytest.raises(
            RuntimeError,
            match="Loop variable can not be used as end value",
        ):
            with ForRange(var, var2, var, -4e-9):
                Wait(cell, var)

    def test_ForRange_error(self):
        with (
            pytest.raises(
                RuntimeError,
                match=re.escape(
                    "When using QiTimeVariables define step size as multiple of 4 ns. (It is currently off by 1 ns.)"
                ),
            ),
            pytest.warns(
                UserWarning, match="End value of 0 will not be included in ForRange."
            ),
        ):
            with QiJob():
                cells = QiCells(1)
                var = QiTimeVariable()
                with ForRange(var, 20e-9, 0, -3e-9):
                    Wait(cells[0], var)

    def test_ForRange_state_error(self, cell):
        # Raises error: step must be multiple of 4e-9
        var = QiStateVariable()
        with pytest.raises(TypeError):
            with ForRange(var, 20e-9, 0, -4e-9):
                Wait(cell, var)

    def test_ForRange_Parallel_var_warning(self, cell):
        # Raises error: step must be multiple of 4e-9
        var = QiTimeVariable()
        warning_msg = r"Loop variable inside Parallel Context Manager might result in unexpected behaviour\. Please unroll loop or change variable"
        with pytest.raises(RuntimeError, match=warning_msg):
            with ForRange(var, 52e-9, 0, -4e-9):
                with Parallel():
                    Play(cell, QiPulse(42e-9))
                with Parallel():
                    Wait(cell, var)

    def test_ForRange_OK(self, cell):
        var = QiTimeVariable()
        with ForRange(var, 0, 100e-9, 24e-9):
            Wait(cell, var)

    def test_ForRange_negative_OK(self):
        with pytest.warns(
            UserWarning, match="End value of 0 will not be included in ForRange."
        ):
            with QiJob():
                cells = QiCells(1)
                var = QiTimeVariable()
                with ForRange(var, 100e-9, 0, -20e-9):
                    Wait(cells[0], var)

    def test_for_range_definition_error(self, job):
        var = QiVariable(int)
        with pytest.raises(ValueError):
            ForRange(var, 0, 5, -1)

        with pytest.raises(ValueError):
            ForRange(var, 5, 0, 1)

        with pytest.raises(ValueError):
            ForRange(var, 0, 5, 0)


class TestQiJobDescription:
    def test_QiVariable_init(self):
        value = 2
        with QiJob() as test:
            _var1 = QiVariable(int, value)

        cmd = test.commands[1]

        assert isinstance(cmd, AssignCommand)
        assert cmd._value == value

    def test_QiTimeVariable_init(self):
        value = 200e-9
        with QiJob() as test:
            _var1 = QiTimeVariable(value)

        cmd = test.commands[1]

        assert isinstance(cmd, AssignCommand)
        assert cmd.value.value == util.conv_time_to_cycles(value)

    def test_if_else_OK(self):
        with QiJob():
            var1 = QiVariable(int)
            with If(var1 > 3) as if_cm:
                Assign(var1, 0)
            with Else():
                Assign(var1, 0)

        assert len(if_cm._else_body) == 1
        assert if_cm.is_followed_by_else()

    def test_recording_OK(self):
        with QiJob(skip_nco_sync=True) as rec_job:
            q = QiCells(1)
            Recording(q[0], 4e-9, save_to="test")

        cmd = rec_job.commands[0]

        assert isinstance(cmd, RecordingCommand)
        assert cmd.length == 4e-9
        assert not cmd.follows_readout

    def test_recording_after_readout(self):
        with QiJob(skip_nco_sync=True) as rec_job:
            q = QiCells(1)
            PlayReadout(q[0], QiPulse(4e-9))
            Recording(q[0], 4e-9, save_to="test")

        cmd = rec_job.commands[0]
        assert isinstance(cmd, PlayReadoutCommand)
        assert isinstance(cmd.recording, RecordingCommand)

    def test_multiple_qicells_calls_Error(self):
        with pytest.raises(
            RuntimeError, match="Can only register one set of cells at a QiJob."
        ):
            with QiJob():
                _q = QiCells(1)
                _p = QiCells(1)

    def test_qicells_in_multiple_jobs_Error(self):
        with QiJob():
            q = QiCells(1)
            q[0]["test"] = 100e-9

        with pytest.raises(
            RuntimeError,
            match="Tried setting values for cells registered to other QiJob",
        ):
            with QiJob():
                q[0]["test"] = 200e-9

        with pytest.raises(
            RuntimeError,
            match="Tried getting values for cells registered to other QiJob",
        ):
            with QiJob():
                _length = q[0]["test"]

    def test_different_qi_cell_values_no_overwrite(self):
        with QiJob() as test1:
            q = QiCells(1)
            q[0]["test"] = 100e-9

        with QiJob() as test2:
            q = QiCells(1)
            q[0]["test"] = 200e-9

        assert test1.cells[0]._properties.get("test") == 100e-9
        assert test2.cells[0]._properties.get("test") == 200e-9

    def test_single_recording_box_retrieval(self):
        with QiJob() as rec_job:
            q = QiCells(1)
            Recording(q[0], 4e-9, save_to="data0")
            q[0]._result_container["data0"].data = [42]

        result = rec_job.cells[0].data()  # returns dict of all data boxes

        assert result.get("data0") == [42]

        result = rec_job.cells[0].data(
            "data0"
        )  # returns data of result box with name data0

        assert result[0] == 42

        # After build should be the same
        rec_job._build_program()

        result = rec_job.cells[0].data()  # returns list of all data boxes

        assert len(result.get("data0")) == 0  # reset after build_program

    def test_single_recording_box_retrieval_string_init(self):
        with QiJob() as rec_job:
            q = QiCells(1)
            Recording(q[0], 4e-9, save_to="data0")
            q[0]._result_container["data0"].data = [42]

        result = rec_job.cells[0].data()  # returns list of all data boxes

        assert len(result) == 1

        result = rec_job.cells[0].data(
            "data0"
        )  # returns data of result box with name data0

        assert result[0] == 42

        rec_job._build_program()

        result = rec_job.cells[0].data()  # returns list of all data boxes

        assert len(result) == 1

    def test_if_else_Error(self):
        # Else only directly after If possible
        with pytest.raises(RuntimeError, match="Else is not preceded by If"):
            with QiJob():
                var1 = QiVariable(int)
                var2 = QiVariable(int)
                with If(var1 > 3):
                    pass
                Assign(var2, 0)
                with Else():
                    pass

    def test_assign_var_in_for_range_Error(self):
        # Variable used in loop head must not be altered inside loop
        with pytest.raises(
            RuntimeError,
            match="Variable used in ForRange must not be used in internal Assign-Commands",
        ):
            with QiJob():
                var1 = QiVariable(int)
                with ForRange(var1, 0, 5, 1):
                    with If(var1 == 4):
                        Assign(var1, 0)

    def test_assign_var_in_for_range_OK(self):
        with QiJob():
            var1 = QiVariable(int)
            var2 = QiVariable(int)
            with ForRange(var1, 0, 5, 1):
                with If(var1 == 4):
                    Assign(var2, 0)

    def test_Parallel_Type_Error(self):
        with pytest.raises(
            RuntimeError, match="Type IfCommand not allowed inside Parallel()"
        ):
            with QiJob():
                var1 = QiVariable(int)
                with Parallel():
                    with If(var1 == 4):
                        Assign(var1, 0)

    def test_Parallel_state_recording_Error(self):
        with pytest.raises(
            RuntimeError, match="Can not save to state variable inside Parallel"
        ):
            with QiJob():
                q = QiCells(2)
                var = QiStateVariable()
                with Parallel():
                    PlayReadout(q[0], QiPulse(length=50e-9))
                    Recording(q[1], 400e-9, state_to=var)

    def test_Parallel_OK(self):
        with QiJob():
            q = QiCells(1)
            with Parallel():
                Play(q[0], QiPulse(length=50e-9))
                PlayReadout(q[0], QiPulse(length=50e-9))

    def test_combine_Parallel(self):
        with QiJob() as para_job:
            q = QiCells(1)
            with Parallel():
                Play(q[0], QiPulse(length=50e-9))
            with Parallel():
                PlayReadout(q[0], QiPulse(length=50e-9))

        assert len(para_job.commands) == 1

        para = para_job.commands[0]

        assert isinstance(para, ParallelCommand)
        assert len(para.entries) == 2

    def test_not_combine_Parallel(self):
        with QiJob() as para_job:
            q = QiCells(2)
            with Parallel():
                Play(q[0], QiPulse(length=50e-9))
            with Parallel():
                PlayReadout(q[1], QiPulse(length=50e-9))
            with Parallel():
                Play(q[1], QiPulse(length=50e-9))

        assert len(para_job.commands) == 2

        para = para_job.commands[0]

        assert isinstance(
            para, ParallelCommand
        )  # first Parallel should contain 2 entries
        assert len(para.entries) == 2

        para = para_job.commands[1]

        assert isinstance(
            para, ParallelCommand
        )  # second Parallel should contain 1 entries
        assert len(para.entries) == 1

    def test_undefined_property_OK(self):
        with QiJob():
            q = QiCells(1)

            Play(q[0], QiPulse(length=q[0]["PiPulse"]))
            PlayReadout(q[0], QiPulse(length=q[0]["PiPulse"]))
            Wait(q[0], q[0]["PiPulse"])

    def test_command_outside_job_error(self):
        with QiJob():
            q = QiCells(1)

            Play(q[0], QiPulse(length=48e-9))

        with pytest.raises(
            RuntimeError, match="Can not use command outside QiJob context manager."
        ):
            Wait(q[0], 20e-9)

    def test_variable_outside_job_error(self):
        with pytest.raises(
            RuntimeError, match="Can not use command outside QiJob context manager."
        ):
            _var = QiVariable(int)

        with pytest.raises(
            RuntimeError, match="Can not use command outside QiJob context manager."
        ):
            _var = QiTimeVariable(42e-9)

        with pytest.raises(
            RuntimeError, match="Can not use command outside QiJob context manager."
        ):
            _var = QiStateVariable()

    def test_undefined_recording_property(self):
        with QiJob():
            q = QiCells(1)
            Recording(q[0], q[0]["len"], q[0]["off"])

    def test_buid_cooltest(self):
        with QiJob() as cool_test:
            q = QiCells(1)
            length = QiVariable()

            with ForRange(length, 0, 20):
                Play(q[0], QiPulse(length=length))
                PlayReadout(q[0], QiPulse(length=length))
                Wait(q[0], length)

        cool_test._build_program()

    def test_stringify(self):
        with QiJob() as str_job:
            q = QiCells(1)
            length = QiVariable()
            storage = QiResult()
            Assign(length, 1e-07)
            Store(q[0], length, storage)
            RotateFrame(q[0], 90)
            Sync(q[0])

            with If(length > 2 + length * 5):
                Wait(q[0], 0)
            with Else():
                Wait(q[0], 1)

            with Parallel():
                Play(q[0], QiPulse(length=length))
                PlayReadout(q[0], QiPulse(length=length))

            with ForRange(length, 0, 20):
                _x = QiVariable(int)
                Play(q[0], QiPulse(length=length))
                PlayReadout(q[0], QiPulse(length=length))
                Wait(q[0], length)
                Recording(q[0], 1, 0)

        string = str(str_job)
        assert (
            string
            == """\
QiJob:
    q = QiCells(1)
    v0 =  QiVariable()
    Assign(v0, 1e-07)
    Store(q[0], v0, QiResult(""))
    RotateFrame(q[0], 90)
    Sync(q[0])
    If(v0 > (2 + (v0 * 5))):
        Wait(q[0], 0)
    Else:
        Wait(q[0], 1)
    Parallel:
        Play(q[0], QiPulse(v0))
        PlayReadout(q[0], QiPulse(v0))
    ForRange(v0, 0, 20, 1):
        v1 =  QiVariable()
        Play(q[0], QiPulse(v0))
        PlayReadout(q[0], QiPulse(v0))
        Wait(q[0], v0)
        Recording(q[0], 1)"""
        )

    def test_stringify_rabi(self):
        from qiclib.experiment.qicode.collection import Rabi

        rabi = Rabi(0, 1e-6, 100e-9)
        string = str(rabi)
        assert (
            string
            == """\
QiJob:
    q = QiCells(1)
    v0 =  QiVariable()
    ForRange(v0, 0, 1e-06, 1e-07):
        Play(q[0], QiPulse(v0, frequency=q[0]["manip_frequency"]))
        PlayReadout(q[0], QiPulse(q[0]["rec_pulse"], frequency=q[0]["rec_frequency"]))
        Recording(q[0], q[0]["rec_length"], offset=q[0]["rec_offset"], save_to="result")
        Wait(q[0], 5 * q[0]["T1"])"""
        )

    def test_stringify_parallel(self):
        with QiJob() as job:
            q = QiCells(1)
            with Parallel():
                Play(q[0], QiPulse(100e-9, frequency=60e6))
                Play(q[0], QiPulse(100e-9, frequency=60e6))
            with Parallel():
                PlayReadout(q[0], QiPulse(100e-9, frequency=40e6))
        string = str(job)
        assert (
            string
            == """\
QiJob:
    q = QiCells(1)
    Parallel:
        Play(q[0], QiPulse(1e-07, frequency=6e+07))
        Play(q[0], QiPulse(1e-07, frequency=6e+07))
    Parallel:
        PlayReadout(q[0], QiPulse(1e-07, frequency=4e+07))"""
        )

    def test_stringify_active_reset(self):
        from qiclib.experiment.qicode.collection import ActiveReset

        job = ActiveReset()
        string = str(job)
        assert (
            string
            == """\
QiJob:
    q = QiCells(1)
    v0 =  QiVariable()
    PlayReadout(q[0], QiPulse(q[0]["rec_pulse"], frequency=q[0]["rec_frequency"]))
    Recording(q[0], q[0]["rec_length"], offset=q[0]["rec_offset"], state_to=v0)
    If(v0 != 0):
        Play(q[0], QiPulse(q[0]["pi"], frequency=q[0]["manip_frequency"]))
    PlayReadout(q[0], QiPulse(q[0]["rec_pulse"], frequency=q[0]["rec_frequency"]))
    Recording(q[0], q[0]["rec_length"], offset=q[0]["rec_offset"], save_to="result")"""
        )

    def test_stringify_two_jobs(self):
        with QiJob() as job1:
            _q = QiCells(1)
            _var = QiVariable()
        with QiJob() as job2:
            _q = QiCells(1)
            _var = QiVariable()
        string = str(job1) + "\n" + str(job2)
        assert (
            string
            == """\
QiJob:
    q = QiCells(1)
    v0 =  QiVariable()
QiJob:
    q = QiCells(1)
    v0 =  QiVariable()"""
        )

    def test_stringify_shapes(self):
        with QiJob() as job:
            q = QiCells(1)
            pulse = QiPulse(10e-6, ShapeLib.gauss)
            Play(q[0], pulse)
        string = str(job)
        assert (
            string
            == """\
QiJob:
    q = QiCells(1)
    Play(q[0], QiPulse(1e-05, shape=Shape(gauss)))"""
        )

    def test_stringify_qicellprop(self):
        with QiJob() as test:
            q = QiCells(1)
            Wait(q[0], 5 * q[0]["T1"])
        string = str(test)
        assert (
            string
            == """\
QiJob:
    q = QiCells(1)
    Wait(q[0], 5 * q[0]["T1"])"""
        )


class TestQiJobDescriptionMissingProperty:
    @pytest.fixture
    def job(self):
        with QiJob() as job:
            q = QiCells(1)

            Play(q[0], QiPulse(length=q[0]["PiPulse"], frequency=q[0]["Manip_Freq"]))
            Wait(q[0], q[0]["Wait"])
            Recording(q[0], q[0]["rec"], q[0]["offset"])
        return job

    def test_property_defined_OK(self, job):
        test = QiSample(1)
        test[0]["PiPulse"] = 52e-9
        test[0]["Manip_Freq"] = 60e6
        test[0]["Wait"] = 52e-9
        test[0]["rec"] = 200e-9
        test[0]["offset"] = 48e-9

        job._build_program(test)

        assert job.commands[0].length == test[0]["PiPulse"]
        assert job.cells[0].initial_manipulation_frequency == test[0]["Manip_Freq"]
        assert job.commands[1].length == test[0]["Wait"]
        assert job.commands[2].length == test[0]["rec"]

    def test_property_defined_Error(self, job):
        test = QiSample(1)
        with pytest.raises(
            RuntimeError,
            match="Not all properties for job could be resolved. Missing properties:",
        ):
            job._build_program(test)

    def test_property_defined_no_cell_Error(self, job):
        with pytest.raises(
            ValueError,
            match="QiSample needs to be passed to resolve job properties!",
        ):
            job._build_program()

    def test_property_too_many_cells_Error(self, job):
        test = QiSample(2)
        test[0]["PiPulse"] = 52e-9

        with pytest.raises(
            RuntimeError,
            match="Not all properties for job could be resolved. Missing properties:",
        ):
            job._build_program(test)


class TestQiGate:
    @staticmethod
    @QiGate
    def PlayPulse(length, cell: QiCell):
        Play(cell, QiPulse(length))

    @staticmethod
    @QiGate
    def PlayPulses(length, cell1: QiCell, cell2: QiCell):
        Play(cell1, QiPulse(length))
        Play(cell2, QiPulse(length))

    @staticmethod
    @QiGate
    def Readout(cell):
        pulse_length = cell["readout"]
        PlayReadout(cell, QiPulse(pulse_length))
        Recording(cell, 100e-9)

    @staticmethod
    @QiGate
    def AssignVar(var):
        Assign(var, 42)

    def test_single_cell_function(self):
        with QiJob(skip_nco_sync=True) as gate_test:
            _q = QiCells(2)
            self.PlayPulse(48e-9, gate_test.cells[0])

        assert len(gate_test.commands) == 1
        assert isinstance(gate_test.commands[0], PlayCommand)

    def test_multi_cell_function(self):
        with QiJob(skip_nco_sync=True) as gate_test:
            _q = QiCells(2)
            self.PlayPulses(48e-9, gate_test.cells[0], gate_test.cells[1])

        assert len(gate_test.commands) == 3

        sync = gate_test.commands[0]
        assert isinstance(sync, SyncCommand)

        assert gate_test.cells[0] in sync._relevant_cells
        assert gate_test.cells[1] in sync._relevant_cells

        assert isinstance(gate_test.commands[1], PlayCommand)
        assert isinstance(gate_test.commands[2], PlayCommand)

    def test_gate_cell_getitem_function(self):
        with QiJob(skip_nco_sync=True) as gate_test:
            _q = QiCells(2)
            self.Readout(gate_test.cells[0])

        assert len(gate_test.commands) == 1
        assert isinstance(gate_test.commands[0], PlayReadoutCommand)

    def test_gate_assign_var(self):
        with pytest.raises(RuntimeError):
            with QiJob(skip_nco_sync=True):
                variable = QiVariable(int)
                self.AssignVar(variable)


class TestPulseToCell:
    def test_equal_pulses(self):
        with QiJob(skip_nco_sync=True) as test:
            q = QiCells(2)
            Play(q[0], QiPulse(length=50e-9))
            Play(q[0], QiPulse(length=50e-9))

            Play(q[1], QiPulse(length=50e-9))
            Play(q[1], QiPulse(length=50e-9))

        assert len(test.cells[0].manipulation_pulses) == 1

        assert test.commands[0].trigger_index == 1
        assert test.commands[1].trigger_index == 1

        assert test.commands[2].trigger_index == 1
        assert test.commands[3].trigger_index == 1

    def test_different_pulses(self):
        with QiJob(skip_nco_sync=True) as test:
            q = QiCells(1)
            Play(q[0], QiPulse(length=50e-9))
            Play(q[0], QiPulse(length=100e-9))

        assert len(test.cells[0].manipulation_pulses) == 2

        assert test.commands[0].trigger_index == 1
        assert test.commands[1].trigger_index == 2

    def test_variable_pulses(self):
        with QiJob(skip_nco_sync=True) as test:
            q = QiCells(1)
            var = QiVariable()

            Play(q[0], QiPulse(length=var))
            Play(q[0], QiPulse(length=var))

        assert len(test.cells[0].manipulation_pulses) == 1

        # commands[0] is QiDeclare
        assert test.commands[1].trigger_index == 1
        assert test.commands[2].trigger_index == 1

    def test_equal_readoutpulses(self):
        with QiJob(skip_nco_sync=True) as test:
            q = QiCells(1)
            PlayReadout(q[0], QiPulse(length=50e-9))
            PlayReadout(q[0], QiPulse(length=50e-9))

        assert len(test.cells[0].readout_pulses) == 1

        assert test.commands[0].trigger_index == 1
        assert test.commands[1].trigger_index == 1

    def test_different_readoutpulses(self):
        with QiJob(skip_nco_sync=True) as test:
            q = QiCells(1)
            PlayReadout(q[0], QiPulse(length=50e-9))
            PlayReadout(q[0], QiPulse(length=100e-9))

        assert len(test.cells[0].readout_pulses) == 2

        assert test.commands[0].trigger_index == 1
        assert test.commands[1].trigger_index == 2

    def test_variable_readoutpulses(self):
        with QiJob(skip_nco_sync=True) as test:
            q = QiCells(1)
            var = QiVariable()

            PlayReadout(q[0], QiPulse(length=var))
            PlayReadout(q[0], QiPulse(length=var))

        assert len(test.cells[0].readout_pulses) == 1

        # commands[0] is QiDeclare
        assert test.commands[1].trigger_index == 1
        assert test.commands[2].trigger_index == 1

    def test_state_variable_in_combined_play_readout_and_recording(self):
        with QiJob() as job:
            q = QiCells(1)
            state = QiVariable()
            PlayReadout(q[0], QiPulse(400e-9, frequency=60e6))
            Recording(q[0], 400e-9, 280e-9, save_to=state)
            Wait(q[0], 2e-6)

        assert state in job.commands[1]._associated_variable_set

    def test_qipulse_with_qicell_property(self):
        # from issue #209
        test_sample = QiSample(1)
        test_sample[0]["pulse"] = 200e-9

        with QiJob() as job:
            q = QiCells(1)
            Play(q[0], QiPulse(q[0]["pulse"], frequency=60e6))
            Play(q[0], QiPulse(100e-9, frequency=60e6))

        job._build_program(sample=test_sample)

        instructions = job.cell_seq_dict[q[0]].instruction_list

        assert isinstance(instructions[1], SeqTrigger)
        assert instructions[1]._trig_indices[2] == 1

        assert isinstance(instructions[3], SeqTrigger)
        assert instructions[3]._trig_indices[2] == 2


class TestQiRecordingOrder:
    def test_single_loop(self):
        with QiJob() as job:
            cells = QiCells(1)
            a = QiVariable(name="a")
            with ForRange(a, 0, 10):
                Recording(cells[0], 20e-9, save_to="result_a")

        x = job._simulate_recordings()[cells[0]]
        x = [x.save_to for x in x]

        assert x == ["result_a"] * 10

    def test_double_nested_loop(self):
        with QiJob() as job:
            cells = QiCells(1)
            a = QiVariable(name="a")
            b = QiVariable(name="b")
            with ForRange(a, 0, 10):
                Recording(cells[0], 20e-9, save_to="result_a")
                with ForRange(b, 0, 10):
                    Recording(cells[0], 20e-9, save_to="result_b")

        x = job._simulate_recordings()[cells[0]]
        x = [x.save_to for x in x]

        expected = []
        for a in range(10):
            expected.append("result_a")
            for b in range(10):
                expected.append("result_b")

        assert x == expected

    def test_double_nested_increasing_upper_bound_loop(self):
        with QiJob() as job:
            cells = QiCells(1)
            a = QiVariable(name="a")
            b = QiVariable(name="b")
            with ForRange(a, 0, 10):
                Recording(cells[0], 20e-9, save_to="result_a")
                with ForRange(b, 0, a):
                    Recording(cells[0], 20e-9, save_to="result_b")

        x = job._simulate_recordings()[cells[0]]
        x = [x.save_to for x in x]

        expected = []
        for a in range(10):
            expected.append("result_a")
            for b in range(a):
                expected.append("result_b")

        assert x == expected

    def test_multiple_recordings_loop_body(self):
        with QiJob() as job:
            cells = QiCells(1)
            a = QiVariable(name="a")
            b = QiVariable(name="b")
            c = QiVariable(name="b")
            with ForRange(a, 0, 10):
                Recording(cells[0], 20e-9, save_to="result_a")

                with ForRange(b, 0, 10):
                    Recording(cells[0], 20e-9, save_to="result_b")

                Recording(cells[0], 20e-9, save_to="result_d")

                with ForRange(c, 0, 10):
                    Recording(cells[0], 20e-9, save_to="result_c")

        x = job._simulate_recordings()[cells[0]]
        x = [x.save_to for x in x]

        expected = []
        for a in range(10):
            expected.append("result_a")
            for b in range(10):
                expected.append("result_b")
            expected.append("result_d")
            for b in range(10):
                expected.append("result_c")

        assert x == expected

    # If we want to support recording in ifs we should add them to the simulation.
    def test_single_recording_in_program_with_if(self):
        with QiJob() as job:
            cells = QiCells(1)
            a = QiVariable(name="a")
            with If(a == 2):
                Recording(cells[0], 20e-9, save_to="result_a")

        with pytest.raises(
            RuntimeError, match="Recording command within If-Else statement"
        ):
            job._simulate_recordings()[cells[0]]

    def test_multiple_cells2(self):
        with QiJob() as job:
            cells = QiCells(2)
            a = QiVariable(name="a")
            _b = QiVariable(name="a")
            with ForRange(a, 0, 10):
                Recording(cells[0], 20e-9, save_to="result_a")
                Recording(cells[1], 20e-9, save_to="result_b")

        job._build_program()

        given_order_0 = [x.name for x in cells[0]._result_recording_order]
        given_order_1 = [x.name for x in cells[1]._result_recording_order]

        expected_cell_0 = []
        expected_cell_1 = []
        for _ in range(10):
            expected_cell_0.append("result_a")
            expected_cell_1.append("result_b")

        assert given_order_0 == expected_cell_0
        assert given_order_1 == expected_cell_1

    def test_multiple_cells3(self):
        with QiJob() as job:
            cells = QiCells(3)
            a = QiVariable(name="a")
            b = QiVariable(name="a")
            with ForRange(a, 0, 10):
                Recording(cells[0], 20e-9, save_to="result_a")
                with ForRange(b, 0, a):
                    Recording(cells[1], 20e-9, save_to="result_b")
            Recording(cells[2], 20e-9, save_to="result_c")

        job._build_program()

        given_order_0 = [x.name for x in cells[0]._result_recording_order]
        given_order_1 = [x.name for x in cells[1]._result_recording_order]
        given_order_2 = [x.name for x in cells[2]._result_recording_order]

        expected_cell_0 = []
        expected_cell_1 = []
        expected_cell_2 = []
        for i in range(10):
            expected_cell_0.append("result_a")
            for _ in range(i):
                expected_cell_1.append("result_b")
        expected_cell_2.append("result_c")

        assert given_order_0 == expected_cell_0
        assert given_order_1 == expected_cell_1
        assert given_order_2 == expected_cell_2

    def test_nested_loops2(self):
        with QiJob() as job:
            q = QiCells(1)
            var1 = QiVariable(int)
            var2 = QiVariable(int, 2)
            with ForRange(var1, var2, 5):
                Recording(q[0], 4e-9, save_to="result_a")
            # Two different boxes so it actually tries to simulate.
            with ForRange(var1, var2, 5):
                Recording(q[0], 4e-9, save_to="result_b")

        job._build_program()

        given_order = [x.name for x in q[0]._result_recording_order]

        assert given_order == ["result_a"] * 3 + ["result_b"] * 3

    def test_float_step(self):
        with QiJob() as calib_offset:
            q = QiCells(1)
            offset = QiVariable()
            with ForRange(offset, 0, 1024e-9, 4e-9):
                PlayReadout(q[0], QiPulse(400e-9, frequency=60e6))
                Recording(q[0], 400e-9, offset, save_to="result")
                Wait(q[0], 2e-6)
        calib_offset._build_program()
        assert calib_offset.cells[0].get_number_of_recordings() == 256


def test_calculation_with_sample_value_and_variable():
    with QiJob() as job:
        q = QiCells(1)
        i = QiFrequencyVariable()
        with ForRange(i, 0, 10e6, 100):
            Play(q[0], QiPulse(length=100e-9, frequency=q[0]["freq"] + i))

    sample = QiSample(1)
    sample[0]["freq"] = 200e6
    job._build_program(sample)


def test_calculation_with_sample_value_and_inferred_variable():
    with QiJob() as job:
        q = QiCells(1)
        i = QiVariable()
        with ForRange(i, 0, 10e6, 100):
            Play(q[0], QiPulse(length=100e-9, frequency=q[0]["freq"] + i))

    sample = QiSample(1)
    sample[0]["freq"] = 200e6
    job._build_program(sample)


def test_highest_frequency():
    with pytest.raises(
        ValueError, match=re.escape("Frequency of 5e+08 Hz is too high")
    ):
        with QiJob():
            f = QiFrequencyVariable()
            with ForRange(f, 0, 500e6, 100e6):
                pass
