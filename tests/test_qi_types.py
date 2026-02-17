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
import re

import pytest

from qiclib.code import (
    Assign,
    ForRange,
    If,
    Play,
    QiCells,
    QiIntVariable,
    QiJob,
    QiPulse,
    QiTimeVariable,
    QiType,
    QiVariable,
    Recording,
    Wait,
)
from qiclib.code.qi_command import (
    AssignCommand,
    IfCommand,
    RecordingCommand,
    WaitCommand,
)
from qiclib.code.qi_var_definitions import (
    QiConst,
    QiTimeValue,
    _QiConstValue,
    _QiVariableBase,
)


def test_wait_defining_use():
    with QiJob() as job:
        cells = QiCells(1)
        x = QiVariable()

        Wait(cells[0], x)

    assert job.get_var(x).type == QiType.TIME


def test_pulse_defining_use():
    with QiJob() as job:
        q = QiCells(1)
        x = QiVariable()

        Play(q[0], QiPulse(x))

    assert job.get_var(x).type == QiType.TIME


def test_state_defining_use():
    with QiJob() as job:
        cells = QiCells(1)

        x = QiVariable()

        Recording(cells[0], 20e-9, state_to=x)

    assert job.get_var(x).type == QiType.STATE


def test_shift_defining_use():
    x = _QiVariableBase(QiType.UNKNOWN)
    y = _QiVariableBase(QiType.UNKNOWN)

    assert x.type == QiType.UNKNOWN
    assert y.type == QiType.UNKNOWN

    z = x << y

    assert x.type == QiType.UNKNOWN
    assert y.type == QiType.NORMAL
    assert z.type == QiType.UNKNOWN


def test_calc_propagation():
    with QiJob() as job:
        _cells = QiCells(1)
        x = QiVariable()

        y = 2 * x + 4e-9

        Assign(QiVariable(), y)

    assert job.get_var(x).type == QiType.TIME


def test_time_result_calc_propagation():
    with QiJob() as job:
        cells = QiCells(1)

        x = QiVariable()
        y = QiVariable()

    x = job.get_var(x)
    y = job.get_var(y)
    z = x + y

    assert x.type == QiType.UNKNOWN
    assert y.type == QiType.UNKNOWN
    assert z.type == QiType.UNKNOWN

    WaitCommand(cells[0], z)

    assert x.type == QiType.TIME
    assert y.type == QiType.TIME
    assert z.type == QiType.TIME


def test_contradictory_types():
    with QiJob() as job:
        cells = QiCells(1)
        x = QiVariable()

        Wait(cells[0], x)

    x = job.get_var(x)
    assert x.type == QiType.TIME

    with pytest.raises(
        TypeError,
        match="QiVariable\\(\\) was of type TIME\\n"
        + "\\(because it is used as length in wait command\\)\\n"
        + "but is also used as type STATE\\n"
        + r"\(because it is used as save_to of recording command\)",
    ):
        RecordingCommand(cells[0], length=20e-9, save_to=None, state_to=x, offset=0)


def test_assign_inference():
    x = _QiVariableBase(QiType.UNKNOWN)
    AssignCommand(x, _QiConstValue(40e-9, QiType.TIME))

    assert x.type == QiType.TIME


def test_normal_value():
    x = _QiVariableBase(QiType.UNKNOWN)
    AssignCommand(x, _QiConstValue(20, QiType.NORMAL))
    assert x.type == QiType.NORMAL


def test_reverse_assign_inference():
    y = _QiVariableBase(QiType.UNKNOWN)
    x = _QiVariableBase(QiType.TIME)

    AssignCommand(x, y)

    assert y.type == QiType.TIME


def test_operand_inference():
    with QiJob() as job:
        cells = QiCells(1)

        x = QiTimeVariable()
        y = QiVariable()

        Wait(cells[0], x * y)

    assert job.get_var(y).type == QiType.NORMAL


def test_indirect_inference():
    with QiJob() as job:
        cells = QiCells(1)

        x = QiVariable()
        y = QiVariable()

        with If(x < y):
            Wait(cells[0], x)

    x = job.get_var(x)
    y = job.get_var(y)

    assert x.type == QiType.TIME
    assert y.type == QiType.TIME


def test_time_loop_inference():
    with QiJob() as job:
        x = QiVariable()

        with ForRange(x, 0, QiTimeVariable(), 4e-9):
            pass

    assert job.get_var(x).type == QiType.TIME


def test_int_loop_inference():
    with QiJob() as job:
        x = QiVariable()

        with ForRange(x, 2, 100):
            pass

    assert job.get_var(x).type == QiType.NORMAL


def test_indirect_operand_inference():
    with QiJob() as job:
        cells = QiCells(1)

        x = QiVariable()
        y = QiVariable()

        Assign(y, x * 12)

        # At this point, y and x can bei either TIME or NORMAL.

        Wait(cells[0], y)

    assert job.get_var(x).type == QiType.TIME
    assert job.get_var(y).type == QiType.TIME


def test_condition_calc_propagation():
    with pytest.raises(
        TypeError, match=re.escape("Could not infer type of QiVariable().")
    ):
        with QiJob() as job:
            cells = QiCells(1)

            x1 = QiVariable()
            x2 = QiVariable()
            y1 = QiVariable()
            y2 = QiVariable()

            x = x1 * x2
            y = y1 * y2

            with If(x == y):
                Wait(cells[0], x1)

    assert job.get_var(x1).type == QiType.TIME
    assert job.get_var(x2).type == QiType.NORMAL
    assert job.get_var(y1).type == QiType.UNKNOWN
    assert job.get_var(y2).type == QiType.UNKNOWN


def test_illegal_type_error():
    with pytest.raises(
        TypeError,
        match="QiVariable\\(X\\) can not have STATE\\n"
        + "\\(because ForRanges can only iterate over TIME or NORMAL values\\)\\n"
        + "but the type is required.\\n"
        + r"\(because it is used as save_to of recording command\)",
    ):
        with QiJob():
            cells = QiCells(1)

            x = QiVariable(name="X")

            with ForRange(x, 1, 10, 1):
                Recording(cells[0], 100e-9, state_to=x)


def test_multiplication_unknown_type_error():
    job = QiJob()
    job.__enter__()

    cells = QiCells(1)

    x = QiVariable(name="X")
    y = QiVariable(name="Y")
    z = y * x

    Wait(cells[0], z)

    with pytest.raises(TypeError, match=r"Could not infer type of QiVariable\(Y\)."):
        job.__exit__(None, None, None)


def test_large_equality_chain_error():
    with pytest.raises(
        TypeError,
        match="QiVariable\\(Z\\) was of type TIME\\n"
        + "\\(because it is used as length in wait command\\)\\n"
        + "but is also used as type NORMAL\\n"
        + "\\(because it is used in QiOp.MULT calculation of type TIME\\n"
        + "\\(because QiVariable\\(W\\) has type TIME\\n"
        + "\\(because it is compared with QiVariable\\(X\\) with type TIME\\n"
        + "\\(because QiVariable\\(X\\) is compared with QiVariable\\(Y\\) with type TIME\\n"
        + "\\(because QiVariable\\(Y\\) is compared with QiVariable\\(Z\\) with type TIME\\n"
        + r"\(because QiVariable\(Z\) is used as length in wait command\)\)\)\)\)\)",
    ):
        with QiJob():
            cells = QiCells(1)

            w = QiVariable(name="W")
            x = QiVariable(name="X")
            y = QiVariable(name="Y")
            z = QiVariable(name="Z")

            with If(x == w):
                pass

            with If(y == x):
                pass

            with If(y == z):
                pass

            Wait(cells[0], w * z)

            Wait(cells[0], z)


def test_expression_error():
    with pytest.raises(
        TypeError,
        match=re.escape("""QiVariable(I) was of type NORMAL
(because it has been defined by the user as this type)
but is also used as type TIME
(because it is used in ForRange over type TIME
(because 1 is used in ForRange over type TIME
(because QiVariable(Y) is used in QiOp.PLUS calculation of type TIME
(because (QiVariable(Z) + QiVariable(Y)) is used in QiOp.PLUS calculation of type TIME
(because QiVariable(Z) is used in Assign command with type TIME
(because QiVariable(b) is used in Assign command with type TIME
(because (QiVariable(a) * 4) is used in QiOp.MULT calculation of type TIME
(because 4 has type TIME
(because it has been defined by the user as this type)))))))))"""),
    ):
        with QiJob():
            x = QiVariable(name="X")
            y = QiVariable(name="Y")
            z = QiVariable(name="Z")

            a = QiVariable(name="a")
            Assign(a, x + 23)
            b = QiVariable(name="b")
            Assign(b, a * QiTimeValue(4.0))

            Assign(QiVariable(name="c"), z + y)

            Assign(z, b)

            with ForRange(QiIntVariable(name="I"), 0, y, 1):
                pass


def test_simple_error():
    with pytest.raises(
        TypeError,
        match="42 can not have NORMAL\\n"
        + "\\(because constant float values can not be of type NORMAL\\)\\n"
        + "but the type is required.\\n"
        + "\\(because it is used in Assign command with type NORMAL\\n"
        + r"\(because QiVariable\(I\) has been defined by the user as this type\)\)",
    ):
        with QiJob():
            Assign(QiIntVariable(name="I"), 42.0)


def test_integer_multiplication():
    with pytest.raises(
        TypeError,
        match="\\(QiVariable\\(X\\) \\* QiVariable\\(Y\\)\\) was of type NORMAL\\n"
        + "\\(because it is used in QiOp.MULT calculation of type NORMAL\\n"
        + "\\(because QiVariable\\(Y\\) has type NORMAL\\n"
        + "\\(because it has been defined by the user as this type\\)\\n"
        + "and QiVariable\\(X\\) has type NORMAL\\n"
        + "\\(because it has been defined by the user as this type\\)\\)\\)\\n"
        + "but is also used as type TIME\\n"
        + r"\(because it is used as length in wait command\)",
    ):
        with QiJob():
            x = QiIntVariable(name="X")
            y = QiIntVariable(name="Y")

            z = x * y

            Wait(QiCells(1)[0], z)


def test_constant_state_value():
    with QiJob() as job:
        cells = QiCells(1)
        x = QiVariable()

        constant_one = QiConst(1)
        Recording(cells[0], 20e-9, state_to=x)

        with If(x != constant_one):
            pass

    if_cmd = next(filter(lambda cmd: isinstance(cmd, IfCommand), job.commands))
    assert isinstance(if_cmd, IfCommand)
    c_one = if_cmd.condition.val2
    assert isinstance(c_one, _QiConstValue)
    assert c_one.type == QiType.STATE


def test_constant_state_value_error():
    with pytest.raises(TypeError):
        with QiJob():
            cells = QiCells(1)
            x = QiVariable()

            constant_one = QiConst(2)
            Recording(cells[0], 20e-9, state_to=x)

            with If(x != constant_one):
                pass
