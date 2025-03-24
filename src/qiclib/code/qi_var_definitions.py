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
This module defines the expressions of a qicode program.
The base class of every expression is :class:`~.QiExpression`.

(The name of this module used to only be concerned with variables and is somewhat misleading nowadays)
"""

from __future__ import annotations

import itertools
from abc import abstractmethod
from collections.abc import Set
from enum import Enum

import qiclib.packages.utility as util
from qiclib.code.qi_visitor import QiExpressionVisitor

from .qi_types import QiType, _IllegalTypeReason, _TypeDefiningUse, _TypeInformation


class QiOp(Enum):
    PLUS = "+"
    MINUS = "-"
    MULT = "*"
    LSH = "<<"
    RSH = ">>"
    AND = "&"
    OR = "|"
    XOR = "^"
    NOT = "~"


class QiOpCond(Enum):
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="
    EQ = "=="
    NE = "!="

    def invert(self):
        inverted = {
            QiOpCond.EQ: QiOpCond.NE,
            QiOpCond.NE: QiOpCond.EQ,
            QiOpCond.LT: QiOpCond.GE,
            QiOpCond.LE: QiOpCond.GT,
            QiOpCond.GT: QiOpCond.LE,
            QiOpCond.GE: QiOpCond.LT,
        }
        inv = inverted.get(self)
        if inv is None:
            raise RuntimeError("Condition not found: " + str(self))
        return inv


class QiVariableSet(Set):
    """Class provides Set functionality for QiVariables.
    QiVariables overwrite comparison operations to build operation trees, to still allow comparisons ids are used.
    """

    def __init__(self) -> None:
        self._var_list: list[_QiVariableBase] = []
        self._var_id_list: list[int] = []

    def __contains__(self, x):
        return x.id in self._var_id_list

    def add(self, x: _QiVariableBase):
        if x.id not in self._var_id_list:
            self._var_id_list.append(x.id)
            self._var_list.append(x)

    def update(self, var_set):
        for var in var_set:
            self.add(var)

    def __iter__(self):
        return iter(self._var_list)

    def __len__(self):
        return len(self._var_list)


class QiExpression:
    """Superclass of every possible qicode expression."""

    def __init__(self):
        self._contained_variables = QiVariableSet()
        self._type_info = _TypeInformation(self)

    @property
    def type(self):
        return self._type_info.type

    @staticmethod
    def _from(x):
        """Creates an instance of QiExpression of the provided argument if possible."""
        if isinstance(x, (float, int)):
            return _QiConstValue(x)
        elif isinstance(x, QiExpression):
            return x
        else:
            raise RuntimeError(f"Can not create QiExpression from type {type(x)}.")

    @abstractmethod
    def accept(self, visitor: QiExpressionVisitor):
        raise NotImplementedError(
            f"{self.__class__} has not implemented `accept`. This is a bug."
        )

    @property
    def contained_variables(self):
        """Returns the variables used in this expression.
        QiExpression subclasses which contain variables (_QiCalcBase and _QiVariableBase) need to overwrite this.
        """
        raise NotImplementedError(
            f"{self.__class__} has not implemented `contained_variables`. This is a bug."
        )

    def _variables_to_container(self):
        if isinstance(self, _QiVariableBase):
            self._contained_variables.add(self)
        elif isinstance(self, _QiCalcBase):
            self._contained_variables.update(self.val1.contained_variables)
            self._contained_variables.update(self.val2.contained_variables)

    def _equal_syntax(self, other: QiExpression) -> bool:
        raise NotImplementedError(
            f"{self.__class__} has not implemented `_equal_syntax`. This is a bug."
        )

    # QiCellProperties are supposed to support some form of constant folding.
    # However, originally, instead of implementing this in an extra pass over
    # QiJob they were added to the QiCellProperty class.
    # In order to keep support for this limited form of constant folding
    # This logic was placed here.

    # (I'm not sure why we don't fold when both operands are QiCellProperty.
    # And I think the reason we don't fold tow _QiConstValue is that originally
    # They were just int/float and would "fold" implicitely when using any
    # math operator on them)

    # If anyone ever feels the need to improve this situation, I would
    # encourage them to implement a constant folding pass using the existing
    # dataflow infrastructure.
    # This pdf seems to give a nice short introduction into the topic:
    # http://openclassroom.stanford.edu/MainFolder/courses/Compilers/docs/slides/15-02-constant-propagation-annotated.pdf

    def __add__(self, x):
        x = QiExpression._from(x)
        if isinstance(self, QiCellProperty) and isinstance(x, _QiConstValue):
            return self.move_add_op_to_property(x)
        elif isinstance(self, _QiConstValue) and isinstance(x, QiCellProperty):
            return x.move_radd_op_to_property(self)
        else:
            return _QiCalcBase(self, QiOp.PLUS, x)

    def __radd__(self, x):
        x = QiExpression._from(x)
        if isinstance(self, QiCellProperty) and isinstance(x, _QiConstValue):
            return self.move_radd_op_to_property(x)
        elif isinstance(self, _QiConstValue) and isinstance(x, QiCellProperty):
            return x.move_add_op_to_property(self)
        else:
            return _QiCalcBase(x, QiOp.PLUS, self)

    def __sub__(self, x):
        x = QiExpression._from(x)
        if isinstance(self, QiCellProperty) and isinstance(x, _QiConstValue):
            return self.move_sub_op_to_property(x)
        elif isinstance(self, _QiConstValue) and isinstance(x, QiCellProperty):
            return x.move_rsub_op_to_property(self)
        else:
            return _QiCalcBase(self, QiOp.MINUS, x)

    def __rsub__(self, x):
        x = QiExpression._from(x)
        if isinstance(self, QiCellProperty) and isinstance(x, _QiConstValue):
            return self.move_rsub_op_to_property(x)
        elif isinstance(self, _QiConstValue) and isinstance(x, QiCellProperty):
            return x.move_sub_op_to_property(self)
        else:
            return _QiCalcBase(x, QiOp.MINUS, self)

    def __mul__(self, x):
        x = QiExpression._from(x)
        if isinstance(self, QiCellProperty) and isinstance(x, _QiConstValue):
            return self.move_mul_op_to_property(x)
        elif isinstance(self, _QiConstValue) and isinstance(x, QiCellProperty):
            return x.move_rmul_op_to_property(self)
        else:
            return _QiCalcBase(self, QiOp.MULT, x)

    def __rmul__(self, x):
        x = QiExpression._from(x)
        if isinstance(self, QiCellProperty) and isinstance(x, _QiConstValue):
            return self.move_rmul_op_to_property(x)
        elif isinstance(self, _QiConstValue) and isinstance(x, QiCellProperty):
            return x.move_mul_op_to_property(self)
        else:
            return _QiCalcBase(x, QiOp.MULT, self)

    def __lshift__(self, x):
        return _QiCalcBase(self, QiOp.LSH, QiExpression._from(x))

    def __rshift__(self, x):
        return _QiCalcBase(self, QiOp.RSH, QiExpression._from(x))

    def __and__(self, x):
        return _QiCalcBase(self, QiOp.AND, QiExpression._from(x))

    def __rand__(self, x):
        return _QiCalcBase(QiExpression._from(x), QiOp.AND, self)

    def __or__(self, x):
        return _QiCalcBase(self, QiOp.OR, QiExpression._from(x))

    def __ror__(self, x):
        return _QiCalcBase(QiExpression._from(x), QiOp.OR, self)

    def __xor__(self, x):
        return _QiCalcBase(self, QiOp.XOR, QiExpression._from(x))

    def __rxor__(self, x):
        return _QiCalcBase(QiExpression._from(x), QiOp.XOR, self)

    def __invert__(self):
        return _QiCalcBase(self, QiOp.NOT, None)

    def __lt__(self, x):
        return QiCondition(self, QiOpCond.LT, QiExpression._from(x))

    def __le__(self, x):
        return QiCondition(self, QiOpCond.LE, QiExpression._from(x))

    def __gt__(self, x):
        return QiCondition(self, QiOpCond.GT, QiExpression._from(x))

    def __ge__(self, x):
        return QiCondition(self, QiOpCond.GE, QiExpression._from(x))

    def __eq__(self, x):
        return QiCondition(self, QiOpCond.EQ, QiExpression._from(x))

    def __ne__(self, x):
        return QiCondition(self, QiOpCond.NE, QiExpression._from(x))


class _QiVariableBase(QiExpression):
    """Base class for QiVariables.
    Variables can be relevant to only a subset of QiCells, this subset is saved in _relevant_cells.
    Variables are simple expressions and, therefore, are typed.
    Variables can be compared by self.id."""

    id_iter = itertools.count()
    str_id_iter = itertools.count()

    def __init__(
        self,
        type: QiType,
        value: int | float | None = None,
        name=None,
    ):
        from qiclib.code.qi_jobs import QiCell

        assert isinstance(type, QiType)
        assert value is None or isinstance(value, (int, float))

        super().__init__()

        if type != QiType.UNKNOWN:
            self._type_info.set_type(type, _TypeDefiningUse.VARIABLE_DEFINITION)

        self.value = value

        self._value = value
        self._relevant_cells: set[QiCell] = set()
        self.id = next(_QiVariableBase.id_iter)
        self.str_id = next(_QiVariableBase.str_id_iter)

        self._contained_variables.add(self)

        self.name = name

    @property
    def contained_variables(self):
        return self._contained_variables

    @staticmethod
    def reset_str_id():
        _QiVariableBase.str_id_iter = itertools.count()

    def accept(self, visitor: QiExpressionVisitor):
        visitor.visit_variable(self)

    def _equal_syntax(self, other: QiExpression) -> bool:
        return isinstance(other, _QiVariableBase) and self.id == other.id

    def __hash__(self) -> int:
        return self.id

    def __str__(self) -> str:
        return f"QiVariable({self.name or ''})"


class _QiConstValue(QiExpression):
    """Represents QiExpression which are a constant (compiletime known) values.
    Integers can be used as either NORMAL, TIME or FREQUENCY values. It is up to the type inference to figure it out.
    If the value can be represented as a float value it has an additional attribute float_value which represents the value before
    it has been converted to the integer representation used by the sequencer.
    """

    def __init__(self, value: int | float):
        super().__init__()

        self._given_value = value  # Value given to the constructor. Is interpreted differently depending on the type.

        # Constant STATE values can only be 0 or 1, therefore we forbid QiType.STATE if we have a different value.
        if isinstance(self._given_value, float) or self._given_value not in [1, 0]:
            self._type_info.add_illegal_type(
                QiType.STATE,
                _IllegalTypeReason.INVALID_STATE_CONSTANT,
            )

        if isinstance(self._given_value, float):
            self._type_info.add_illegal_type(
                QiType.NORMAL, _IllegalTypeReason.INVALID_NORMAL_CONSTANT
            )

    @property
    def float_value(self):
        assert self.type in (
            QiType.TIME or self.type,
            QiType.FREQUENCY,
            QiType.PHASE,
            QiType.AMPLITUDE,
        )
        return self._given_value

    @property
    def value(self):
        """
        Integer representation of the constant value.
        Since the sequencer doesn't have a floating point unit, any calculations has to be using integers.
        In practice, this means we only perform fixpoint arithmetic and need to convert any float like value
        to such an fixpoint value.
        The correct conversion depends on the type.
        """
        if self.type in (
            QiType.NORMAL,
            QiType.STATE,
            QiType.UNKNOWN,
        ):
            return self._given_value
        elif self.type == QiType.TIME:
            return int(util.conv_time_to_cycles(self._given_value, "ceil"))
        elif self.type == QiType.PHASE:
            return int(util.conv_phase_to_nco_phase(self._given_value))
        elif self.type == QiType.AMPLITUDE:
            return int(util.conv_amplitude_to_int(self._given_value))
        else:
            assert self.type == QiType.FREQUENCY
            return util.conv_freq_to_nco_phase_inc(self._given_value)

    @property
    def contained_variables(self):
        return QiVariableSet()

    def accept(self, visitor: QiExpressionVisitor):
        visitor.visit_constant(self)

    def _equal_syntax(self, other: QiExpression) -> bool:
        assert QiType.UNKNOWN not in (self.type, other.type)
        return isinstance(other, _QiConstValue) and self.value == other.value

    def __str__(self):
        if self.type in (
            QiType.TIME,
            QiType.FREQUENCY,
            QiType.AMPLITUDE,
            QiType.PHASE,
        ):
            value = self.float_value
        elif self.type in (QiType.NORMAL, QiType.STATE, QiType.UNKNOWN):
            value = self.value
        else:
            raise RuntimeError(
                "This program point should be unreacheable. Please file a bug report."
            )
        return f"{value:g}"


class QiNormalValue(_QiConstValue):
    def __init__(self, value: int):
        super().__init__(value)
        self._type_info.set_type(QiType.NORMAL, _TypeDefiningUse.VALUE_DEFINITION)


class QiTimeValue(_QiConstValue):
    def __init__(self, value: int | float):
        super().__init__(value)
        self._type_info.set_type(QiType.TIME, _TypeDefiningUse.VALUE_DEFINITION)


class QiFrequencyValue(_QiConstValue):
    def __init__(self, value: int | float):
        super().__init__(value)
        self._type_info.set_type(QiType.FREQUENCY, _TypeDefiningUse.VALUE_DEFINITION)


class QiPhaseValue(_QiConstValue):
    def __init__(self, value: int | float):
        super().__init__(value)
        self._type_info.set_type(QiType.PHASE, _TypeDefiningUse.VALUE_DEFINITION)


class QiAmplitudeValue(_QiConstValue):
    def __init__(self, value: int | float):
        super().__init__(value)
        self._type_info.set_type(QiType.AMPLITUDE, _TypeDefiningUse.VALUE_DEFINITION)


class QiCellProperty(QiExpression):
    """When describing experiments, properties of cells might not yet be defined.Instead, a QiCellProperty object will be generated.
    This object can be used as length definition in WaitCommand and QiPulse"""

    def __init__(self, cell, name: str):
        super().__init__()
        from .qi_jobs import QiCell

        self.name = name
        self.cell: QiCell = cell
        self.operations = lambda val: val
        self.opcode = "x"

    @property
    def opcode_p(self):
        """Old opcode in parentheses for building new opcode"""
        return self.opcode if self.opcode == "x" else f"({self.opcode})"

    def resolve_equal(self, o: object) -> bool:
        if isinstance(o, QiCellProperty):
            return self.name == o.name and self.opcode == o.opcode
        elif o is None:
            return False
        try:
            return o == self()
        except KeyError:
            return False  # At time of comparison, unresolved property is not equal to o

    def __call__(self):
        value = self.cell._properties.get(self.name)

        if isinstance(value, QiCellProperty) or value is None:
            raise KeyError("Property could not be resolved")
        return self.operations(value)

    @property
    def value(self):
        if self.type == QiType.TIME:
            return util.conv_time_to_cycles(self())
        elif self.type == QiType.FREQUENCY:
            return util.conv_freq_to_nco_phase_inc(self())
        elif self.type == QiType.NORMAL:
            return self()
        elif self.type == QiType.STATE:
            return self()
        elif self.type == QiType.PHASE:
            return util.conv_phase_to_nco_phase(self())
        elif self.type == QiType.AMPLITUDE:
            return util.conv_amplitude_to_int(self())
        else:
            raise RuntimeError(
                "Missing type information to resolve value to convert to a machine value."
            )

    @property
    def float_value(self):
        assert self.type in (
            QiType.TIME,
            QiType.FREQUENCY,
            QiType.PHASE,
            QiType.AMPLITUDE,
        )
        return self()

    def accept(self, visitor: QiExpressionVisitor):
        visitor.visit_cell_property(self)

    @property
    def contained_variables(self):
        return QiVariableSet()

    def _equal_syntax(self, other: QiExpression) -> bool:
        return isinstance(other, QiCellProperty) and self.resolve_equal(other)

    def move_add_op_to_property(self, x: _QiConstValue):
        if x._given_value == 0:
            return self
        old_op = self.operations  # Necessary because of recursion otherwise
        self.operations = lambda val: old_op(val) + x.value
        self.opcode = f"{self.opcode_p} + {x}"
        return self

    def move_radd_op_to_property(self, x: _QiConstValue):
        if x._given_value == 0:
            return self
        old_op = self.operations
        self.operations = lambda val: x.value + old_op(val)
        self.opcode = f"{self.opcode_p} + {x}"
        return self

    def move_sub_op_to_property(self, x: _QiConstValue):
        if x._given_value == 0:
            return self
        old_op = self.operations
        self.operations = lambda val: old_op(val) - x.value
        self.opcode = f"{self.opcode_p} - {x}"
        return self

    def move_rsub_op_to_property(self, x: _QiConstValue):
        old_op = self.operations
        self.operations = lambda val: x.value - old_op(val)
        self.opcode = f"{x} - {self.opcode_p}"
        return self

    def move_mul_op_to_property(self, x: _QiConstValue):
        if x._given_value == 1:
            return self
        old_op = self.operations
        self.operations = lambda val: old_op(val) * x.value
        self.opcode = f"{x} * {self.opcode_p}"
        return self

    def move_rmul_op_to_property(self, x: _QiConstValue):
        if x._given_value == 1:
            return self
        old_op = self.operations
        self.operations = lambda val: x.value * old_op(val)
        self.opcode = f"{x} * {self.opcode_p}"
        return self

    # These operations are not implemented for general QiExpressions
    # and are, therefore, left as they are.

    def __truediv__(self, x):
        if (isinstance(x, _QiConstValue) and x._given_value == 1) or x == 1:
            return self
        old_op = self.operations
        self.operations = lambda val: old_op(val) / x
        self.opcode = f"{self.opcode_p} / {x}"
        return self

    def __rtruediv__(self, x):
        old_op = self.operations
        self.operations = lambda val: x / old_op(val)
        self.opcode = f"{x} / {self.opcode_p}"
        return self


class _QiCalcBase(QiExpression):
    """Represents binary and unary operations."""

    def __init__(self, val1, op, val2) -> None:
        super().__init__()

        self.val1 = val1
        self.op: QiOp = op
        self.val2 = val2

        from .qi_types import add_qi_calc_constraints

        add_qi_calc_constraints(op, val1, val2, self)

    @property
    def contained_variables(self):
        """Function traverses the operation tree to determine which QiVariables are used for the calculations.
        Found QiVariables are added to _contained_variables"""
        if len(self._contained_variables) == 0:
            self._variables_to_container()

        return self._contained_variables

    def accept(self, visitor: QiExpressionVisitor):
        visitor.visit_calc(self)

    def _equal_syntax(self, other: QiExpression) -> bool:
        return (
            isinstance(other, _QiCalcBase)
            and self.op == other.op
            and self.val1._equal_syntax(other.val1)
            and self.val2._equal_syntax(other.val2)
        )

    def __str__(self):
        return f"({self.val1} {self.op.value} {self.val2})"


class QiCondition:
    """Saves conditional comparisons.
    Can only be root node"""

    def __init__(
        self,
        val1: QiExpression,
        op: QiOpCond = QiOpCond.GT,
        val2: QiExpression = _QiConstValue(0),
    ) -> None:
        self._contained_variables = QiVariableSet()

        self.val1 = val1
        self.op = op
        self.val2 = val2

        from .qi_types import add_qi_condition_constraints

        add_qi_condition_constraints(op, val1, val2)

    @property
    def contained_variables(self):
        if len(self._contained_variables) == 0:
            self._contained_variables.update(self.val1.contained_variables)
            self._contained_variables.update(self.val2.contained_variables)

        return self._contained_variables

    def accept(self, visitor):
        visitor.visit_condition(self)

    def __str__(self) -> str:
        return f"{self.val1} {self.op.value} {self.val2}"
