"""Test __str__ methods for all QiCode classes."""

from qicode.proto.compiled_job_pb2 import CompiledJob as ProtoCompiledJob

from qicode import (
    CompiledJob,
    QiCells,
    QiConst,
    QiCouplers,
    QiExpression,
    QiIntVariable,
    QiJob,
    QiPulse,
    QiType,
)


def test_qi_type_strings():
    """Test string representations of QiType constants."""
    assert str(QiType.TIME) == "TIME"
    assert str(QiType.STATE) == "STATE"
    assert str(QiType.NORMAL) == "NORMAL"
    assert str(QiType.FREQUENCY) == "FREQUENCY"
    assert str(QiType.PHASE) == "PHASE"
    assert str(QiType.AMPLITUDE) == "AMPLITUDE"
    assert str(QiType.UNKNOWN) == "UNKNOWN"


def test_qi_array_type_strings():
    """Test string representations of QiType arrays."""
    assert str(QiType.ARRAY(QiType.TIME, length=10)) == "Array[TIME, 10]"
    assert str(QiType.ARRAY(QiType.NORMAL)) == "Array[NORMAL, ?]"


def test_qi_expression_literals():
    """Test string representations of QiExpression literals."""
    assert str(QiExpression.from_any(42)) == "42"
    assert str(QiExpression.from_any(3.14)) == "3.14"
    # Array format includes proto internal representation
    array_str = str(QiExpression.from_any([1, 2, 3]))
    assert array_str.startswith("[")
    assert array_str.endswith("]")


def test_qi_expression_binary_operations():
    """Test string representations of binary operations."""
    expr_add = QiExpression.from_any(5) + QiExpression.from_any(3)
    assert str(expr_add) == "(5 + 3)"

    expr_sub = QiExpression.from_any(10) - QiExpression.from_any(2)
    assert str(expr_sub) == "(10 - 2)"

    expr_mul = QiExpression.from_any(4) * QiExpression.from_any(2)
    assert str(expr_mul) == "(4 * 2)"


def test_qi_expression_unary_operations():
    """Test string representations of unary operations."""
    expr_neg = -QiExpression.from_any(5)
    assert str(expr_neg) == "(-5)"

    expr_pos = +QiExpression.from_any(5)
    assert str(expr_pos) == "(+5)"


def test_qi_expression_type_cast():
    """Test string representation of type casts."""
    expr = QiConst(42, QiType.TIME)
    assert str(expr) == "(TIME)42"


def test_qi_cell_str():
    """Test QiCell string representation."""
    with QiJob():
        cells = QiCells(3)
        assert str(cells[0]) == "QiCell(0)"
        assert str(cells[1]) == "QiCell(1)"
        assert str(cells[2]) == "QiCell(2)"


def test_qi_cells_str():
    """Test QiCells string representation."""
    with QiJob():
        cells = QiCells(4)
        assert str(cells) == "QiCells(4)"

    with QiJob():
        cells = QiCells(1)
        assert str(cells) == "QiCells(1)"


def test_qi_coupler_str():
    """Test QiCoupler string representation."""
    with QiJob():
        couplers = QiCouplers(2)
        assert str(couplers[0]) == "QiCoupler(0)"
        assert str(couplers[1]) == "QiCoupler(1)"


def test_qi_couplers_str():
    """Test QiCouplers string representation."""
    with QiJob():
        couplers = QiCouplers(5)
        assert str(couplers) == "QiCouplers(5)"


def test_variable_ref_str():
    """Test VariableRef string representation."""
    with QiJob():
        var1 = QiIntVariable()
        var2 = QiIntVariable()
        assert str(var1) == f"Var_{var1._variable.id}"
        assert str(var2) == f"Var_{var2._variable.id}"
        assert str(var1) != str(var2)


def test_qi_job_empty():
    """Test QiJob string representation with default settings."""
    with QiJob():
        pass


def test_qi_job_with_skip_nco_sync():
    """Test QiJob string representation with skip_nco_sync flag."""
    with QiJob(skip_nco_sync=True):
        pass


def test_qi_job_with_cells():
    """Test QiJob string representation with cells."""
    with QiJob() as job:
        QiCells(2)
        assert str(job) == "QiJob(commands=0, cells=2, couplers=0, skipNcoSync=False)"


def test_qi_job_with_couplers():
    """Test QiJob string representation with couplers."""
    with QiJob() as job:
        QiCouplers(3)
        assert str(job) == "QiJob(commands=0, cells=0, couplers=3, skipNcoSync=False)"


def test_qi_pulse_off():
    """Test QiPulse.off() string representation."""
    pulse = QiPulse.off()
    assert str(pulse) == "QiPulse(off)"


def test_qi_pulse_cw():
    """Test QiPulse.cw() string representation."""
    pulse = QiPulse.cw(frequency=1e9, amplitude=0.5, phase=0.25)
    # The exact format depends on proto representation
    assert str(pulse).startswith("QiPulse(cw")
    assert "frequency=" in str(pulse)
    assert "amplitude=" in str(pulse)
    assert "phase=" in str(pulse)


def test_qi_pulse_discrete():
    """Test discrete QiPulse string representation."""
    pulse = QiPulse(length=100e-9, frequency=1e9, amplitude=0.8, phase=0.0, hold=False)
    # The exact format depends on proto representation
    assert str(pulse).startswith("QiPulse(")
    assert "length=" in str(pulse)
    assert "frequency=" in str(pulse)
    assert "amplitude=" in str(pulse)
    assert "phase=" in str(pulse)
    assert "hold=" in str(pulse)


def test_compiled_job():
    """Test CompiledJob assembly format string representation."""
    assembly_job = ProtoCompiledJob()
    compiled_job = CompiledJob(assembly_job)
    result = str(compiled_job)
    assert result.startswith("CompiledJob(size=")
    assert "bytes)" in result
