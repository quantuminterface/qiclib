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
import pytest

import qiclib.code.qi_visitor as qv
from qiclib.code.qi_command import AssignCommand
from qiclib.code.qi_jobs import (
    Assign,
    ForRange,
    If,
    Parallel,
    Play,
    PlayReadout,
    QiCells,
    QiJob,
    QiSample,
    QiVariable,
    Recording,
    Wait,
)
from qiclib.code.qi_pulse import QiPulse


class TestVariableAssignment:
    def assign_cell_to_CM(self, commands):
        contained_cells_visitor = qv.QiCMContainedCellVisitor()
        for command in commands:
            command.accept(contained_cells_visitor)

    def assign_variables_to_cell(self, commands):
        cell_to_variable_visitor = qv.QiCmdVariableInspection()
        for command in reversed(commands):
            command.accept(cell_to_variable_visitor)

    def test_contained_variables(self):
        with QiJob() as job:
            q = QiCells(4)
            x = QiVariable(int)
            y = QiVariable(int)
            z = QiVariable(int)

            y_time = QiVariable()

            Assign(x, 2)
            Assign(y, 1)
            Assign(z, x + y)

            Assign(y_time, y * 4e-9)

            with If(x > z) as if_test:
                Play(q[0], QiPulse(length=y_time))
                Wait(q[1], delay=50e-9)

                with Parallel() as parallel_test:
                    Play(q[0], QiPulse(length=30e-9))
                    PlayReadout(q[0], QiPulse(length=30e-9))

            Play(q[2], QiPulse(length=y_time))

        # test if context managers recognize used cells inside their body
        self.assign_cell_to_CM(job.commands)

        assert job.cells[0] in if_test._relevant_cells
        assert job.cells[1] in if_test._relevant_cells

        assert job.cells[2] not in if_test._relevant_cells
        assert job.cells[3] not in if_test._relevant_cells

        assert job.cells[0] in parallel_test._relevant_cells
        assert job.cells[1] not in parallel_test._relevant_cells

        assert if_test.is_variable_relevant(x)
        assert not (if_test.is_variable_relevant(y))
        assert if_test.is_variable_relevant(z)

        # variable is relevant only if it is needed for the calculation; so the assigned variable is not relevant
        test_assign = AssignCommand(z, x + y)

        assert test_assign.is_variable_relevant(x)
        assert test_assign.is_variable_relevant(y)
        assert not (test_assign.is_variable_relevant(z))

        self.assign_variables_to_cell(job.commands)

        assert q[0] in x._relevant_cells
        assert q[1] in x._relevant_cells
        assert q[2] not in x._relevant_cells
        assert q[3] not in x._relevant_cells

        assert q[0] in y._relevant_cells
        assert q[1] in y._relevant_cells
        assert q[2] in y._relevant_cells
        assert q[3] not in y._relevant_cells

        assert q[0] in z._relevant_cells
        assert q[1] in z._relevant_cells
        assert q[2] not in z._relevant_cells
        assert q[3] not in z._relevant_cells

        # The other way round as well
        assert x in q[0]._relevant_vars
        assert x in q[1]._relevant_vars
        assert x not in q[2]._relevant_vars
        assert x not in q[3]._relevant_vars

        assert y in q[0]._relevant_vars
        assert y in q[1]._relevant_vars
        assert y in q[2]._relevant_vars
        assert y not in q[3]._relevant_vars

        assert z in q[0]._relevant_vars
        assert z in q[1]._relevant_vars
        assert z not in q[2]._relevant_vars
        assert z not in q[3]._relevant_vars

    def test_assign_variables_to_cell_simple(self):
        with QiJob() as job:
            p = QiCells(4)
            v = QiVariable()

            Assign(v, 8e-9)

            Wait(p[0], v)

        # Test if QiVariables are only allocated to relevant cells
        self.assign_variables_to_cell(job.commands)

        assert p[0] in v._relevant_cells
        assert p[1] not in v._relevant_cells
        assert p[2] not in v._relevant_cells
        assert p[3] not in v._relevant_cells

        # The other way round as well
        assert v in p[0]._relevant_vars
        assert v not in p[1]._relevant_vars
        assert v not in p[2]._relevant_vars
        assert v not in p[3]._relevant_vars

    def test_assign_variables_if_assign(self):
        with QiJob() as assign_test:
            q = QiCells(1)
            var1 = QiVariable(int)
            var2 = QiVariable(int)

            with If(var2 == 0) as if_test:
                Assign(var1, 2)
            with ForRange(var2, 5, var1, -1):
                Wait(q[0], 24e-9)

        self.assign_cell_to_CM(assign_test.commands)
        self.assign_variables_to_cell(assign_test.commands)
        self.assign_cell_to_CM(assign_test.commands)

        assert q[0] in if_test._relevant_cells


class TestRecordingLength:
    def test_length_OK(self):
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

        rec_test._run_analyses()

        assert rec_test.cells[0].recording_length == 13e-9
        assert rec_test.cells[0].initial_recording_offset == 12e-9

        assert rec_test.cells[1].recording_length == 42e-9
        assert rec_test.cells[1].initial_recording_offset == 43e-9

    def test_length_properties_OK(self):
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

        sample = QiSample(2)
        sample[0]["rec"] = 42e-9
        sample[0]["offset"] = 43e-9
        sample[1]["rec"] = 44e-9
        sample[1]["offset"] = 45e-9

        rec_test._resolve_properties(sample)

        rec_test._run_analyses()

        assert rec_test.cells[0].recording_length == 42e-9
        assert rec_test.cells[0].initial_recording_offset == 43e-9

        assert rec_test.cells[1].recording_length == 44e-9
        assert rec_test.cells[1].initial_recording_offset == 45e-9

    def test_length_properties_Error(self):
        with pytest.raises(
            RuntimeError,
            match=r"Cell \d+: Multiple definitions of recording length used\.",
        ):
            with QiJob():
                q = QiCells(1)
                var1 = QiVariable(int)
                with If(var1 == 1):
                    with Parallel():
                        Recording(q[0], q[0]["rec1"], q[0]["offset"])
                    with Parallel():
                        PlayReadout(q[0], QiPulse(50e-9))
                        Recording(q[0], q[0]["rec2"], q[0]["offset"])

    def test_length_Error(self):
        with pytest.raises(
            RuntimeError,
            match=r"Cell \d+: Multiple definitions of recording length used\.",
        ):
            with QiJob():
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

        with pytest.raises(
            RuntimeError,
            match="Parallel Blocks with multiple Recording instructions with different offsets are not supported.",
        ):
            rec_test._run_analyses()
