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
import qiclib.code.qi_visitor as qv
from qiclib.code.qi_pulse import QiPulse
from qiclib.code.qi_jobs import (
    QiSample,
    QiVariable,
    Play,
    PlayReadout,
    QiJob,
    Recording,
    Wait,
    Assign,
    If,
    ForRange,
    Parallel,
    QiCells,
)
from qiclib.code.qi_jobs import cQiAssign


class VariableAssignmentTestCase(unittest.TestCase):
    def setUp(self):
        with QiJob() as self.job:
            self.q = QiCells(4)
            self.x = QiVariable(int)
            self.y = QiVariable(int)
            self.z = QiVariable(int)

            self.y_time = QiVariable()

            Assign(self.x, 2)
            Assign(self.y, 1)
            Assign(self.z, self.x + self.y)

            Assign(self.y_time, self.y * 4e-9)

            with If(self.x > self.z) as self.if_test:
                Play(self.q[0], QiPulse(length=self.y_time))
                Wait(self.q[1], delay=50e-9)

                with Parallel() as self.parallel_test:
                    Play(self.q[0], QiPulse(length=30e-9))
                    PlayReadout(self.q[0], QiPulse(length=30e-9))

            Play(self.q[2], QiPulse(length=self.y_time))

        with QiJob() as self.job2:
            self.p = QiCells(4)
            self.v = QiVariable()

            Assign(self.v, 8e-9)

            Wait(self.p[0], self.v)

    def assign_cell_to_CM(self, commands):
        contained_cells_visitor = qv.QiCMContainedCellVisitor()
        for command in commands:
            command.accept(contained_cells_visitor)

    def assign_variables_to_cell(self, commands):
        cell_to_variable_visitor = qv.QiCmdVariableInspection()
        for command in reversed(commands):
            command.accept(cell_to_variable_visitor)

    def test_contained_variables(self):
        # test if context managers recognize used cells inside their body
        self.assign_cell_to_CM(self.job.commands)

        self.assertIn(self.q[0], self.if_test._relevant_cells)
        self.assertIn(self.q[1], self.if_test._relevant_cells)

        self.assertNotIn(self.q[2], self.if_test._relevant_cells)
        self.assertNotIn(self.q[3], self.if_test._relevant_cells)

        self.assertIn(self.q[0], self.parallel_test._relevant_cells)
        self.assertNotIn(self.q[1], self.parallel_test._relevant_cells)

    def test_relevant_variables_If(self):
        # test if context managers recognize used QiVariables
        self.assign_cell_to_CM(self.job.commands)

        self.assertTrue(self.if_test.is_variable_relevant(self.x))
        self.assertFalse(self.if_test.is_variable_relevant(self.y))
        self.assertTrue(self.if_test.is_variable_relevant(self.z))

    def test_relevant_variables_Assign(self):
        # variable is relevant only if it is needed for the calculation; so the assigned variable is not relevant
        test_assign = cQiAssign(self.z, self.x + self.y)

        self.assertTrue(test_assign.is_variable_relevant(self.x))
        self.assertTrue(test_assign.is_variable_relevant(self.y))
        self.assertFalse(test_assign.is_variable_relevant(self.z))

    def test_assign_variables_to_cell_simple(self):
        # Test if QiVariables are only allocated to relevant cells
        self.assign_variables_to_cell(self.job2.commands)

        self.assertIn(self.p[0], self.v._relevant_cells)
        self.assertNotIn(self.p[1], self.v._relevant_cells)
        self.assertNotIn(self.p[2], self.v._relevant_cells)
        self.assertNotIn(self.p[3], self.v._relevant_cells)

        # The other way round as well
        self.assertIn(self.v, self.p[0]._relevant_vars)
        self.assertNotIn(self.v, self.p[1]._relevant_vars)
        self.assertNotIn(self.v, self.p[2]._relevant_vars)
        self.assertNotIn(self.v, self.p[3]._relevant_vars)

    def test_assign_variables_to_cell(self):
        # Test if QiVariables are only allocated to relevant cells
        self.assign_cell_to_CM(self.job.commands)
        self.assign_variables_to_cell(self.job.commands)

        self.assertIn(self.q[0], self.x._relevant_cells)
        self.assertIn(self.q[1], self.x._relevant_cells)
        self.assertNotIn(self.q[2], self.x._relevant_cells)
        self.assertNotIn(self.q[3], self.x._relevant_cells)

        self.assertIn(self.q[0], self.y._relevant_cells)
        self.assertIn(self.q[1], self.y._relevant_cells)
        self.assertIn(self.q[2], self.y._relevant_cells)
        self.assertNotIn(self.q[3], self.y._relevant_cells)

        self.assertIn(self.q[0], self.z._relevant_cells)
        self.assertIn(self.q[1], self.z._relevant_cells)
        self.assertNotIn(self.q[2], self.z._relevant_cells)
        self.assertNotIn(self.q[3], self.z._relevant_cells)

        # The other way round as well
        self.assertIn(self.x, self.q[0]._relevant_vars)
        self.assertIn(self.x, self.q[1]._relevant_vars)
        self.assertNotIn(self.x, self.q[2]._relevant_vars)
        self.assertNotIn(self.x, self.q[3]._relevant_vars)

        self.assertIn(self.y, self.q[0]._relevant_vars)
        self.assertIn(self.y, self.q[1]._relevant_vars)
        self.assertIn(self.y, self.q[2]._relevant_vars)
        self.assertNotIn(self.y, self.q[3]._relevant_vars)

        self.assertIn(self.z, self.q[0]._relevant_vars)
        self.assertIn(self.z, self.q[1]._relevant_vars)
        self.assertNotIn(self.z, self.q[2]._relevant_vars)
        self.assertNotIn(self.z, self.q[3]._relevant_vars)

    def test_assign_variables_if_assign(self):
        with QiJob() as assign_test:
            q = QiCells(1)
            var1 = QiVariable(int)
            var2 = QiVariable(int)

            with If(var2 == 0) as if_test:
                Assign(var1, 2)
            with ForRange(var2, 5, var1, -1) as for_test:
                Wait(q[0], 24e-9)

        self.assign_cell_to_CM(assign_test.commands)
        self.assign_variables_to_cell(assign_test.commands)
        self.assign_cell_to_CM(assign_test.commands)

        self.assertIn(q[0], if_test._relevant_cells)


class RecordingLengthTest(unittest.TestCase):
    def test_length_OK(self):
        try:
            with QiJob() as rec_test:
                q = QiCells(2)
                var1 = QiVariable(int)
                with If(var1 == 1):
                    with Parallel():
                        Recording(q[0], 13e-9, 12e-9)
                    with Parallel():
                        PlayReadout(q[0], QiPulse(50e-9))
                        Recording(q[0], 13e-9, 12e-9)

                Recording(q[1], 42e-9, 43e-9)

        except Exception as e:
            self.fail("test_length_OK raised exception " + str(e))

        rec_test._run_analyses()

        self.assertEqual(rec_test.cells[0].recording_length, 13e-9)
        self.assertEqual(rec_test.cells[0].initial_recording_offset, 12e-9)

        self.assertEqual(rec_test.cells[1].recording_length, 42e-9)
        self.assertEqual(rec_test.cells[1].initial_recording_offset, 43e-9)

    def test_length_properties_OK(self):
        try:
            with QiJob() as rec_test:
                q = QiCells(2)
                var1 = QiVariable(int)
                with If(var1 == 1):
                    with Parallel():
                        Recording(q[0], q[0]["rec"], q[0]["offset"])
                    with Parallel():
                        PlayReadout(q[0], QiPulse(50e-9))
                        Recording(q[0], q[0]["rec"], q[0]["offset"])

                Recording(q[1], q[1]["rec"], q[1]["offset"])

        except Exception as e:
            self.fail("test_length_properties_OK raised exception " + str(e))

        sample = QiSample(2)
        sample[0]["rec"] = 42e-9
        sample[0]["offset"] = 43e-9
        sample[1]["rec"] = 44e-9
        sample[1]["offset"] = 45e-9

        rec_test._resolve_properties(sample)

        rec_test._run_analyses()

        self.assertEqual(rec_test.cells[0].recording_length, 42e-9)
        self.assertEqual(rec_test.cells[0].initial_recording_offset, 43e-9)

        self.assertEqual(rec_test.cells[1].recording_length, 44e-9)
        self.assertEqual(rec_test.cells[1].initial_recording_offset, 45e-9)

    def test_length_properties_Error(self):
        with self.assertRaisesRegex(
            RuntimeError, r"Cell \d+: Multiple definitions of recording length used\."
        ):
            with QiJob() as rec_test:
                q = QiCells(1)
                var1 = QiVariable(int)
                with If(var1 == 1):
                    with Parallel():
                        Recording(q[0], q[0]["rec1"], q[0]["offset"])
                    with Parallel():
                        PlayReadout(q[0], QiPulse(50e-9))
                        Recording(q[0], q[0]["rec2"], q[0]["offset"])

    def test_length_Error(self):
        with self.assertRaisesRegex(
            RuntimeError, r"Cell \d+: Multiple definitions of recording length used\."
        ):
            with QiJob() as rec_test:
                q = QiCells(1)
                var1 = QiVariable(int)
                with If(var1 == 1):
                    with Parallel():
                        Recording(q[0], 13e-9, 12e-9)
                    with Parallel():
                        PlayReadout(q[0], QiPulse(50e-9))
                        Recording(q[0], 130e-9, 12e-9)

    def test_offset_Error(self):
        with QiJob() as rec_test:
            q = QiCells(1)
            var1 = QiVariable(int)
            with If(var1 == 1):
                with Parallel():
                    Recording(q[0], 13e-9, 12e-9)
                with Parallel():
                    PlayReadout(q[0], QiPulse(50e-9))
                    Recording(q[0], 13e-9, 120e-9)

        with self.assertRaisesRegex(
            RuntimeError,
            "Parallel Blocks with multiple Recording instructions with different offsets are not supported.",
        ):
            rec_test._run_analyses()
