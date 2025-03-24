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
This module contains the type infrastructure and error reporting logic.

The basic typechecking idea is described in the documentation for `_TypeConstraint`
"""

from __future__ import annotations

import warnings
from abc import abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

from qiclib.packages.constants import CONTROLLER_CYCLE_TIME

from .qi_visitor import QiJobVisitor

if TYPE_CHECKING:
    from .qi_command import ForRangeCommand
    from .qi_var_definitions import QiExpression, QiOp, QiOpCond


class QiType(Enum):
    """The type that a :class:`~qiclib.code.qi_var_definitions.QiExpression` has."""

    UNKNOWN = 0
    TIME = 1
    """Time values contain some amount of times (in cycles) that, for example, can be used in wait commands.
    They are specified using float (seconds) and are converted to cycles automatically.
    """
    STATE = 2
    """State values are the result of a recording."""
    NORMAL = 3
    """Freely usable integer values."""
    FREQUENCY = 4
    """
    Frequency values can be used in the Play/PlayReadout commands and, like TIME, are specified using floats.
    """
    PHASE = 5

    AMPLITUDE = 6


class _TypeConstraintReason:
    pass


class _TypeConstraintReasonQiCalc(_TypeConstraintReason):
    def __init__(self, op: QiOp, result: QiExpression):
        self.op = op
        self.result = result


class _TypeConstraintReasonQiCondition(_TypeConstraintReason):
    def __init__(self, op: QiOpCond):
        self.op = op


class _TypeConstraintReasonQiCommand(_TypeConstraintReason):
    def __init__(self, command):
        self.command = command


class _IllegalTypeReason(Enum):
    ASSIGN = 0
    FOR_RANGE = 1
    INVALID_STATE_CONSTANT = 2
    INVALID_NORMAL_CONSTANT = 3

    def to_error_message(self) -> str:
        return {
            _IllegalTypeReason.ASSIGN: "assign commands can not assign STATE variables",
            _IllegalTypeReason.FOR_RANGE: "ForRanges can only iterate over TIME or NORMAL values",
            _IllegalTypeReason.INVALID_STATE_CONSTANT: "constant values which are neither 0 or 1 can only have type TIME or NORMAL",
            _IllegalTypeReason.INVALID_NORMAL_CONSTANT: "constant float values can not be of type NORMAL",
        }[self]


class _TypeFact:
    @abstractmethod
    def to_error_message(self) -> str:
        raise NotImplementedError(
            f"{self.__class__} has not implemented `to_error_message`. This is a bug."
        )


class _TypeDefiningUse(_TypeFact, Enum):
    VARIABLE_DEFINITION = 0
    VALUE_DEFINITION = 1
    SHIFT_EXPRESSION = 2
    PULSE_LENGTH = 3
    RECORDING_SAVE_TO = 4
    WAIT_COMMAND = 5
    RECORDING_OFFSET_EXPRESSION = 6
    PULSE_FREQUENCY = 7
    PULSE_PHASE = 8
    PULSE_AMPLITUDE = 9

    def to_error_message(self) -> str:
        return {
            _TypeDefiningUse.VARIABLE_DEFINITION: "has been defined by the user as this type",
            _TypeDefiningUse.VALUE_DEFINITION: "has been defined by the user as this type",
            _TypeDefiningUse.SHIFT_EXPRESSION: "is used as right hand side of shift expression",
            _TypeDefiningUse.PULSE_LENGTH: "is used as length of pulse",
            _TypeDefiningUse.RECORDING_SAVE_TO: "is used as save_to of recording command",
            _TypeDefiningUse.WAIT_COMMAND: "is used as length in wait command",
            _TypeDefiningUse.RECORDING_OFFSET_EXPRESSION: "is used as an recording offset",
            _TypeDefiningUse.PULSE_FREQUENCY: "is used as pulse frequency.",
            _TypeDefiningUse.PULSE_PHASE: "is used as pulse phase.",
            _TypeDefiningUse.PULSE_AMPLITUDE: "is used as pulse amplitude.",
        }[self]


class _TypeFallback(_TypeFact, Enum):
    FLOAT = 1
    INT = 2

    def to_error_message(self) -> str:
        end = {
            _TypeFallback.INT: "NORMAL.",
            _TypeFallback.FLOAT: "TIME",
        }[self]
        return "had no type inferred and therefore fell back to type " + end


class _TypeConstraint(_TypeFact):
    """A type constraint represents an implication.
    If a (or multiple) QiExpression has a certain QiType, then a different QiExpression must have the specified type.
    Using this construct we formulate all typing rules in qicode.
    For example we can express that two expressions A and B must have the same type, by specifying that for all (four) types T:
    1. If A has type T then B has to have type T.
    2. If B has type T then A has to have type T.

    Equality constraints alone are not sufficient to express all typing rules (for example those of multiplication)
    which is why we use the implication as the primitive constraint.

    When we learn about the type of an expression (for example if it is specified or used in a command which requires a certain type.)
    We can check all implications which have this expression in their condition, see if they are satisfied and if so apply the conclusion
    of the implication, thereby propagating our newly learned information.
    """

    def __init__(
        self,
        condition: list[tuple[QiExpression, QiType]],
        conclusion: tuple[QiExpression, QiType],
        reason: _TypeConstraintReason,
    ):
        self.condition = condition
        self.conclusion = conclusion
        self.reason = reason

    def is_condition_satisified(self) -> bool:
        for var, type in self.condition:
            if var.type != type:
                return False
        return True

    def try_apply(self):
        """Checks if the type constraint is satisifed and if so, will apply the conclusion recursively."""
        if self.is_condition_satisified():
            self.conclusion[0]._type_info.set_type(self.conclusion[1], self)

    def to_error_message(self) -> str:
        if isinstance(self.reason, _TypeConstraintReasonQiCalc):
            from .qi_var_definitions import QiOp

            if self.reason.op in [
                QiOp.PLUS,
                QiOp.MINUS,
                QiOp.AND,
                QiOp.OR,
                QiOp.XOR,
                QiOp.LSH,
                QiOp.RSH,
                QiOp.NOT,
            ]:
                cond = self.condition[0]

                return (
                    f"is used in {self.reason.op} calculation of type {self.reason.result.type}\n"
                    + f"(because {cond[0]} {cond[0]._type_info.type_reason.to_error_message()})"
                )

            elif self.reason.op == QiOp.MULT:
                msg = (
                    f"{self.condition[0][0]} has type {self.condition[0][1]}\n"
                    + f"(because it {self.condition[0][0]._type_info.type_reason.to_error_message()})"
                )

                for _ in self.condition[1:]:
                    msg += (
                        f"\nand {self.condition[1][0]} has type {self.condition[1][1]}\n"
                        + f"(because it {self.condition[1][0]._type_info.type_reason.to_error_message()})"
                    )

                return (
                    f"is used in {self.reason.op} calculation of type {self.reason.result.type}\n"
                    + f"(because {msg})"
                )
            else:
                raise AssertionError(
                    f"Unknown operation ({self.reason.op}, type ({type(self.reason.op)})"
                )

        elif isinstance(self.reason, _TypeConstraintReasonQiCondition):
            assert len(self.condition) == 1
            cond = self.condition[0]
            return (
                f"is compared with {cond[0]} with type {cond[1]}\n"
                + f"(because {cond[0]} {cond[0]._type_info.type_reason.to_error_message()})"
            )

        elif isinstance(self.reason, _TypeConstraintReasonQiCommand):
            from .qi_command import AssignCommand, ForRangeCommand

            cmd = self.reason.command

            assert len(self.condition) == 1
            cond = self.condition[0]

            if cmd == AssignCommand:
                return (
                    f"is used in Assign command with type {cond[1]}\n"
                    + f"(because {cond[0]} {cond[0]._type_info.type_reason.to_error_message()})"
                )

            elif cmd == ForRangeCommand:
                return (
                    f"is used in ForRange over type {cond[1]}\n"
                    + f"(because {cond[0]} {cond[0]._type_info.type_reason.to_error_message()})"
                )

            else:
                assert False, f"Unexpected command {self.reason.command}."

        else:
            raise AssertionError(
                f"reason ({self.reason}, type {type(self.reason)}) is not a type constraint reason"
            )


class _TypeInformation:
    def __init__(self, expr: QiExpression):
        self.expression = expr
        self.type = QiType.UNKNOWN
        self.type_reason: _TypeFact = None

        self.constraints: list[_TypeConstraint] = []
        self.illegal_types: dict[QiType, _IllegalTypeReason] = {}

    def add_constraint(self, constraint: _TypeConstraint):
        """Adds a type constraint to this expression.
        If this expression already has a type it will try to apply it immediately."""
        if self.type == QiType.UNKNOWN:
            self.constraints.append(constraint)
        else:
            constraint.try_apply()

    def _report_illegal_type_error(
        self,
        type: QiType,
        reason: _TypeFact,
        illegal_reason: _IllegalTypeReason,
    ):
        raise TypeError(
            f"{self.expression} can not have {type}\n"
            + f"(because {illegal_reason.to_error_message()})\n"
            + "but the type is required.\n"
            + f"(because it {reason.to_error_message()})"
        )

    def set_type(self, type: QiType, reason: _TypeFact):
        """Sets the type of this QiExpression.
        If the new type contradicts the current one it will throw a type error.
        If the type was previously UNKNOWN it will apply all satisfied constraints.
        """
        if type in self.illegal_types:
            self._report_illegal_type_error(type, reason, self.illegal_types[type])

        if self.type == QiType.UNKNOWN:
            self.type = type
            self.type_reason = reason

            for constraint in self.constraints:
                constraint.try_apply()
        elif self.type != type:
            raise TypeError(
                f"{self.expression} was of type {self.type}\n"
                + f"(because it {self.type_reason.to_error_message()})\n"
                + f"but is also used as type {type}\n"
                + f"(because it {reason.to_error_message()})"
            )

    def add_illegal_type(self, type: QiType, reason: _IllegalTypeReason):
        """Add type that this expression can not have a certain type.
        If this expression is given such a type it will throw a type error.
        """
        if self.type == type:
            self._report_illegal_type_error(type, self.type_reason, reason)
        self.illegal_types[type] = reason


def add_qi_calc_constraints(
    op: QiOp, lhs: QiExpression, rhs: QiExpression | None, res: QiExpression
):
    """Adds type constraints for a qicalc operation to the corresponding expressions."""

    from .qi_var_definitions import QiOp

    reason = _TypeConstraintReasonQiCalc(op, res)

    if op == QiOp.NOT:
        assert rhs is None
        _add_equal_constraints(QiType.NORMAL, reason, lhs, res)
        _add_equal_constraints(QiType.STATE, reason, lhs, res)
        return

    if op in [QiOp.PLUS, QiOp.MINUS, QiOp.AND, QiOp.OR, QiOp.XOR]:
        _add_equal_constraints(QiType.NORMAL, reason, rhs, lhs, res)

    if op in [QiOp.AND, QiOp.OR, QiOp.XOR]:
        _add_equal_constraints(QiType.STATE, reason, rhs, lhs, res)

    if op == QiOp.PLUS:
        _add_equal_constraints(QiType.TIME, reason, rhs, lhs, res)
        _add_equal_constraints(QiType.FREQUENCY, reason, rhs, lhs, res)
        _add_equal_constraints(QiType.PHASE, reason, rhs, lhs, res)
        _add_equal_constraints(QiType.AMPLITUDE, reason, rhs, lhs, res)

    if op == QiOp.MULT:
        _add_scalar_multiplication_rules(QiType.TIME, lhs, rhs, res, reason)
        _add_scalar_multiplication_rules(QiType.FREQUENCY, lhs, rhs, res, reason)
        _add_scalar_multiplication_rules(QiType.PHASE, lhs, rhs, res, reason)
        _add_scalar_multiplication_rules(QiType.AMPLITUDE, lhs, rhs, res, reason)

    if op in [QiOp.LSH, QiOp.RSH]:
        rhs._type_info.set_type(QiType.NORMAL, _TypeDefiningUse.SHIFT_EXPRESSION)

        _add_equal_constraints(QiType.NORMAL, reason, lhs, res)
        _add_equal_constraints(QiType.TIME, reason, lhs, res)
        _add_equal_constraints(QiType.FREQUENCY, reason, lhs, res)
        _add_equal_constraints(QiType.PHASE, reason, lhs, res)
        _add_equal_constraints(QiType.AMPLITUDE, reason, lhs, res)


def _add_scalar_multiplication_rules(
    type: QiType,
    lhs: QiExpression,
    rhs: QiExpression,
    res: QiExpression,
    reason: _TypeConstraintReason,
):
    _add_implies_constraint([(lhs, type)], (rhs, QiType.NORMAL), reason)
    _add_implies_constraint([(lhs, type)], (res, type), reason)

    _add_implies_constraint([(rhs, type)], (lhs, QiType.NORMAL), reason)
    _add_implies_constraint([(rhs, type)], (res, type), reason)

    _add_implies_constraint(
        [(rhs, QiType.NORMAL), (lhs, QiType.NORMAL)], (res, QiType.NORMAL), reason
    )
    _add_implies_constraint([(res, type), (lhs, QiType.NORMAL)], (rhs, type), reason)
    _add_implies_constraint([(res, type), (rhs, QiType.NORMAL)], (lhs, type), reason)
    _add_implies_constraint([(res, QiType.NORMAL)], (lhs, QiType.NORMAL), reason)
    _add_implies_constraint([(res, QiType.NORMAL)], (rhs, QiType.NORMAL), reason)


def add_qi_condition_constraints(op: QiOpCond, lhs: QiExpression, rhs: QiExpression):
    """Adds type constraints for a qicondition to the corresponding expressions."""
    from .qi_var_definitions import QiOpCond

    reason = _TypeConstraintReasonQiCondition(op)

    _add_equal_constraints(QiType.NORMAL, reason, lhs, rhs)
    _add_equal_constraints(QiType.TIME, reason, lhs, rhs)

    if op in [QiOpCond.EQ, QiOpCond.NE]:
        _add_equal_constraints(QiType.STATE, reason, lhs, rhs)


def _add_equal_constraints(
    type: QiType, reason: _TypeConstraintReason, *expressions: QiExpression
):
    """Helper function to add equality constraints."""
    assert len(expressions) > 1

    prev = expressions[-1]
    for next in expressions:
        prev._type_info.add_constraint(
            _TypeConstraint([(prev, type)], (next, type), reason)
        )
        prev = next


def _add_implies_constraint(
    condition: list[tuple[QiExpression, QiType]],
    conclusion: tuple[QiExpression, QiType],
    reason: _TypeConstraintReason,
):
    """Simple helper function to add constraints to all necessary QiExpressions."""

    for var, _ in condition:
        var._type_info.add_constraint(_TypeConstraint(condition, conclusion, reason))


class QiTypeFallbackVisitor(QiJobVisitor):
    """Sets the fallback type to NORMAL for _QiConstValue if they weren't given a type during QiJob construction.
    This is important for qicode like the following:

    .. code-block:: python

        with ForRange(x, 0, 10, 1):
            ...

    Here, x could theoretically be either of type TIME or NORMAL because int literals can have either type.
    However, we want this code to compile to with integer semantics which is why we need this visitor to run
    after job construction. (see QiJob __exit__ method).
    """

    def visit_for_range(self, for_range_cm: ForRangeCommand):
        if for_range_cm.var.type == QiType.UNKNOWN:
            for_range_cm.var._type_info.set_type(QiType.NORMAL, _TypeFallback.INT)

        super().visit_for_range(for_range_cm)

    def visit_constant(self, const):
        if const.type == QiType.UNKNOWN:
            if isinstance(const._given_value, float):
                const._type_info.set_type(QiType.TIME, _TypeFallback.FLOAT)
            else:
                assert isinstance(const._given_value, int)
                const._type_info.set_type(QiType.NORMAL, _TypeFallback.INT)


class QiPostTypecheckVisitor(QiJobVisitor):
    """Checks that every variable has an assigned type.
    The start and end values of ForRanges over time values are converted to cycles, because we only know with
    certainty whether they iterate over NORMAL or TIME values after the QiTypeFallbackVisitor has run.
    """

    def visit_for_range(self, for_range_cm: ForRangeCommand):
        from .qi_var_definitions import _QiConstValue

        for_range_cm.var.accept(self)
        for_range_cm.start.accept(self)
        for_range_cm.end.accept(self)

        super().visit_for_range(for_range_cm)

        if for_range_cm.var.type == QiType.TIME:
            if isinstance(for_range_cm.start, _QiConstValue):
                if for_range_cm.start.value < 0:
                    raise RuntimeError(
                        f"ForRange with negative time value ({for_range_cm.start._given_value}) are not allowed"
                    )

                if for_range_cm.end.value == 0:
                    warnings.warn("End value of 0 will not be included in ForRange.")

            # round to 11 decimals, if result is CONTROLLER_CYCLE_TIME then float modulo probably failed
            if (
                round(
                    abs(for_range_cm.step._given_value) % CONTROLLER_CYCLE_TIME,
                    11,
                )
                != 0
                and round(
                    abs(for_range_cm.step._given_value) % CONTROLLER_CYCLE_TIME,
                    11,
                )
                != CONTROLLER_CYCLE_TIME
            ):
                raise RuntimeError(
                    f"When using QiTimeVariables define step size as multiple of {CONTROLLER_CYCLE_TIME*1e9:.3g} ns."
                    f" (It is currently off by {(for_range_cm.step._given_value % CONTROLLER_CYCLE_TIME)*1e9:.3g} ns.)"
                )
        elif (
            for_range_cm.var.type == QiType.FREQUENCY
            and isinstance(for_range_cm.end, _QiConstValue)
            and for_range_cm.end.value == 0
        ):
            warnings.warn("End value of 0 will not be included in ForRange.")

    def visit_assign_command(self, assign_cmd):
        assign_cmd.var.accept(self)
        super().visit_assign_command(assign_cmd)

    def visit_constant(self, const):
        if const.type == QiType.UNKNOWN:
            raise TypeError(f"Could not infer type of {const}.")

    def visit_variable(self, var):
        if var.type == QiType.UNKNOWN:
            raise TypeError(f"Could not infer type of {var}.")

    def visit_calc(self, calc):
        super().visit_calc(calc)
        if calc.type == QiType.UNKNOWN:
            raise TypeError(f"Could not infer type of {calc}.")

    def visit_cell_property(self, cell_prop):
        if cell_prop.type == QiType.UNKNOWN:
            raise TypeError(f"Could not infer type of {cell_prop}")
