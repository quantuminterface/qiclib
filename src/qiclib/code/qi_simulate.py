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

"""
Some analysis require us to simulate a qicode program.
Currently, this is only used to figure out the order of recording commands.
"""

# (In the future we might want to create a real simulator with support for more complex programs)
from __future__ import annotations

from typing import Any

from qiclib.code.qi_command import (
    AssignCommand,
    DeclareCommand,
    ForRangeCommand,
    ParallelCommand,
    PlayReadoutCommand,
    RecordingCommand,
)
from qiclib.code.qi_jobs import (
    QiCell,
    QiCommand,
)
from qiclib.code.qi_var_definitions import (
    QiCellProperty,
    QiExpression,
    QiOp,
    _QiCalcBase,
    _QiConstValue,
    _QiVariableBase,
)
from qiclib.packages.constants import RECORDING_MAX_RAW_SAMPLES


def to32bit(x):
    """Convert an arbitrary signed value to the 32bit signed range of a register"""
    return divmod(x + 2**31, 2**32)[1] - 2**31


# (In the future we might want to create a real simulator with support for more complex programs)
class Simulator:
    """
    Simulate a qicode program.
    Currently, this is only used to determine the execution order of recording commands.
    See :meth:`qiclib.code._simulate_recordings`
    """

    def __init__(self, cells: list[QiCell]):
        # Current state of loop variables
        self.variables: dict[_QiVariableBase, Any] = {}

        # The order of recordings for a cell
        self.cell_recordings: dict[QiCell, list[RecordingCommand]] = {}
        for cell in cells:
            self.cell_recordings[cell] = []

    class Unassigned:
        pass

    def _eval(self, expr: QiExpression) -> int:
        if isinstance(expr, (_QiConstValue, QiCellProperty)):
            return expr.value
        elif isinstance(expr, _QiVariableBase):
            return self.variables[expr]
        elif isinstance(expr, _QiCalcBase):
            if expr.op == QiOp.NOT:
                return ~self._eval(expr.val1)

            v1 = self._eval(expr.val1)
            v2 = self._eval(expr.val2)

            if expr.op == QiOp.PLUS:
                return to32bit(v1 + v2)
            elif expr.op == QiOp.MINUS:
                return to32bit(v1 - v2)
            elif expr.op == QiOp.MULT:
                return to32bit(v1 * v2)
            elif expr.op == QiOp.LSH:
                return to32bit(v1 >> v2)
            elif expr.op == QiOp.RSH:
                return to32bit(v1 << v2)
            elif expr.op == QiOp.AND:
                return to32bit(v1 & v2)
            elif expr.op == QiOp.OR:
                return to32bit(v1 | v2)
            elif expr.op == QiOp.XOR:
                return to32bit(v1 ^ v2)
            else:
                raise AssertionError("Unexpected QiOp")
        else:
            raise AssertionError("Unknown QiExpression type")

    def _simulate(self, commands: list[QiCommand]):
        for cmd in commands:
            if isinstance(cmd, PlayReadoutCommand) and cmd.recording is not None:
                cmd = cmd.recording

            if isinstance(cmd, RecordingCommand):
                if len(self.cell_recordings[cmd.cell]) >= RECORDING_MAX_RAW_SAMPLES:
                    raise RuntimeError(
                        f"More than {RECORDING_MAX_RAW_SAMPLES} recordings during job execution."
                    )

                self.cell_recordings[cmd.cell].append(cmd)

            elif isinstance(cmd, DeclareCommand):
                self.variables[cmd.var] = Simulator.Unassigned

            elif isinstance(cmd, AssignCommand):
                self.variables[cmd.var] = self._eval(cmd.value)

            elif isinstance(cmd, ParallelCommand):
                self._simulate(cmd.body)

            elif isinstance(cmd, ForRangeCommand):
                assert cmd.var in self.variables

                if isinstance(cmd.start, _QiVariableBase):
                    start_value = self.variables[cmd.start]
                elif isinstance(cmd.start, (_QiConstValue, QiCellProperty)):
                    start_value = cmd.start.value
                else:
                    raise AssertionError("unreacheable")

                if isinstance(cmd.end, _QiVariableBase):
                    end_value = self.variables[cmd.end]
                elif isinstance(cmd.end, (_QiConstValue, QiCellProperty)):
                    end_value = cmd.end.value
                else:
                    raise AssertionError("unreacheable")

                assert isinstance(cmd.step, (_QiConstValue, QiCellProperty))
                step_value = cmd.step.value

                for i in range(start_value, end_value, step_value):
                    self.variables[cmd.var] = i
                    self._simulate(cmd.body)
