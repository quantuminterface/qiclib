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
import math
import os
import re

import numpy as np
import pytest
from inline_snapshot import snapshot

import qiclib.packages.utility as util
import qicode.proto
from qiclib.code import QiIntVariable, QiPhaseVariable, While
from qiclib.code.qi_command import (
    AssignCommand,
    ForRangeCommand,
    IfCommand,
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
    QiAmplitudeVariable,
    QiCell,
    QiCells,
    QiFrequencyVariable,
    QiGate,
    QiJob,
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
from qiclib.code.qi_types import QiType
from qiclib.code.qi_var_definitions import _QiVariableBase


def test_no_length_inside_job():
    with QiJob():
        q = QiCells(1)
        assert isinstance(q[0]["nothing here"], qicode.QiCellProperty)


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
            ValueError,
            match=re.escape("Imported JSON string does not contain 'cells'."),
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
        cells = QiCells(1)
        cell = cells[0]
        cell["electrical_delay"] = 0
        cell["recording_length"] = 400e-9
        return cell

    @pytest.fixture
    def sample(self):
        sample = QiSample(1)
        sample[0]["electrical_delay"] = 0
        sample[0]["recording_length"] = 400e-9
        return sample

    def test_recording_length(self):
        with QiJob() as job:
            q = QiCells(1)
            Recording(
                q[0],
                duration=400e-9,
                offset=0,
                save_to="result",
            )
        assert isinstance(job.commands[0], RecordingCommand)
        assert job.commands[0].length == 400e-9

    def test_recording_error(self):
        # Raises error: RecordingCommand needs state variable
        with pytest.raises(TypeError):
            with QiJob():
                q = QiCells(1)
                var = QiTimeVariable()
                Recording(
                    q[0],
                    duration=q[0]["recording_length"],
                    offset=q[0]["electrical_delay"],
                    save_to="result",
                    state_to=var,
                )

    def test_recording_state(self):
        with QiJob() as job:
            q = QiCells(1)
            var = QiStateVariable()
            Recording(
                q[0],
                duration=q[0]["recording_length"],
                offset=q[0]["electrical_delay"],
                state_to=var,
            )
            # Test also with additional QiResult supplied
            Recording(
                q[0],
                duration=q[0]["recording_length"],
                offset=q[0]["electrical_delay"],
                state_to=var,
                save_to="result",
            )
        # Command 1 is declare command

        rec1 = job.commands[1]
        assert isinstance(rec1, RecordingCommand)
        assert rec1.uses_state

        rec2 = job.commands[2]
        assert isinstance(rec2, RecordingCommand)
        assert rec2.uses_state

    def test_assign_error(self):
        with pytest.raises(TypeError):
            with QiJob():
                var = QiStateVariable()
                Assign(var, 1)

    def test_ForRange_end_value_warning(self):
        with pytest.warns(
            UserWarning, match="End value of 0 will not be included in ForRange."
        ):
            with QiJob():
                q = QiCells(1)
                # Warns that end value 0 is not included
                var = QiTimeVariable()
                with ForRange(var, 20e-9, 0, -4e-9):
                    Wait(q[0], var)

    def test_ForRange_var_start_end_warning(self):
        # Warns that unrolling is not supported for variable start/end times
        with pytest.raises(
            RuntimeError,
            match="Loop variable can not be used as start value",
        ):
            with QiJob():
                q = QiCells(1)
                var = QiTimeVariable()
                var2 = QiTimeVariable()
                with ForRange(var, var, var2, -4e-9):
                    Wait(q[0], var)

        with pytest.raises(
            RuntimeError,
            match="Loop variable can not be used as end value",
        ):
            with QiJob():
                q = QiCells(1)
                var = QiTimeVariable()
                var2 = QiTimeVariable()
                with ForRange(var, var2, var, -4e-9):
                    Wait(q[0], var)

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

    def test_ForRange_state_error(self):
        # Raises error: step must be multiple of 4e-9
        with pytest.raises(TypeError):
            with QiJob():
                q = QiCells(1)
                var = QiStateVariable()
                with pytest.raises(TypeError):
                    with ForRange(var, 20e-9, 0, -4e-9):
                        Wait(q[0], var)

    def test_ForRange_Parallel_var_warning(self):
        # Raises error: step must be multiple of 4e-9
        warning_msg = r"Loop variable inside Parallel Context Manager might result in unexpected behaviour\. Please unroll loop or change variable"
        with pytest.raises(RuntimeError, match=warning_msg):
            with QiJob():
                var = QiTimeVariable()
                q = QiCells(1)
                with ForRange(var, 52e-9, 0, -4e-9):
                    with Parallel():
                        Play(q[0], QiPulse(42e-9))
                    with Parallel():
                        Wait(q[0], var)

    def test_ForRange_OK(self):
        with QiJob():
            q = QiCells(1)
            var = QiTimeVariable()
            with ForRange(var, 0, 100e-9, 24e-9):
                Wait(q[0], var)

    def test_ForRange_negative_OK(self):
        with pytest.warns(
            UserWarning, match="End value of 0 will not be included in ForRange."
        ):
            with QiJob():
                cells = QiCells(1)
                var = QiTimeVariable()
                with ForRange(var, 100e-9, 0, -20e-9):
                    Wait(cells[0], var)

    def test_for_range_definition_error(self):
        var = _QiVariableBase(QiType.NORMAL)
        with pytest.raises(ValueError):
            ForRangeCommand(var, 0, 5, -1, [])

        with pytest.raises(ValueError):
            ForRangeCommand(var, 5, 0, 1, [])

        with pytest.raises(ValueError):
            ForRangeCommand(var, 0, 5, 0, [])


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
        with QiJob() as job:
            var1 = QiVariable(int)
            with If(var1 > 3):
                Assign(var1, 0)
            with Else():
                Assign(var1, 0)

        if_cm = next(filter(lambda cmd: isinstance(cmd, IfCommand), job.commands))
        assert isinstance(if_cm, IfCommand)
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
            RuntimeError,
            match=re.escape("Can only register one set of cells at a QiJob."),
        ):
            with QiJob():
                _q = QiCells(1)
                _p = QiCells(1)

    def test_qicells_in_multiple_jobs_Error(self):
        with QiJob():
            q = QiCells(1)

        with pytest.raises(
            RuntimeError,
            match="Tried getting values for cells registered to other QiJob",
        ):
            with QiJob():
                _length = q[0]["test"]

    def test_single_recording_box_retrieval(self):
        with QiJob() as rec_job:
            q = QiCells(1)
            Recording(q[0], 4e-9, save_to="data0")

        rec_job.cells[0]._result_container["data0"].data = [42]

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

        rec_job.cells[0]._result_container["data0"].data = [42]

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
            RuntimeError,
            match=re.escape("Type IfCommand not allowed inside Parallel()"),
        ):
            with QiJob():
                var1 = QiVariable(int)
                with Parallel():
                    with If(var1 == 4):
                        Assign(var1, 0)

    def test_Parallel_state_recording_Error(self):
        with pytest.raises(
            RuntimeError,
            match=re.escape("Can not save to state variable inside Parallel"),
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
            RuntimeError, match=re.escape("Can not use command outside QiJob context.")
        ):
            Wait(q[0], 20e-9)

    def test_variable_outside_job_error(self):
        with pytest.raises(
            RuntimeError, match=re.escape("Can not use command outside QiJob context.")
        ):
            _var = QiVariable(int)

        with pytest.raises(
            RuntimeError, match=re.escape("Can not use command outside QiJob context.")
        ):
            _var = QiTimeVariable(42e-9)

        with pytest.raises(
            RuntimeError, match=re.escape("Can not use command outside QiJob context.")
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
            Assign(length, 1e-07)
            Store(q[0], length, "result")
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
    Store(q[0], v0, QiResult("result"))
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
            pulse = QiPulse(10e-6, shape=ShapeLib.gauss)
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


def test_duplicte_amplitude_assignment():
    """Test that different amplitude assignments to pulses on the same cell are handled correctly and preserved."""
    sample = QiSample(1)
    sample[0]["amp0"] = 0.5
    sample[0]["amp1"] = 0.6

    with QiJob() as job:
        q = QiCells(1)
        Play(q[0], QiPulse(length=100e-9, amplitude=q[0]["amp0"]))
        Play(q[0], QiPulse(length=100e-9, amplitude=q[0]["amp1"]))

    job._build_program(sample)

    # Verify the commands were created correctly
    assert len(job.commands) == 2

    # Verify first Play command has correct amplitude
    assert isinstance(job.commands[0], PlayCommand)
    assert job.commands[0].pulse.amplitude == 0.5

    # Verify second Play command has correct amplitude
    assert isinstance(job.commands[1], PlayCommand)
    assert job.commands[1].pulse.amplitude == 0.6

    # Verify the pulses are treated as distinct due to different amplitudes
    assert len(job.cells[0].manipulation_pulses) == 2


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
            match=re.escape(
                "Not all properties for job could be resolved. Missing properties:"
            ),
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
            match=re.escape(
                "Not all properties for job could be resolved. Missing properties:"
            ),
        ):
            job._build_program(test)


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


class TestQiGate:
    def test_single_cell_function(self):
        with QiJob(skip_nco_sync=True) as gate_test:
            _q = QiCells(2)
            PlayPulse(48e-9, gate_test.cells[0])

        assert len(gate_test.commands) == 1
        assert isinstance(gate_test.commands[0], PlayCommand)

    def test_multi_cell_function(self):
        with QiJob(skip_nco_sync=True) as gate_test:
            _q = QiCells(2)
            PlayPulses(48e-9, gate_test.cells[0], gate_test.cells[1])

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
            Readout(gate_test.cells[0])

        assert len(gate_test.commands) == 1
        assert isinstance(gate_test.commands[0], PlayReadoutCommand)

    def test_gate_assign_var(self):
        with pytest.raises(RuntimeError):
            with QiJob(skip_nco_sync=True):
                variable = QiVariable(int)
                AssignVar(variable)


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
            Recording(q[0], 400e-9, 280e-9, state_to=state)
            Wait(q[0], 2e-6)

        assert job.get_var(state) in job.commands[1]._associated_variable_set

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


def test_calculation_minus_frequency():
    with QiJob() as job:
        q = QiCells(1)
        f = QiFrequencyVariable()
        with ForRange(f, 0, 100e6, 10e6):
            PlayReadout(q[0], QiPulse(100e-9, frequency=33e6 - f))

    job._build_program()


def test_highest_frequency():
    with pytest.raises(
        ValueError, match=re.escape("Frequency of 5e+08 Hz is too high")
    ):
        with QiJob():
            f = QiFrequencyVariable()
            with ForRange(f, 0, 500e6, 100e6):
                pass


def test_amplitude_as_sample_ok():
    sample = QiSample(1)
    sample[0].update(rec_amplitude=0.06)

    with QiJob() as job:
        q = QiCells(1)
        PlayReadout(
            q[0], QiPulse(amplitude=q[0]["rec_amplitude"], length="cw", frequency=100e6)
        )
    job._build_program(sample)
    assert isinstance(job.commands[0], PlayReadoutCommand)
    assert job.commands[0].pulse.amplitude == 0.06
    assert np.all(job.commands[0].pulse(2e9) == np.array([0.06] * 8))


def test_nested_parallel_blocks():
    with pytest.raises(
        RuntimeError,
        match=re.escape("Type ParallelCommand not allowed inside Parallel()"),
    ):
        with QiJob():
            q = QiCells(1)
            with Parallel():
                with Parallel():  # This should fail - nested parallel not allowed
                    PlayReadout(q[0], QiPulse(length=50e-9))


def test_for_within_if():
    with QiJob() as job:
        q = QiCells(1)
        a = QiVariable(int)
        b = QiVariable(int, value=1)
        with If(b == 1):
            with ForRange(a, 0, 10):
                Recording(q[0], duration=1e-6)

    assert job.get_assembly() == [
        "tr 0x0, 0x0, 0x0, 0x0, 0x0, 0x0",
        "addi r2, r0, 0x1",
        "addi r3, r0, 0x1",
        "bne r2, r3, 0x8",
        "addi r3, r0, 0xa",
        "addi r1, r0, 0x0",
        "bge r1, r3, 0x5",
        "tr 0x0, 0x2, 0x0, 0x0, 0x0, 0x0",
        "wti 0xfa",
        "addi r1, r1, 0x1",
        "j -0x4",
        "end",
    ]


def test_variable_amplitude_can_be_used():
    with QiJob() as job:
        q = QiCells(2)
        a = QiAmplitudeVariable()
        with ForRange(a, 0, 0.99, 0.1):
            PlayReadout(q[0], QiPulse(length="cw", frequency=200e6, amplitude=a))
            Play(q[1], QiPulse.off())

    job._build_program()


def test_qi_sample_can_divide():
    with QiJob() as job:
        q = QiCells(1)
        x = QiIntVariable()
        Assign(x, q[0]["property"] / 2)
        y = QiIntVariable()
        Assign(y, 120 / q[0]["property"])

    sample = QiSample(1)
    sample[0]["property"] = 40
    job._build_program(sample)

    assert isinstance(job.commands[1], AssignCommand)
    assert job.commands[1].value() == 20

    assert isinstance(job.commands[3], AssignCommand)
    assert job.commands[3].value == 3


def test_active_reset_while_recording_if():
    """Active reset: While(state != 0) contains Recording(state_to=) and conditional Play."""
    with QiJob() as job:
        q = QiCells(1)
        state = QiStateVariable()

        PlayReadout(q[0], QiPulse(1e-6))
        Recording(q[0], state_to=state, duration=1e-6)

        with While(state != 0):
            PlayReadout(q[0], QiPulse(1e-6))
            Recording(q[0], state_to=state, duration=1e-6)
            with If(state != 0):
                Play(q[0], QiPulse(100e-9))  # pi pulse to reset

    assert (
        job.get_assembly()
        == snapshot(
            [
                "tr 0x0, 0x0, 0x0, 0x0, 0x0, 0x0",  # start
                "tr 0x1, 0x2, 0x0, 0x0, 0x0, 0x0",  # Readout + Recording
                "wtq r1, 0",  # Await qubit state
                "beq r1, r0, 0x7",  # If state == 0 -> finish
                "tr 0x1, 0x2, 0x0, 0x0, 0x0, 0x0",  # Readout + Recording (inside While)
                "wtq r1, 0",  # Await qubit state
                "beq r1, r0, 0x3",  # If r1 == 0 => jump to start (which will then jump to finish)
                "tr 0x0, 0x0, 0x1, 0x0, 0x0, 0x0",  # Trigger pi pulse
                "wti 0x18",  # Wait for pi pulse to finish
                "j -0x6",  # Jump to start of While loop
                "end",
            ]
        )
    )


def test_parallel_ramsey_two_qubits():
    """
    Build a 2-cell Parallel Ramsey job: ForRange sweeping delay, two Parallel pi/2
    blocks bracketing a variable Wait, and Sync.
    """
    pi_half = QiPulse(length=20e-9)

    with QiJob() as job:
        q = QiCells(2)
        delay = QiTimeVariable()

        with ForRange(delay, 0, 3e-6, 100e-9):
            with Parallel():
                Play(q[0], pi_half)
                Play(q[1], pi_half)
            Wait(q[0], delay)
            Wait(q[1], delay)
            with Parallel():
                Play(q[0], pi_half)
                Play(q[1], pi_half)
            Sync(q[0], q[1])

    assert job.get_assembly(0) == snapshot(
        [
            "tr 0x0, 0x0, 0x0, 0x0, 0x0, 0x0",  # start
            "addi r1, r0, 0x0",  # initialize r1 := 0
            "tr 0x0, 0x0, 0x1, 0x0, 0x0, 0x0",  # Peeled loop iteration 0
            "wti 0x4",  # Wait for 4 ns
            "tr 0x0, 0x0, 0x1, 0x0, 0x0, 0x0",  # Second Play
            "wti 0x4",  # Second wait
            "addi r2, r0, 0x2ee",  # Initialize r2 : end value
            "addi r1, r0, 0x19",  # Increment r1 by 100 ns
            "bge r1, r2, 0x8",  # for-loop conditional branch
            "tr 0x0, 0x0, 0x1, 0x0, 0x0, 0x0",  # pi/2 pulse play
            "wti 0x4",  # pi/2 pulse wait duration
            "wtr r1, 0x0",  # Variable wait; source is register
            "tr 0x0, 0x0, 0x1, 0x0, 0x0, 0x0",  # pi/2 pulse play
            "wti 0x4",  # pi/2 pulse wait duration
            "addi r1, r1, 0x19",  # Increment r1 (loop)
            "j -0x7",  # Jump to start of loop
            "end",
        ]
    )

    assert job.get_assembly(1) == job.get_assembly(0)


# There was a bug (AttributeError: 'int' object has no attribute 'insert') for what seems to be correct code
@pytest.mark.skip(reason="Unresolved Bug")
def test_nested_amplitude_length_sweep():
    with QiJob() as job:
        q = QiCells(1)
        amp = QiAmplitudeVariable()
        length = QiTimeVariable()

        with ForRange(amp, 0.1, 1.0, 0.1):
            with ForRange(length, 20e-9, 200e-9, 20e-9):
                Play(q[0], QiPulse(length, amplitude=amp))
                Recording(q[0], 200e-9, save_to="result")

    assert job.get_assembly() == snapshot()


def test_cpmg_n_dynamical_decoupling():
    """CPMG-2: outer delay sweep, inner loop of 2 Y-axis pi pulses (RotateFrame +-pi/2 + Play)."""
    n_pulses = 2
    pi_len = 20e-9
    pi_half_len = 10e-9

    with QiJob() as job:
        q = QiCells(1)
        delay = QiTimeVariable()
        seg = QiTimeVariable()
        i = QiVariable(int)

        with ForRange(delay, 200e-9, 600e-9, 200e-9):
            # seg = delay / (2 * n_pulses); n_pulses=2 -> right-shift by 2
            Assign(seg, delay >> 2)
            # initial pi/2 pulse (X axis)
            Play(q[0], QiPulse(pi_half_len))
            # N refocusing pi pulses rotated to Y axis via RotateFrame
            with ForRange(i, 0, n_pulses, 1):
                Wait(q[0], seg)
                RotateFrame(q[0], math.pi / 2)
                Play(q[0], QiPulse(pi_len))
                RotateFrame(q[0], -(math.pi / 2))
                Wait(q[0], seg)
            # final pi/2 pulse
            Play(q[0], QiPulse(pi_half_len))
            PlayReadout(q[0], QiPulse(400e-9))
            Recording(q[0], 400e-9, 0, save_to="result")
            Wait(q[0], 50e-6)

    assert job.get_assembly() == snapshot(
        [
            "tr 0x0, 0x0, 0x0, 0x0, 0x0, 0x0",  # Start trigger
            "addi r4, r0, 0x96",  # Initialize r4: loop end
            "addi r1, r0, 0x32",  # Initialize r1: loop start
            "bge r1, r4, 0x17",  # Loop condition: If r1 > r4; goto end
            "sra r5, r1, 0x2",  # Multiply r5 := r1 / 2 (r5 == wait time)
            "addi r2, r5, 0x0",  # Add r2 := r5
            "tr 0x0, 0x0, 0x1, 0x0, 0x0, 0x0",  # Trigger play command
            "wti 0x2",  # Wait for 2 cycles (10 ns)
            "addi r5, r0, 0x2",  # Inner loop end value initialization: r5 = n_pulses (2)
            "addi r3, r0, 0x0",  # Inner loop initial value initialization: r3 = 0
            "bge r3, r5, 0x9",  # If r3 > r5 => goto end
            "wtr r2, 0x0",  # Wait for variable amout of time (r1 / 2)
            "tr 0x0, 0x0, 0x2, 0x0, 0x0, 0x0",  # Rotate Frame
            "tr 0x0, 0x0, 0x3, 0x0, 0x0, 0x0",  # Play
            "wti 0x4",  # Wait for pi-pulse
            "tr 0x0, 0x0, 0x4, 0x0, 0x0, 0x0",  # Rotate Frame
            "wtr r2, 0x0",  # Wait for delay agabin
            "addi r3, r3, 0x1",  # Increment: r3 := r3 + 1
            "j -0x8",  # Jump to loop start
            "tr 0x0, 0x0, 0x1, 0x0, 0x0, 0x0",  # Trigger pi/2 pulse
            "wti 0x2",  # Wait...
            "tr 0x1, 0x1, 0x0, 0x0, 0x0, 0x0",  # Record qubit state
            "wti 0x64",
            "wti 0x30d4",  # wait for T1
            "addi r1, r1, 0x32",  # Increment r1
            "j -0x16",  # Jump to outer loop start
            "end",
        ]
    )


def test_allxy_calibration():
    """
    AllXY gate-pair diagnostic with 5 representative pairs.

    Two QiVariables hold the per-pair phase for gate-1 and gate-2 respectively.
    A ForRange iterates over the pair index and uses QiIndexed (via __getitem__)
    to fetch each phase dynamically.
    """
    N = 5
    # Five representative AllXY pairs: (Id,Id), (X,X), (Y,Y), (X,Y), (Y,X)
    g1_phases = [0.0, 0.0, math.pi / 2, 0.0, math.pi / 2]
    g2_phases = [0.0, 0.0, math.pi / 2, math.pi / 2, 0.0]

    with QiJob() as job:
        q = QiCells(1)
        # QiVariable with an iterable value creates an array variable;
        # the element type (PHASE) is inferred from the pulse's phase= argument.
        phases1 = QiVariable(value=g1_phases)  # gate-1 phase per pair
        phases2 = QiVariable(value=g2_phases)  # gate-2 phase per pair
        idx = QiIntVariable()

        with ForRange(idx, 0, N, 1):
            Play(q[0], QiPulse(20e-9, phase=phases1[idx]))  # gate 1
            Play(q[0], QiPulse(20e-9, phase=phases2[idx]))  # gate 2
            Recording(q[0], 400e-9, save_to="result")

    assert (
        job.get_assembly()
        == snapshot(
            [
                "tr 0x0, 0x0, 0x0, 0x0, 0x0, 0x0",  # Start trigger
                "addi r2, r0, 0x5",  # Set r2 = 5
                "addi r1, r0, 0x0",  # Set r1 = 0
                "bge r1, r2, 0x17",  # If r1 > r2 => Jump to end
                "lui r4, 0x8000",  # Set r4 = 0x8400 (memory base address)
                "addi r4, r4, 0x400",  # ...
                "add r3, r1, r4",  # Set r3 := r1 + r4 (memory address)
                "lw r4, 0(r3)",  # Load the memory at the address -> Store to r4
                "lui r5, 0x6000",  # Set r5 := 0x600C
                "addi r5, r5, 0xc",  # ...
                "sw r4, 0(r5)",  # Set NCO Phase using memory-mapped I/O
                "tr 0x0, 0x0, 0x1, 0x0, 0x0, 0x0",  # First play command
                "wti 0x4",  # Wait until play is done...
                "lui r6, 0x8000",  # Set r6 = 0x8405 (memory base address 2)
                "addi r6, r6, 0x405",  # ...
                "add r5, r1, r6",  # Increment r5 := r1 + r6 (memory address)
                "lw r6, 0(r5)",  # Load r6 := mem[r5] (gate-2 phase at index)
                "lui r7, 0x6000",  # Set r7 := 0x600C
                "addi r7, r7, 0xc",  # ...
                "sw r6, 0(r7)",  # Set NCO address
                "tr 0x0, 0x0, 0x1, 0x0, 0x0, 0x0",  # Second Play command (second phase applied)
                "wti 0x4",  # Wait until second play is over
                "tr 0x0, 0x1, 0x0, 0x0, 0x0, 0x0",  # Trigger Recording
                "wti 0x64",  # Wait for recording to finish
                "addi r1, r1, 0x1",  # Increment r1 by 1
                "j -0x16",  # Jump to loop start
                "end",
            ]
        )
    )


def _collect_save_to(cmds):
    """Collect save_to strings from RecordingCommands, including those linked via PlayReadoutCommand.recording."""
    result = set()
    for cmd in cmds:
        if isinstance(cmd, RecordingCommand) and isinstance(cmd.save_to, str):
            result.add(cmd.save_to)
        if isinstance(cmd, PlayReadoutCommand) and isinstance(
            cmd.recording, RecordingCommand
        ):
            if isinstance(cmd.recording.save_to, str):
                result.add(cmd.recording.save_to)
    return result


# The second job should produce identical results like the first job (maybe except for register allocation).
# However, the wait times are longer in the second job.
# This is potentially a bug in the Sync calculation.
@pytest.mark.skip(reason="Unresolved Bug")
def test_two_qubit_parallel_readout():
    """Simultaneous readout of two qubits via Parallel PlayReadout with independent Recordings."""
    with QiJob() as job:
        q = QiCells(2)
        sweep = QiIntVariable()

        with ForRange(sweep, 0, 3, 1):
            with Parallel():
                PlayReadout(q[0], QiPulse(500e-9))
                Recording(q[0], 500e-9, save_to="result_q0")
                PlayReadout(q[1], QiPulse(500e-9))
                Recording(q[1], 500e-9, save_to="result_q1")
            Sync(q[0], q[1])

    assert job.get_assembly(0) == snapshot(
        [
            "tr 0x0, 0x0, 0x0, 0x0, 0x0, 0x0",
            "addi r2, r0, 0x3",
            "addi r1, r0, 0x0",
            "bge r1, r2, 0x5",
            "tr 0x1, 0x1, 0x0, 0x0, 0x0, 0x0",
            "wti 0x7d",
            "addi r1, r1, 0x1",
            "j -0x4",
            "end",
        ]
    )

    assert job.get_assembly(1) == snapshot(
        [
            "tr 0x0, 0x0, 0x0, 0x0, 0x0, 0x0",
            "addi r2, r0, 0x3",
            "addi r1, r0, 0x0",
            "bge r1, r2, 0x5",
            "tr 0x1, 0x1, 0x0, 0x0, 0x0, 0x0",
            "wti 0x7d",  # Bug here: job.get_assembly(1) returns 0x6F; should be 0x7D
            "addi r1, r1, 0x1",
            "j -0x4",
            "end",
        ]
    )


def test_frequency_swept_spectroscopy():
    """Frequency-swept spectroscopy: ForRange over a QiFrequencyVariable sweeps
    the drive frequency from (center - span/2) to (center + span/2) in steps of
    freq_step.  Each iteration plays a drive pulse at the current frequency and
    immediately records the response.
    """
    center_freq = 100e6  # Hz
    span = 20e6  # Hz  -> sweep 90 MHz ... 110 MHz
    freq_step = 1e6  # Hz  -> 20 steps

    with QiJob() as job:
        q = QiCells(1)
        freq = QiFrequencyVariable()

        with ForRange(
            freq,
            center_freq - span / 2,  # 90 MHz start
            center_freq + span / 2,  # 110 MHz stop (exclusive)
            freq_step,  # 1 MHz step
        ):
            Play(q[0], QiPulse(1e-6, frequency=freq))
            PlayReadout(q[0], QiPulse(1e-6, frequency=100e6))
            Recording(q[0], 1e-6, save_to="spec")

    assert job.get_assembly() == snapshot(
        [
            "tr 0x0, 0x0, 0x0, 0x0, 0x0, 0x0",  # Start
            "lui r2, 0x1c6a8000",  # Set r2 := Loop end
            "addi r2, r2, 0xef4",  # ...
            "lui r1, 0x170a4000",  # Set r1 := loop start
            "addi r1, r1, 0xd71",  # ...
            "bge r1, r2, 0xc",  # If r1 > r2 => jump to end
            "lui r3, 0x6000",  # Load memory address
            "addi r3, r3, 0x5",  # ...
            "sw r1, 0(r3)",  # Store r1 -> Memory address (set NCO frequency)
            "tr 0x0, 0x0, 0x1, 0x0, 0x0, 0x0",  # Play manipulation pulse
            "wti 0xf9",  # Wait until manipulation has finished
            "tr 0x1, 0x1, 0x0, 0x0, 0x0, 0x0",  # Play Readout + Recording
            "wti 0xfa",  # Wait for finish
            "lui r3, 0x419000",  # Address increment
            "addi r3, r3, 0x937",  # ...
            "add r1, r1, r3",  # Increment address
            "j -0xb",  # Jump to start
            "end",
        ]
    )


def test_amplitude_phase_sweep():
    with QiJob() as job:
        cells = QiCells(1)
        for q in cells:
            a = QiAmplitudeVariable()
            p = QiPhaseVariable()
            with ForRange(a, 0, 0.5, 0.01):
                with ForRange(p, 0, 2 * math.pi, 0.01):
                    PlayReadout(q, QiPulse(amplitude=a, length=1e-6, frequency=0))
                    Recording(q, duration=1e-6, offset=52e-9, save_to="result")

    assert job.get_assembly() == snapshot(
        [
            "tr 0x0, 0x0, 0x0, 0x0, 0x0, 0x0",
            "lui r3, 0x4000",
            "addi r3, r3, 0xfff",
            "addi r1, r0, 0x0",
            "bge r1, r3, 0xf",
            "sll r4, r1, 0x10",
            "or r5, r1, r4",
            "lui r4, 0x4000",
            "addi r4, r4, 0x4",
            "sw r5, 0(r4)",
            "lui r4, 0x10000",
            "addi r2, r0, 0x0",
            "bge r2, r4, 0x5",
            "tr 0x1, 0x1, 0x0, 0x0, 0x0, 0x0",
            "wti 0xfa",
            "addi r2, r2, 0x68",
            "j -0x4",
            "addi r1, r1, 0x147",
            "j -0xe",
            "end",
        ]
    )
