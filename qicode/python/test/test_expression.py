from qicode.proto.expression_pb2 import Expression
from qicode.qi_expression import QiExpression


def _make_int_expr(val: int) -> QiExpression:
    return QiExpression(Expression(literal=Expression.Literal(intLiteral=val)))


def test_rsub_operand_order():
    var = _make_int_expr(10)
    result = 3 - var
    binary = result._proto().binary
    assert binary.op == Expression.Binary.Operator.Minus
    assert binary.lhs.literal.intLiteral == 3
    assert binary.rhs.literal.intLiteral == 10


def test_sub_operand_order():
    var = _make_int_expr(10)
    result = var - 3
    binary = result._proto().binary
    assert binary.op == Expression.Binary.Operator.Minus
    assert binary.lhs.literal.intLiteral == 10
    assert binary.rhs.literal.intLiteral == 3


def test_lshift():
    var = _make_int_expr(5)
    result = var << 2
    binary = result._proto().binary
    assert binary.op == Expression.Binary.Operator.Lsh
    assert binary.lhs.literal.intLiteral == 5
    assert binary.rhs.literal.intLiteral == 2


def test_rshift():
    var = _make_int_expr(16)
    result = var >> 3
    binary = result._proto().binary
    assert binary.op == Expression.Binary.Operator.Rsh
    assert binary.lhs.literal.intLiteral == 16
    assert binary.rhs.literal.intLiteral == 3


def test_and_operator():
    var = _make_int_expr(0xFF)
    result = var & 0x0F
    binary = result._proto().binary
    assert binary.op == Expression.Binary.Operator.And
    assert binary.lhs.literal.intLiteral == 0xFF
    assert binary.rhs.literal.intLiteral == 0x0F


def test_rand_operator():
    var = _make_int_expr(0xFF)
    result = 0x0F & var
    binary = result._proto().binary
    assert binary.op == Expression.Binary.Operator.And
    assert binary.lhs.literal.intLiteral == 0x0F
    assert binary.rhs.literal.intLiteral == 0xFF


def test_or_operator():
    var = _make_int_expr(0xA0)
    result = var | 0x05
    binary = result._proto().binary
    assert binary.op == Expression.Binary.Operator.Or
    assert binary.lhs.literal.intLiteral == 0xA0
    assert binary.rhs.literal.intLiteral == 0x05


def test_xor_operator():
    var = _make_int_expr(0xFF)
    result = var ^ 0xAA
    binary = result._proto().binary
    assert binary.op == Expression.Binary.Operator.Xor
    assert binary.lhs.literal.intLiteral == 0xFF
    assert binary.rhs.literal.intLiteral == 0xAA


def test_rmul_operand_order():
    var = _make_int_expr(7)
    result = 3 * var
    binary = result._proto().binary
    assert binary.op == Expression.Binary.Operator.Mult
    assert binary.lhs.literal.intLiteral == 3
    assert binary.rhs.literal.intLiteral == 7


def test_rtruediv_operand_order():
    var = _make_int_expr(4)
    result = 12 / var
    binary = result._proto().binary
    assert binary.op == Expression.Binary.Operator.Div
    assert binary.lhs.literal.intLiteral == 12
    assert binary.rhs.literal.intLiteral == 4


def test_comparison_lt():
    var = _make_int_expr(5)
    result = var < 10
    binary = result._proto().binary
    assert binary.op == Expression.Binary.Operator.Lt


def test_comparison_eq():
    a = _make_int_expr(5)
    b = _make_int_expr(5)
    result = a == b
    binary = result._proto().binary
    assert binary.op == Expression.Binary.Operator.Eq


def test_unary_invert():
    var = _make_int_expr(0xFF)
    result = ~var
    unary = result._proto().unary
    assert unary.op == Expression.Unary.Operator.Not
    assert unary.expr.literal.intLiteral == 0xFF


def test_unary_neg():
    var = _make_int_expr(42)
    result = -var
    unary = result._proto().unary
    assert unary.op == Expression.Unary.Operator.Minus


def test_getitem():
    var = _make_int_expr(100)
    result = var[3]
    indexed = result._proto().indexed
    assert indexed.base.literal.intLiteral == 100
    assert indexed.value.literal.intLiteral == 3
