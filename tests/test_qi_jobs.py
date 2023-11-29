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
import unittest
import json
import os
from qiclib.code.qi_seq_instructions import SeqTrigger

from qiclib.code.qi_pulse import QiPulse, ShapeLib
import qiclib.packages.utility as util
from qiclib.code.qi_jobs import (
    QiSample,
    QiTimeVariable,
    QiVariable,
    QiStateVariable,
    Play,
    PlayReadout,
    QiJob,
    QiCells,
    QiCell,
    QiCellProperty,
    RotateFrame,
    Store,
    Sync,
    cQiAssign,
)
from qiclib.code.qi_jobs import Recording, Wait, Assign, If, Else, ForRange, Parallel
from qiclib.code.qi_jobs import cQiPlay, cQiPlayReadout, cQiSync
from qiclib.code.qi_jobs import (
    cQiRecording,
    QiResult,
    QiGate,
    _set_job_reference,
    _delete_job_reference,
)


class QiCellTest(unittest.TestCase):
    def setUp(self):
        job = QiJob()
        _set_job_reference(job)

    def tearDown(self):
        _delete_job_reference()

    def test_no_length_inside_job(self):
        q = QiCells(1)
        self.assertIsInstance(q[0]["nothing here"], QiCellProperty)


class QiSampleCellTest(unittest.TestCase):
    def setUp(self) -> None:
        sample = QiSample(1)
        sample[0].cellID = 42
        self.sample = sample[0]
        self.sample["recording_length"] = 400e-9

    def test_length(self):
        self.assertEqual(self.sample["recording_length"], 400e-9)

    def test_no_length(self):
        with self.assertRaises(KeyError):
            self.sample["nothing here"]

    def test_new_length(self):
        self.sample["pi_pulse"] = 48e-9
        self.assertEqual(self.sample["pi_pulse"], 48e-9)

    def test_new_recording_length(self):
        self.sample["recording_length"] = 48e-9
        self.assertEqual(self.sample["recording_length"], 48e-9)

    def test_export_cell(self):

        new_sample = QiSample(1)[0]
        new_sample["electrical_delay"] = 42e-9
        new_sample["recording_length"] = 400e-9
        self.assertEqual(
            new_sample._export(),
            {"properties": {"electrical_delay": 4.2e-08, "recording_length": 4e-07}},
        )

    def test_import_cell(self):
        new_sample = QiSample(1)[0]
        new_sample._import(
            {"electrical_delay": 200e-9, "recording_length": 5e-07, "new_prop": 42e-9},
            0,
        )

        self.assertEqual(new_sample["electrical_delay"], 200e-9)
        self.assertEqual(new_sample["recording_length"], 500e-9)
        self.assertEqual(new_sample["new_prop"], 42e-9)

    def test_export_qi_cells(self):
        s = QiSample(2)

        s[0]["pi_pulse"] = 42e-9

        expected = {
            "cells": [
                {
                    "properties": {
                        "pi_pulse": 4.2e-08,
                    }
                },
                {"properties": {}},
            ],
            "cell_map": [0, 1],
        }

        self.assertEqual(s._export(), expected)

    def test_import_qi_cells(self):
        s = QiSample(2)
        s._import(
            '{"cells": [{"properties": {"electrical_delay": 2.0e-7, "recording_length": 5e-07, "pi_pulse": 4.2e-08}}, {"properties": {"electrical_delay": 0.0, "recording_length": 4e-07}}]}'
        )

        self.assertEqual(s[0]["electrical_delay"], 200e-9)
        self.assertEqual(s[0]["recording_length"], 500e-9)
        self.assertEqual(s[0]["pi_pulse"], 42e-9)

        self.assertEqual(s[1]["electrical_delay"], 0)
        self.assertEqual(s[1]["recording_length"], 400e-9)
        with self.assertRaises(KeyError):
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

        self.assertEqual(
            file_data,
            {
                "cells": [
                    {
                        "properties": {
                            "electrical_delay": 4.2e-08,
                            "recording_length": 4e-07,
                        }
                    }
                ],
                "cell_map": [0],
            },
        )

        # export again
        s[0]["electrical_delay"] = 41e-9

        with self.assertRaises(FileExistsError):
            s.save(fp)

        s.save(fp, overwrite=True)

        with open(fp) as file:
            file_data = json.load(file)

        self.assertEqual(
            file_data,
            {
                "cells": [
                    {
                        "properties": {
                            "electrical_delay": 4.1e-08,
                            "recording_length": 4e-07,
                        }
                    }
                ],
                "cell_map": [0],
            },
        )

        os.remove(fp)

    def test_load_from_file(self):
        s = QiSample(2)
        path = os.path.join(os.path.dirname(__file__), "test_files/properties_ok.json")
        s.load(path)

        self.assertEqual(s[0]["electrical_delay"], 200e-9)
        self.assertEqual(s[0]["recording_length"], 500e-9)
        self.assertEqual(s[0]["pi_pulse"], 42e-9)

    def test_load_file_error(self):
        s = QiSample(1)

        with self.assertRaises(json.JSONDecodeError):
            path = os.path.join(
                os.path.dirname(__file__), "test_files/properties_error.json"
            )
            s.load(path)

    def test_load_file_wrong_cell_count(self):
        s = QiSample(1)

        with self.assertRaisesRegex(
            ValueError,
            "Imported JSON contains \d+ sample cells but \d+ expected.",
        ):
            path = os.path.join(
                os.path.dirname(__file__), "test_files/properties_ok.json"
            )
            s.load(path)

    def test_import_qi_cells_error(self):
        s = QiSample(1)
        with self.assertWarnsRegex(
            UserWarning, "Imported JSON string does not contain 'cells'."
        ):
            s._import(
                '{"properties": {"electrical_delay": 0.0, "recording_length": 4e-07, "pi_pulse": 4.2e-08}}'
            )

        with self.assertWarnsRegex(
            UserWarning,
            r"Imported JSON string does not contain 'properties' for cell\[\d+\]\.",
        ):
            s._import(
                '{"cells": [{"electrical_delay": 4.1e-08, "recording_length": 4e-07}]}'
            )


class QiCommandTest(unittest.TestCase):
    def setUp(self) -> None:
        job = QiJob()
        self.job = job
        _set_job_reference(job)
        self.cell = QiCell(42)
        self.cell["electrical_delay"] = 0
        self.cell["recording_length"] = 400e-9
        self.result = "result"

    def tearDown(self) -> None:
        _delete_job_reference()
        return super().tearDown()

    def test_recording_length(self):
        rec = cQiRecording(
            self.cell,
            self.result,
            None,
            length=self.cell["recording_length"],
            offset=self.cell["electrical_delay"],
        )

        self.assertEqual(self.cell["recording_length"], rec.length)

    def test_recording_error(self):
        # Raises error: cQiRecording needs state variable
        var = QiTimeVariable()
        with self.assertRaises(TypeError):
            rec = cQiRecording(
                self.cell,
                None,
                var,
                length=self.cell["recording_length"],
                offset=self.cell["electrical_delay"],
            )

    def test_recording_state(self):
        var = QiStateVariable()

        rec = cQiRecording(
            self.cell,
            None,
            var,
            length=self.cell["recording_length"],
            offset=self.cell["electrical_delay"],
        )

        self.assertEqual(rec.uses_state, True)

        # Test also with additional QiResult supplied
        rec = cQiRecording(
            self.cell,
            self.result,
            var,
            length=self.cell["recording_length"],
            offset=self.cell["electrical_delay"],
        )

        self.assertEqual(rec.uses_state, True)

    def test_assign_error(self):
        # Raises error: Cannot assign to state variable
        var = QiStateVariable()
        with self.assertRaises(
            TypeError,
        ):
            Assign(var, 1)

        with self.assertRaisesRegex(
            TypeError, "Target of Assign can only be a QiVariable."
        ):
            Assign(1, 1)

        with self.assertRaisesRegex(
            TypeError, "Target of Assign can only be a QiVariable."
        ):
            q = QiCell(31)
            Assign(q, 1)

    def test_ForRange_end_value_warning(self):
        # Warns that end value 0 is not included
        var = QiTimeVariable()
        with ForRange(var, 20e-9, 0, -4e-9):
            Wait(self.cell, var)

        with self.assertWarnsRegex(
            UserWarning, "End value of 0 will not be included in ForRange."
        ):
            self.job.__exit__(None, None, None)

    def test_ForRange_var_start_end_warning(self):
        # Warns that unrolling is not supported for variable start/end times
        var = QiTimeVariable()
        var2 = QiTimeVariable()
        with self.assertRaisesRegex(
            RuntimeError,
            "Loop variable can not be used as start value",
        ):
            with ForRange(var, var, var2, -4e-9):
                Wait(self.cell, var)

        with self.assertRaisesRegex(
            RuntimeError,
            "Loop variable can not be used as end value",
        ):
            with ForRange(var, var2, var, -4e-9):
                Wait(self.cell, var)

    def test_ForRange_error(self):
        # Raises error: step must be multiple of 4e-9
        var = QiTimeVariable()
        with ForRange(var, 20e-9, 0, -3e-9):
            Wait(self.cell, var)

        with self.assertRaises(RuntimeError):
            with self.assertWarnsRegex(
                UserWarning, "End value of 0 will not be included in ForRange."
            ):
                self.job.__exit__(None, None, None)

    def test_ForRange_state_error(self):
        # Raises error: step must be multiple of 4e-9
        var = QiStateVariable()
        with self.assertRaises(TypeError):
            with ForRange(var, 20e-9, 0, -4e-9):
                Wait(self.cell, var)

    def test_ForRange_Parallel_var_warning(self):
        # Raises error: step must be multiple of 4e-9
        var = QiTimeVariable()
        warning_msg = r"Loop variable inside Parallel Context Manager might result in unexpected behaviour\. Please unroll loop or change variable"
        with self.assertRaisesRegex(RuntimeError, warning_msg):
            with ForRange(var, 52e-9, 0, -4e-9):
                with Parallel():
                    Play(self.cell, QiPulse(42e-9))
                with Parallel():
                    Wait(self.cell, var)

    def test_ForRange_OK(self):
        try:
            var = QiTimeVariable()
            with ForRange(var, 0, 100e-9, 24e-9):
                Wait(self.cell, var)
        except Exception as e:
            self.fail("test_ForRange_OK raised exception " + str(e))

    def test_ForRange_negative_OK(self):
        try:
            var = QiTimeVariable()
            with ForRange(var, 100e-9, 0, -20e-9):
                Wait(self.cell, var)

            with self.assertWarnsRegex(
                UserWarning, "End value of 0 will not be included in ForRange."
            ):
                self.job.__exit__(None, None, None)

        except Exception as e:
            self.fail("test_ForRange_OK raised exception " + str(e))

    def test_for_range_definition_error(self):
        var = QiVariable(int)
        with self.assertRaises(ValueError):
            for_cmd = ForRange(var, 0, 5, -1)

        with self.assertRaises(ValueError):
            for_cmd = ForRange(var, 5, 0, 1)

        with self.assertRaises(ValueError):
            for_cmd = ForRange(var, 0, 5, 0)


class QiJobDescriptionTest(unittest.TestCase):
    def test_QiVariable_init(self):
        value = 2
        with QiJob() as test:
            var1 = QiVariable(int, value)

        cmd = test.commands[1]

        self.assertIsInstance(cmd, cQiAssign)

        if isinstance(cmd, cQiAssign):
            self.assertEqual(cmd._value, value)

    def test_QiTimeVariable_init(self):
        value = 200e-9
        with QiJob() as test:
            var1 = QiTimeVariable(value)

        cmd = test.commands[1]

        self.assertIsInstance(cmd, cQiAssign)

        if isinstance(cmd, cQiAssign):
            self.assertEqual(cmd.value.value, util.conv_time_to_cycles(value))

    def test_if_else_OK(self):
        with QiJob():
            var1 = QiVariable(int)
            with If(var1 > 3) as if_cm:
                Assign(var1, 0)
            with Else():
                Assign(var1, 0)

        self.assertEqual(len(if_cm._else_body), 1)
        self.assertTrue(if_cm.is_followed_by_else())

    def test_recording_OK(self):
        with QiJob(skip_nco_sync=True) as rec_job:
            q = QiCells(1)
            Recording(q[0], 4e-9, save_to="test")

        cmd = rec_job.commands[0]

        self.assertIsInstance(cmd, cQiRecording)

        if isinstance(cmd, cQiRecording):
            self.assertEqual(cmd.length, 4e-9)
            self.assertFalse(cmd.follows_readout)

    def test_recording_after_readout(self):
        with QiJob(skip_nco_sync=True) as rec_job:
            q = QiCells(1)
            PlayReadout(q[0], QiPulse(4e-9))
            Recording(q[0], 4e-9, save_to="test")

        cmd = rec_job.commands[0]

        if isinstance(cmd, cQiPlayReadout):
            self.assertIsInstance(cmd.recording, cQiRecording)

    def test_multiple_qicells_calls_Error(self):
        with self.assertRaisesRegex(
            RuntimeError, "Can only register one set of cells at a QiJob."
        ):
            with QiJob() as test:
                q = QiCells(1)
                p = QiCells(1)

    def test_qicells_in_multiple_jobs_Error(self):
        with QiJob() as test1:
            q = QiCells(1)
            q[0]["test"] = 100e-9

        with self.assertRaisesRegex(
            RuntimeError, "Tried setting values for cells registered to other QiJob"
        ):
            with QiJob() as test2:
                q[0]["test"] = 200e-9

        with self.assertRaisesRegex(
            RuntimeError, "Tried getting values for cells registered to other QiJob"
        ):
            with QiJob() as test3:
                length = q[0]["test"]

    def test_different_qi_cell_values_no_overwrite(self):
        with QiJob() as test1:
            q = QiCells(1)
            q[0]["test"] = 100e-9

        with QiJob() as test2:
            q = QiCells(1)
            q[0]["test"] = 200e-9

        self.assertEqual(test1.cells[0]._properties.get("test"), 100e-9)
        self.assertEqual(test2.cells[0]._properties.get("test"), 200e-9)

    def test_single_recording_box_retrieval(self):
        try:
            with QiJob() as rec_job:
                q = QiCells(1)
                Recording(q[0], 4e-9, save_to="data0")
                q[0]._result_container["data0"].data = [42]
        except Exception as e:
            self.fail("test_single_recording_box_OK raised exception " + str(e))

        result = rec_job.cells[0].data()  # returns dict of all data boxes

        self.assertEqual(result.get("data0"), [42])

        result = rec_job.cells[0].data(
            "data0"
        )  # returns data of result box with name data0

        self.assertEqual(result[0], 42)

        # After build should be the same
        rec_job._build_program()

        result = rec_job.cells[0].data()  # returns list of all data boxes

        self.assertEqual(len(result.get("data0")), 0)  # reset after build_program

    def test_single_recording_box_retrieval_string_init(self):
        try:
            with QiJob() as rec_job:
                q = QiCells(1)
                Recording(q[0], 4e-9, save_to="data0")
                q[0]._result_container["data0"].data = [42]
        except Exception as e:
            self.fail("test_single_recording_box_OK raised exception " + str(e))

        result = rec_job.cells[0].data()  # returns list of all data boxes

        self.assertEqual(len(result), 1)

        result = rec_job.cells[0].data(
            "data0"
        )  # returns data of result box with name data0

        self.assertEqual(result[0], 42)

        rec_job._build_program()

        result = rec_job.cells[0].data()  # returns list of all data boxes

        self.assertEqual(len(result), 1)

    def test_if_else_Error(self):
        # Else only directly after If possible
        with self.assertRaisesRegex(RuntimeError, "Else is not preceded by If"):
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
        with self.assertRaisesRegex(
            RuntimeError,
            "Variable used in ForRange must not be used in internal Assign-Commands",
        ):
            with QiJob():
                var1 = QiVariable(int)
                with ForRange(var1, 0, 5, 1):
                    with If(var1 == 4):
                        Assign(var1, 0)

    def test_assign_var_in_for_range_OK(self):
        try:
            with QiJob():
                var1 = QiVariable(int)
                var2 = QiVariable(int)
                with ForRange(var1, 0, 5, 1):
                    with If(var1 == 4):
                        Assign(var2, 0)
        except Exception as e:
            self.fail("test_assign_var_in_for_range_OK raised exception " + str(e))

    def test_Parallel_Type_Error(self):
        with self.assertRaisesRegex(TypeError, "Type not allowed inside Parallel()"):
            with QiJob():
                var1 = QiVariable(int)
                with Parallel():
                    with If(var1 == 4):
                        Assign(var1, 0)

    def test_Parallel_state_recording_Error(self):
        with self.assertRaisesRegex(
            RuntimeError, "Can not save to state variable inside Parallel"
        ):
            with QiJob() as para_job:
                q = QiCells(2)
                var = QiStateVariable()
                with Parallel():
                    PlayReadout(q[0], QiPulse(length=50e-9))
                    Recording(q[1], 400e-9, state_to=var)

    def test_Parallel_OK(self):
        try:
            with QiJob() as para_job:
                q = QiCells(1)
                with Parallel():
                    Play(q[0], QiPulse(length=50e-9))
                    PlayReadout(q[0], QiPulse(length=50e-9))
        except Exception as e:
            self.fail("test_Parallel_OK raised exception " + str(e))

    def test_combine_Parallel(self):
        with QiJob() as para_job:
            q = QiCells(1)
            with Parallel():
                Play(q[0], QiPulse(length=50e-9))
            with Parallel():
                PlayReadout(q[0], QiPulse(length=50e-9))

        self.assertEqual(len(para_job.commands), 1)

        para = para_job.commands[0]

        if isinstance(para, Parallel):
            self.assertEqual(len(para.entries), 2)

    def test_not_combine_Parallel(self):
        with QiJob() as para_job:
            q = QiCells(2)
            with Parallel():
                Play(q[0], QiPulse(length=50e-9))
            with Parallel():
                PlayReadout(q[1], QiPulse(length=50e-9))
            with Parallel():
                Play(q[1], QiPulse(length=50e-9))

        self.assertEqual(len(para_job.commands), 2)

        para = para_job.commands[0]

        if isinstance(para, Parallel):  # first Parallel should contain 2 entries
            self.assertEqual(len(para.entries), 2)

        para = para_job.commands[1]

        if isinstance(para, Parallel):  # second Parallel should contain 1 entries
            self.assertEqual(len(para.entries), 1)

    def test_undefined_property_OK(self):
        try:
            with QiJob() as job:
                q = QiCells(1)

                Play(q[0], QiPulse(length=q[0]["PiPulse"]))
                PlayReadout(q[0], QiPulse(length=q[0]["PiPulse"]))
                Wait(q[0], q[0]["PiPulse"])
        except Exception as e:
            self.fail("test_not_defined_property_OK raised exception " + str(e))

    def test_command_outside_job_error(self):
        with QiJob() as job:
            q = QiCells(1)

            Play(q[0], QiPulse(length=48e-9))

        with self.assertRaisesRegex(
            RuntimeError, "Can not use command outside QiJob context manager."
        ):
            Wait(q[0], 20e-9)

    def test_variable_outside_job_error(self):
        with self.assertRaisesRegex(
            RuntimeError, "Can not use command outside QiJob context manager."
        ):
            var = QiVariable(int)

        with self.assertRaisesRegex(
            RuntimeError, "Can not use command outside QiJob context manager."
        ):
            var = QiTimeVariable(42e-9)

        with self.assertRaisesRegex(
            RuntimeError, "Can not use command outside QiJob context manager."
        ):
            var = QiStateVariable()

    def test_undefined_recording_property(self):
        try:
            with QiJob() as test:
                q = QiCells(1)
                Recording(q[0], q[0]["len"], q[0]["off"])

        except Exception as e:
            self.fail("test_undefined_recording_property raised exception " + str(e))

    def test_buid_cooltest(self):
        try:
            with QiJob() as cool_test:
                q = QiCells(1)
                length = QiVariable()

                with ForRange(length, 0, 20):
                    Play(q[0], QiPulse(length=length))
                    PlayReadout(q[0], QiPulse(length=length))
                    Wait(q[0], length)

            cool_test._build_program()
        except Exception as e:
            self.fail("test_cooltest raised exception " + str(e))

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
                x = QiVariable(int)
                Play(q[0], QiPulse(length=length))
                PlayReadout(q[0], QiPulse(length=length))
                Wait(q[0], length)
                Recording(q[0], 1, 0)

        string = str(str_job)
        self.assertEqual(
            string,
            """\
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
        Recording(q[0], 1)""",
        )

    def test_stringify_rabi(self):
        from qiclib.experiment.qicode.collection import Rabi

        rabi = Rabi(0, 1e-6, 100e-9)
        string = str(rabi)
        self.assertEqual(
            string,
            """\
QiJob:
    q = QiCells(1)
    v0 =  QiVariable()
    ForRange(v0, 0, 1e-06, 1e-07):
        Play(q[0], QiPulse(v0, frequency=q[0]["manip_frequency"]))
        PlayReadout(q[0], QiPulse(q[0]["rec_pulse"], frequency=q[0]["rec_frequency"]))
        Recording(q[0], q[0]["rec_length"], offset=q[0]["rec_offset"], save_to="result")
        Wait(q[0], 5 * q[0]["T1"])""",
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
        self.assertEqual(
            string,
            """\
QiJob:
    q = QiCells(1)
    Parallel:
        Play(q[0], QiPulse(1e-07, frequency=6e+07))
        Play(q[0], QiPulse(1e-07, frequency=6e+07))
    Parallel:
        PlayReadout(q[0], QiPulse(1e-07, frequency=4e+07))""",
        )

    def test_stringify_active_reset(self):
        from qiclib.experiment.qicode.collection import ActiveReset

        job = ActiveReset()
        string = str(job)
        self.assertEqual(
            string,
            """\
QiJob:
    q = QiCells(1)
    v0 =  QiVariable()
    PlayReadout(q[0], QiPulse(q[0]["rec_pulse"], frequency=q[0]["rec_frequency"]))
    Recording(q[0], q[0]["rec_length"], offset=q[0]["rec_offset"], state_to=v0)
    If(v0 != 0):
        Play(q[0], QiPulse(q[0]["pi"], frequency=q[0]["manip_frequency"]))
    PlayReadout(q[0], QiPulse(q[0]["rec_pulse"], frequency=q[0]["rec_frequency"]))
    Recording(q[0], q[0]["rec_length"], offset=q[0]["rec_offset"], save_to="result")""",
        )

    def test_stringify_two_jobs(self):
        with QiJob() as job1:
            q = QiCells(1)
            var = QiVariable()
        with QiJob() as job2:
            q = QiCells(1)
            var = QiVariable()
        string = str(job1) + "\n" + str(job2)
        self.assertEqual(
            string,
            """\
QiJob:
    q = QiCells(1)
    v0 =  QiVariable()
QiJob:
    q = QiCells(1)
    v0 =  QiVariable()""",
        )

    def test_stringify_shapes(self):
        with QiJob() as job:
            q = QiCells(1)
            pulse = QiPulse(10e-6, ShapeLib.gauss)
            Play(q[0], pulse)
        string = str(job)
        self.assertEqual(
            string,
            """\
QiJob:
    q = QiCells(1)
    Play(q[0], QiPulse(1e-05, shape=Shape(gauss)))""",
        )

    def test_stringify_qicellprop(self):
        with QiJob() as test:
            q = QiCells(1)
            Wait(q[0], 5 * q[0]["T1"])
        string = str(test)
        self.assertEqual(
            string,
            """\
QiJob:
    q = QiCells(1)
    Wait(q[0], 5 * q[0]["T1"])""",
        )


class QiJobDescriptionMissingPropertyTest(unittest.TestCase):
    def setUp(self) -> None:
        with QiJob() as self.job:
            q = QiCells(1)

            Play(q[0], QiPulse(length=q[0]["PiPulse"], frequency=q[0]["Manip_Freq"]))
            Wait(q[0], q[0]["Wait"])
            Recording(q[0], q[0]["rec"], q[0]["offset"])

    def test_property_defined_OK(self):
        test = QiSample(1)
        test[0]["PiPulse"] = 52e-9
        test[0]["Manip_Freq"] = 60e6
        test[0]["Wait"] = 52e-9
        test[0]["rec"] = 200e-9
        test[0]["offset"] = 48e-9

        self.job._build_program(test)
        print(self.job)

        self.assertEqual(self.job.commands[0].length, test[0]["PiPulse"])
        self.assertEqual(
            self.job.cells[0].initial_manipulation_frequency, test[0]["Manip_Freq"]
        )
        self.assertEqual(self.job.commands[1].length, test[0]["Wait"])
        self.assertEqual(self.job.commands[2].length, test[0]["rec"])

    def test_property_defined_Error(self):
        test = QiSample(1)
        with self.assertRaisesRegex(
            RuntimeError,
            "Not all properties for job could be resolved. Missing properties:",
        ):
            self.job._build_program(test)

    def test_property_defined_no_cell_Error(self):
        with self.assertRaisesRegex(
            ValueError,
            "QiSample needs to be passed to resolve job properties!",
        ):
            self.job._build_program()

    def test_property_too_many_cells_Error(self):
        test = QiSample(2)
        test[0]["PiPulse"] = 52e-9

        with self.assertRaisesRegex(
            RuntimeError,
            "Not all properties for job could be resolved. Missing properties:",
        ):
            self.job._build_program(test)


class QiGateTest(unittest.TestCase):
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
            q = QiCells(2)
            self.PlayPulse(48e-9, gate_test.cells[0])

        self.assertEqual(len(gate_test.commands), 1)
        self.assertIsInstance(gate_test.commands[0], cQiPlay)

    def test_multi_cell_function(self):
        with QiJob(skip_nco_sync=True) as gate_test:
            q = QiCells(2)
            self.PlayPulses(48e-9, gate_test.cells[0], gate_test.cells[1])

        self.assertEqual(len(gate_test.commands), 3)

        sync = gate_test.commands[0]
        self.assertIsInstance(sync, cQiSync)

        if isinstance(sync, cQiSync):
            self.assertIn(gate_test.cells[0], sync._relevant_cells)
            self.assertIn(gate_test.cells[1], sync._relevant_cells)

        self.assertIsInstance(gate_test.commands[1], cQiPlay)
        self.assertIsInstance(gate_test.commands[2], cQiPlay)

    def test_gate_cell_getitem_function(self):
        with QiJob(skip_nco_sync=True) as gate_test:
            q = QiCells(2)
            self.Readout(gate_test.cells[0])

        self.assertEqual(len(gate_test.commands), 1)
        self.assertIsInstance(gate_test.commands[0], cQiPlayReadout)

    def test_gate_assign_var(self):
        with self.assertRaises(RuntimeError):
            with QiJob(skip_nco_sync=True) as gate_test:
                variable = QiVariable(int)
                self.AssignVar(variable)


class PulseToCellTest(unittest.TestCase):
    def test_equal_pulses(self):
        with QiJob(skip_nco_sync=True) as test:
            q = QiCells(2)
            Play(q[0], QiPulse(length=50e-9))
            Play(q[0], QiPulse(length=50e-9))

            Play(q[1], QiPulse(length=50e-9))
            Play(q[1], QiPulse(length=50e-9))

        self.assertEqual(len(test.cells[0].manipulation_pulses), 1)

        self.assertEqual(test.commands[0].trigger_index, 1)
        self.assertEqual(test.commands[1].trigger_index, 1)

        self.assertEqual(test.commands[2].trigger_index, 1)
        self.assertEqual(test.commands[3].trigger_index, 1)

    def test_different_pulses(self):
        with QiJob(skip_nco_sync=True) as test:
            q = QiCells(1)
            Play(q[0], QiPulse(length=50e-9))
            Play(q[0], QiPulse(length=100e-9))

        self.assertEqual(len(test.cells[0].manipulation_pulses), 2)

        self.assertEqual(test.commands[0].trigger_index, 1)
        self.assertEqual(test.commands[1].trigger_index, 2)

    def test_variable_pulses(self):
        with QiJob(skip_nco_sync=True) as test:
            q = QiCells(1)
            var = QiVariable()

            Play(q[0], QiPulse(length=var))
            Play(q[0], QiPulse(length=var))

        self.assertEqual(len(test.cells[0].manipulation_pulses), 1)

        # commands[0] is QiDeclare
        self.assertEqual(test.commands[1].trigger_index, 1)
        self.assertEqual(test.commands[2].trigger_index, 1)

    def test_equal_readoutpulses(self):
        with QiJob(skip_nco_sync=True) as test:
            q = QiCells(1)
            PlayReadout(q[0], QiPulse(length=50e-9))
            PlayReadout(q[0], QiPulse(length=50e-9))

        self.assertEqual(len(test.cells[0].readout_pulses), 1)

        self.assertEqual(test.commands[0].trigger_index, 1)
        self.assertEqual(test.commands[1].trigger_index, 1)

    def test_different_readoutpulses(self):
        with QiJob(skip_nco_sync=True) as test:
            q = QiCells(1)
            PlayReadout(q[0], QiPulse(length=50e-9))
            PlayReadout(q[0], QiPulse(length=100e-9))

        self.assertEqual(len(test.cells[0].readout_pulses), 2)

        self.assertEqual(test.commands[0].trigger_index, 1)
        self.assertEqual(test.commands[1].trigger_index, 2)

    def test_variable_readoutpulses(self):
        with QiJob(skip_nco_sync=True) as test:
            q = QiCells(1)
            var = QiVariable()

            PlayReadout(q[0], QiPulse(length=var))
            PlayReadout(q[0], QiPulse(length=var))

        self.assertEqual(len(test.cells[0].readout_pulses), 1)

        # commands[0] is QiDeclare
        self.assertEqual(test.commands[1].trigger_index, 1)
        self.assertEqual(test.commands[2].trigger_index, 1)

    def test_state_variable_in_combined_play_readout_and_recording(self):
        with QiJob() as job:
            q = QiCells(1)
            state = QiVariable()
            PlayReadout(q[0], QiPulse(400e-9, frequency=60e6))
            Recording(q[0], 400e-9, 280e-9, save_to=state)
            Wait(q[0], 2e-6)

        self.assertIn(state, job.commands[1]._associated_variable_set)

    def test_qipulse_with_qicell_property(self):
        # from issue #209
        test_sample = QiSample(1)
        test_sample[0]["pulse"] = 200e-9

        with QiJob() as job:
            q = QiCells(1)
            Play(q[0], QiPulse(q[0]["pulse"], frequency=60e6))
            Play(q[0], QiPulse(100e-9, frequency=60e6))
        job.print_assembler(test_sample)

        instructions = job.cell_seq_dict[q[0]].instruction_list

        self.assertIsInstance(instructions[1], SeqTrigger)
        self.assertEqual(instructions[1]._trig_indices[2], 1)

        self.assertIsInstance(instructions[3], SeqTrigger)
        self.assertEqual(instructions[3]._trig_indices[2], 2)


class QiRecordingOrderTest(unittest.TestCase):
    def test_single_loop(self):
        with QiJob() as job:
            cells = QiCells(1)
            a = QiVariable(name="a")
            with ForRange(a, 0, 10):
                Recording(cells[0], 20e-9, save_to="result_a")

        x = job._simulate_recordings()[cells[0]]
        x = list(map(lambda x: x.save_to, x))

        self.assertEqual(x, ["result_a"] * 10)

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
        x = list(map(lambda x: x.save_to, x))

        expected = []
        for a in range(0, 10):
            expected.append("result_a")
            for b in range(0, 10):
                expected.append("result_b")

        self.assertEqual(x, expected)

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
        x = list(map(lambda x: x.save_to, x))

        expected = []
        for a in range(0, 10):
            expected.append("result_a")
            for b in range(0, a):
                expected.append("result_b")

        self.assertEqual(x, expected)

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
        x = list(map(lambda x: x.save_to, x))

        expected = []
        for a in range(0, 10):
            expected.append("result_a")
            for b in range(0, 10):
                expected.append("result_b")
            expected.append("result_d")
            for b in range(0, 10):
                expected.append("result_c")

        self.assertEqual(x, expected)

    # If we want to support recording in ifs we should add them to the simulation.
    def test_single_recording_in_program_with_if(self):
        with QiJob() as job:
            cells = QiCells(1)
            a = QiVariable(name="a")
            with If(a == 2):
                Recording(cells[0], 20e-9, save_to="result_a")

        with self.assertRaisesRegex(
            RuntimeError, "Recording command within If-Else statement"
        ):
            job._simulate_recordings()[cells[0]]

    def test_multiple_cells2(self):
        with QiJob() as job:
            cells = QiCells(2)
            a = QiVariable(name="a")
            b = QiVariable(name="a")
            with ForRange(a, 0, 10):
                Recording(cells[0], 20e-9, save_to="result_a")
                Recording(cells[1], 20e-9, save_to="result_b")

        job._build_program()

        given_order_0 = list(map(lambda x: x.name, cells[0]._result_recording_order))
        given_order_1 = list(map(lambda x: x.name, cells[1]._result_recording_order))

        expected_cell_0 = []
        expected_cell_1 = []
        for i in range(0, 10):
            expected_cell_0.append("result_a")
            expected_cell_1.append("result_b")

        self.assertEqual(given_order_0, expected_cell_0)
        self.assertEqual(given_order_1, expected_cell_1)

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

        given_order_0 = list(map(lambda x: x.name, cells[0]._result_recording_order))
        given_order_1 = list(map(lambda x: x.name, cells[1]._result_recording_order))
        given_order_2 = list(map(lambda x: x.name, cells[2]._result_recording_order))

        expected_cell_0 = []
        expected_cell_1 = []
        expected_cell_2 = []
        for i in range(0, 10):
            expected_cell_0.append("result_a")
            for _ in range(0, i):
                expected_cell_1.append("result_b")
        expected_cell_2.append("result_c")

        self.assertEqual(given_order_0, expected_cell_0)
        self.assertEqual(given_order_1, expected_cell_1)
        self.assertEqual(given_order_2, expected_cell_2)

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

        given_order = list(map(lambda x: x.name, q[0]._result_recording_order))

        self.assertEqual(given_order, ["result_a"] * 3 + ["result_b"] * 3)

    def test_float_step(self):
        with QiJob() as calib_offset:
            q = QiCells(1)
            offset = QiVariable()
            with ForRange(offset, 0, 1024e-9, 4e-9):
                PlayReadout(q[0], QiPulse(400e-9, frequency=60e6))
                Recording(q[0], 400e-9, offset, save_to="result")
                Wait(q[0], 2e-6)
        calib_offset._build_program()
        self.assertEqual(calib_offset.cells[0].get_number_of_recordings(), 256)
