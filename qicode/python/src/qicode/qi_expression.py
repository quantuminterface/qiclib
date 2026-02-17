from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, TypeAlias

from qicode._callsite import capture_callsite
from qicode.proto.commands_pb2 import DeclareCommand
from qicode.proto.expression_pb2 import CellProperty, Expression
from qicode.proto.variables_pb2 import Variable
from qicode.qi_job import QiJob
from qicode.qi_type import QiType

if TYPE_CHECKING:
    # QiCellProperty causes a cyclic import between qi_expression.py and qi_cell.py
    from qicode.qi_cell import QiCell


class _ExpressionMixin:
    def _binary(self, other: Any, op: Expression.Binary.Operator, swap=False):
        lhs = QiExpression.from_any(other if swap else self)._proto()
        rhs = QiExpression.from_any(self if swap else other)._proto()
        return QiExpression(
            Expression(
                binary=Expression.Binary(
                    lhs=lhs,
                    op=op,
                    rhs=rhs,
                )
            )
        )

    def _unary(self, op: Expression.Unary.Operator):
        expr = QiExpression.from_any(self)
        return QiExpression(
            Expression(unary=Expression.Unary(expr=expr._proto(), op=op))
        )

    def __add__(self, other):
        return self._binary(other, Expression.Binary.Operator.Plus)

    def __radd__(self, other):
        return self._binary(other, Expression.Binary.Operator.Plus, swap=True)

    def __sub__(self, other):
        return self._binary(other, Expression.Binary.Operator.Minus)

    def __rsub__(self, other):
        return self._binary(other, Expression.Binary.Operator.Minus, swap=True)

    def __mul__(self, other):
        return self._binary(other, Expression.Binary.Operator.Mult)

    def __rmul__(self, other):
        return self._binary(other, Expression.Binary.Operator.Mult, swap=True)

    def __truediv__(self, other):
        return self._binary(other, Expression.Binary.Operator.Div)

    def __rtruediv__(self, other):
        return self._binary(other, Expression.Binary.Operator.Div, swap=True)

    def __lshift__(self, other):
        return self._binary(other, Expression.Binary.Operator.Lsh)

    def __rlshift__(self, other):
        return self._binary(other, Expression.Binary.Operator.Lsh, swap=True)

    def __rshift__(self, other):
        return self._binary(other, Expression.Binary.Operator.Rsh)

    def __rrshift__(self, other):
        return self._binary(other, Expression.Binary.Operator.Rsh, swap=True)

    def __and__(self, other):
        return self._binary(other, Expression.Binary.Operator.And)

    def __rand__(self, other):
        return self._binary(other, Expression.Binary.Operator.And, swap=True)

    def __or__(self, other):
        return self._binary(other, Expression.Binary.Operator.Or)

    def __ror__(self, other):
        return self._binary(other, Expression.Binary.Operator.Or, swap=True)

    def __xor__(self, other):
        return self._binary(other, Expression.Binary.Operator.Xor)

    def __rxor__(self, other):
        return self._binary(other, Expression.Binary.Operator.Xor, swap=True)

    def __lt__(self, other):
        return self._binary(other, Expression.Binary.Operator.Lt)

    def __le__(self, other):
        return self._binary(other, Expression.Binary.Operator.Le)

    def __gt__(self, other):
        return self._binary(other, Expression.Binary.Operator.Gt)

    def __ge__(self, other):
        return self._binary(other, Expression.Binary.Operator.Ge)

    def __eq__(self, other):
        return self._binary(other, Expression.Binary.Operator.Eq)

    def __ne__(self, other):
        return self._binary(other, Expression.Binary.Operator.Ne)

    def __invert__(self) -> QiExpression:
        return self._unary(Expression.Unary.Operator.Not)

    def __neg__(self) -> QiExpression:
        return self._unary(Expression.Unary.Operator.Minus)

    def __pos__(self) -> QiExpression:
        return self._unary(Expression.Unary.Operator.Plus)

    def __getitem__(self, item: ExpressionLike) -> QiExpression:
        return QiExpression(
            Expression(
                indexed=Expression.Index(
                    base=QiExpression.from_any(self)._proto(),
                    value=QiExpression.from_any(item)._proto(),
                )
            )
        )


class QiExpression(_ExpressionMixin):
    def __init__(self, _expr: Expression) -> None:
        self._expression = _expr

    @staticmethod
    def from_any(value: Any) -> QiExpression:
        def from_literal(lit: int | float | Iterable) -> Expression.Literal:
            if isinstance(lit, int):
                return Expression.Literal(intLiteral=lit)
            elif isinstance(lit, float):
                return Expression.Literal(floatLiteral=lit)
            else:
                assert isinstance(lit, Iterable)
                return Expression.Literal(
                    arrayLiteral=Expression.Literal.Array(
                        values=(from_literal(el) for el in lit)
                    )
                )

        if isinstance(value, int | float | Iterable):
            return QiExpression(Expression(literal=from_literal(value)))
        if isinstance(value, VariableRef):
            return QiExpression(Expression(variable=value._proto()))
        if isinstance(value, QiCellProperty):
            return QiExpression(Expression(property=value._proto()))
        if isinstance(value, QiExpression):
            return value
        raise ValueError(
            f"value {value} of type {value.__class__.__name__} cannot be converted to a QiExpression"
        )

    def _proto(self) -> Expression:
        return self._expression

    def __str__(self) -> str:
        if self._expression.HasField("literal"):
            lit = self._expression.literal
            if lit.HasField("intLiteral"):
                return str(lit.intLiteral)
            elif lit.HasField("floatLiteral"):
                return str(lit.floatLiteral)
            elif lit.HasField("arrayLiteral"):
                values = [str(v) for v in lit.arrayLiteral.values]
                return f"[{', '.join(values)}]"
        elif self._expression.HasField("variable"):
            return f"Var_{self._expression.variable.id}"
        elif self._expression.HasField("property"):
            return f"Cell[{self._expression.property.name}]"
        elif self._expression.HasField("binary"):
            ops = {
                self._expression.binary.Operator.Plus: "+",
                self._expression.binary.Operator.Minus: "-",
                self._expression.binary.Operator.Mult: "*",
                self._expression.binary.Operator.Div: "/",
                self._expression.binary.Operator.Lsh: "<<",
                self._expression.binary.Operator.Rsh: ">>",
                self._expression.binary.Operator.And: "&",
                self._expression.binary.Operator.Or: "|",
                self._expression.binary.Operator.Xor: "^",
                self._expression.binary.Operator.Lt: "<",
                self._expression.binary.Operator.Le: "<=",
                self._expression.binary.Operator.Gt: ">",
                self._expression.binary.Operator.Ge: ">=",
                self._expression.binary.Operator.Eq: "==",
                self._expression.binary.Operator.Ne: "!=",
            }
            op_str = ops.get(self._expression.binary.op, "?")
            lhs = QiExpression(self._expression.binary.lhs)
            rhs = QiExpression(self._expression.binary.rhs)
            return f"({lhs} {op_str} {rhs})"
        elif self._expression.HasField("unary"):
            ops = {
                self._expression.unary.Operator.Not: "!",
                self._expression.unary.Operator.Minus: "-",
                self._expression.unary.Operator.Plus: "+",
            }
            op_str = ops.get(self._expression.unary.op, "?")
            expr = QiExpression(self._expression.unary.expr)
            return f"({op_str}{expr})"
        elif self._expression.HasField("indexed"):
            base = QiExpression(self._expression.indexed.base)
            index = QiExpression(self._expression.indexed.value)
            return f"{base}[{index}]"
        elif self._expression.HasField("typeCast"):
            expr = QiExpression(self._expression.typeCast.expr)
            target_type = QiType(self._expression.typeCast.targetType)
            return f"({target_type}){expr}"
        return "QiExpression(?)"


class QiCellProperty(_ExpressionMixin):
    def __init__(
        self, cell: QiCell, name: str, default: ExpressionLike | None = None
    ) -> None:
        if default is not None:
            default_value = QiExpression.from_any(default)._proto()
        else:
            default_value = None
        self._property = CellProperty(
            cell=cell._proto(), name=name, defaultValue=default_value
        )

    def _proto(self) -> CellProperty:
        return self._property

    def __str__(self) -> str:
        return (
            f"QiCellProperty(cell[{self._property.cell.index}].{self._property.name})"
        )


class VariableRef(_ExpressionMixin):
    def __init__(self) -> None:
        self._variable = QiJob._current().request_variable()

    def _proto(self) -> Variable:
        return self._variable

    def __str__(self) -> str:
        return f"Var_{self._variable.id}"


ExpressionLike: TypeAlias = (
    QiExpression
    | int
    | float
    | Iterable[int]
    | Iterable[float]
    | QiCellProperty
    | VariableRef
)


def QiVariable(
    type: QiType | type[int] = QiType.UNKNOWN,
    value: ExpressionLike | None = None,
    name: str | None = None,
    static: bool = False,
) -> VariableRef:
    var = VariableRef()
    initial_value = None
    if value is not None:
        initial_value = QiExpression.from_any(value)._proto()
    QiJob._current()._add_command(
        declareCommand=DeclareCommand(
            var=var._proto(),
            type=QiType.from_any(type)._proto(),
            name=name,
            static=static,
            initialValue=initial_value,
        ),
        sourceInfo=capture_callsite(),
    )
    return var


def QiTimeVariable(
    value: ExpressionLike | None = None,
    name: str | None = None,
    static: bool = False,
) -> VariableRef:
    return QiVariable(QiType.TIME, value, name, static)


def QiFrequencyVariable(
    value: ExpressionLike | None = None,
    name: str | None = None,
    static: bool = False,
) -> VariableRef:
    return QiVariable(QiType.FREQUENCY, value, name, static)


def QiStateVariable(
    value: ExpressionLike | None = None,
    name: str | None = None,
    static: bool = False,
) -> VariableRef:
    return QiVariable(QiType.STATE, value, name, static)


def QiIntVariable(
    value: ExpressionLike | None = None,
    name: str | None = None,
    static: bool = False,
) -> VariableRef:
    return QiVariable(QiType.NORMAL, value, name, static)


def QiPhaseVariable(
    value: ExpressionLike | None = None,
    name: str | None = None,
    static: bool = False,
) -> VariableRef:
    return QiVariable(QiType.PHASE, value, name, static)


def QiAmplitudeVariable(
    value: ExpressionLike | None = None,
    name: str | None = None,
    static: bool = False,
) -> VariableRef:
    return QiVariable(QiType.AMPLITUDE, value, name, static)


def QiConst(value: int | float, type: QiType = QiType.UNKNOWN) -> QiExpression:
    return QiExpression(
        Expression(
            typeCast=Expression.TypeCast(
                expr=QiExpression.from_any(value)._proto(), targetType=type._proto()
            )
        )
    )


def QiTimeValue(value: int | float) -> QiExpression:
    return QiConst(value, QiType.TIME)


def QiFrequencyValue(value: int | float) -> QiExpression:
    return QiConst(value, QiType.FREQUENCY)


def QiStateValue(value: int | float) -> QiExpression:
    return QiConst(value, QiType.STATE)


def QiNormalValue(value: int | float) -> QiExpression:
    return QiConst(value, QiType.NORMAL)


def QiPhaseValue(value: int | float) -> QiExpression:
    return QiConst(value, QiType.PHASE)


def QiAmplitudeValue(value: int | float) -> QiExpression:
    return QiConst(value, QiType.AMPLITUDE)
