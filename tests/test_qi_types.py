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
from qiclib.code.qi_jobs import (
    QiIntVariable,
    QiJob,
    QiTimeVariable,
    QiVariable,
    QiCells,
    QiType,
    Recording,
    Assign,
    Wait,
    If,
    ForRange,
    QiPulse,
)
from qiclib.code.qi_var_definitions import QiTimeValue, QiNormalValue


class QiVariableInferenceTest(unittest.TestCase):
    def test_wait_defining_use(self):
        with QiJob():
            cells = QiCells(1)

            x = QiVariable()

            self.assertEqual(x.type, QiType.UNKNOWN)

            Wait(cells[0], x)

        self.assertEqual(x.type, QiType.TIME)

    def test_pulse_defining_use(self):
        with QiJob():
            cells = QiCells(1)

            x = QiVariable()

            self.assertEqual(x.type, QiType.UNKNOWN)

            pulse = QiPulse(x)

        self.assertEqual(x.type, QiType.TIME)

    def test_state_defining_use(self):
        with QiJob():
            cells = QiCells(1)

            x = QiVariable()

            self.assertEqual(x.type, QiType.UNKNOWN)

            Recording(cells[0], 20e-9, state_to=x)

        self.assertEqual(x.type, QiType.STATE)

    def test_shift_defining_use(self):
        job = QiJob()
        job.__enter__()

        x = QiVariable()
        y = QiVariable()

        self.assertEqual(x.type, QiType.UNKNOWN)
        self.assertEqual(y.type, QiType.UNKNOWN)

        z = x << y

        self.assertEqual(x.type, QiType.UNKNOWN)
        self.assertEqual(y.type, QiType.NORMAL)
        self.assertEqual(z.type, QiType.UNKNOWN)

    def test_calc_propagation(self):
        with QiJob():
            cells = QiCells(1)

            x = QiVariable()

            self.assertEqual(x.type, QiType.UNKNOWN)

            y = 2 * x + 4e-9

            Assign(QiVariable(), y)

        self.assertEqual(y.type, QiType.TIME)
        self.assertEqual(x.type, QiType.TIME)

    def test_time_result_calc_propagation(self):
        with QiJob():
            cells = QiCells(1)

            x = QiVariable()
            y = QiVariable()

            z = x + y

            self.assertEqual(x.type, QiType.UNKNOWN)
            self.assertEqual(y.type, QiType.UNKNOWN)
            self.assertEqual(z.type, QiType.UNKNOWN)

            Wait(cells[0], z)

            self.assertEqual(x.type, QiType.TIME)
            self.assertEqual(y.type, QiType.TIME)
            self.assertEqual(z.type, QiType.TIME)

    def test_contradictory_types(self):
        with QiJob():
            cells = QiCells(1)
            x = QiVariable()

            Wait(cells[0], x)

            self.assertEqual(x.type, QiType.TIME)

            with self.assertRaisesRegex(
                TypeError,
                "QiVariable\(\) was of type QiType.TIME\\n"
                + "\(because it is used as length in wait command\)\\n"
                + "but is also used as type QiType.STATE\\n"
                + "\(because it is used as save_to of recording command\)",
            ):
                Recording(cells[0], 20e-9, state_to=x)

    def test_assign_inference(self):
        with QiJob():
            x = QiVariable()

            self.assertEqual(x.type, QiType.UNKNOWN)

            Assign(x, QiTimeValue(40e-9))

            self.assertEqual(x.type, QiType.TIME)

    def test_normal_value(self):
        with QiJob():
            x = QiVariable()

            self.assertEqual(x.type, QiType.UNKNOWN)

            Assign(x, QiNormalValue(20))

            self.assertEqual(x.type, QiType.NORMAL)

    def test_reverse_assign_inference(self):
        with QiJob():
            y = QiVariable()
            x = QiVariable(type=QiType.TIME)

            self.assertEqual(y.type, QiType.UNKNOWN)

            Assign(x, y)

            self.assertEqual(y.type, QiType.TIME)

    def test_operand_inference(self):
        with QiJob():
            cells = QiCells(1)

            x = QiVariable(type=QiType.TIME)
            y = QiVariable()

            self.assertEqual(y.type, QiType.UNKNOWN)

            Wait(cells[0], x * y)

            self.assertEqual(y.type, QiType.NORMAL)

    def test_indirect_inference(self):
        with QiJob():
            cells = QiCells(1)

            x = QiVariable()
            y = QiVariable()

            with If(x < y):
                self.assertEqual(x.type, QiType.UNKNOWN)
                self.assertEqual(y.type, QiType.UNKNOWN)

                Wait(cells[0], x)

                self.assertEqual(x.type, QiType.TIME)
                self.assertEqual(y.type, QiType.TIME)

    def test_time_loop_inference(self):
        with QiJob():
            x = QiVariable()

            self.assertEqual(x.type, QiType.UNKNOWN)

            with ForRange(x, 0, QiTimeVariable(), 4e-9):
                self.assertEqual(x.type, QiType.TIME)

    def test_int_loop_inference(self):
        with QiJob():
            x = QiVariable()

            with ForRange(x, 2, 100):
                pass

        self.assertEqual(x.type, QiType.NORMAL)

    def test_indirect_operand_inference(self):
        with QiJob():
            cells = QiCells(1)

            x = QiVariable()
            y = QiVariable()

            Assign(y, x * 12)

            # At this point, y and x can bei either TIME or NORMAL.

            self.assertEqual(x.type, QiType.UNKNOWN)
            self.assertEqual(y.type, QiType.UNKNOWN)

            Wait(cells[0], y)

        self.assertEqual(x.type, QiType.TIME)
        self.assertEqual(y.type, QiType.TIME)

    def test_condition_calc_propagation(self):
        job = QiJob()
        job.__enter__()

        cells = QiCells(1)

        x1 = QiVariable()
        x2 = QiVariable()
        y1 = QiVariable()
        y2 = QiVariable()

        x = x1 * x2
        y = y1 * y2

        with If(x == y):
            self.assertEqual(x1.type, QiType.UNKNOWN)
            self.assertEqual(x2.type, QiType.UNKNOWN)
            self.assertEqual(x.type, QiType.UNKNOWN)
            self.assertEqual(y1.type, QiType.UNKNOWN)
            self.assertEqual(y2.type, QiType.UNKNOWN)
            self.assertEqual(y.type, QiType.UNKNOWN)

            Wait(cells[0], x1)

            self.assertEqual(x1.type, QiType.TIME)
            self.assertEqual(x2.type, QiType.NORMAL)
            self.assertEqual(x.type, QiType.TIME)
            self.assertEqual(y1.type, QiType.UNKNOWN)
            self.assertEqual(y2.type, QiType.UNKNOWN)
            self.assertEqual(y.type, QiType.TIME)

        with self.assertRaisesRegex(TypeError, "Could not infer type of QiVariable()."):
            job.__exit__(None, None, None)


class QiTypeErrorTest(unittest.TestCase):
    def test_illegal_type_error(self):
        with QiJob() as job:
            cells = QiCells(1)

            x = QiVariable(name="X")

            with ForRange(x, 1, 10, 1):
                with self.assertRaisesRegex(
                    TypeError,
                    "QiVariable\(X\) can not have QiType.STATE\\n"
                    + "\(because ForRanges can only iterate over TIME or NORMAL values\)\\n"
                    + "but the type is required.\\n"
                    + "\(because it is used as save_to of recording command\)",
                ):
                    Recording(cells[0], 100e-9, state_to=x)

    def test_multiplication_unknown_type_error(self):
        job = QiJob()
        job.__enter__()

        cells = QiCells(1)

        x = QiVariable(name="X")
        y = QiVariable(name="Y")
        z = y * x

        Wait(cells[0], z)

        with self.assertRaisesRegex(
            TypeError, "Could not infer type of QiVariable\(Y\)."
        ):
            job.__exit__(None, None, None)

    def test_large_equality_chain_error(self):
        with QiJob() as job:
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

            with self.assertRaisesRegex(
                TypeError,
                "QiVariable\(Z\) was of type QiType.TIME\\n"
                + "\(because it is used as length in wait command\)\\n"
                + "but is also used as type QiType.NORMAL\\n"
                + "\(because it is used in QiOp.MULT calculation of type QiType.TIME\\n"
                + "\(because QiVariable\(W\) has type QiType.TIME\\n"
                + "\(because it is compared with QiVariable\(X\) with type QiType.TIME\\n"
                + "\(because QiVariable\(X\) is compared with QiVariable\(Y\) with type QiType.TIME\\n"
                + "\(because QiVariable\(Y\) is compared with QiVariable\(Z\) with type QiType.TIME\\n"
                + "\(because QiVariable\(Z\) is used as length in wait command\)\)\)\)\)\)",
            ):
                Wait(cells[0], z)

    def test_expression_error(self):
        from qiclib.code.qi_var_definitions import QiTimeValue

        with QiJob() as job:
            x = QiVariable(name="X")
            y = QiVariable(name="Y")
            z = QiVariable(name="Z")

            a = x + 23
            b = a * QiTimeValue(4.0)

            c = z + y

            Assign(z, b)

            with self.assertRaisesRegex(
                TypeError,
                "QiVariable\(I\) was of type QiType.NORMAL\\n"
                + "\(because it has been defined by the user as this type\)\\n"
                + "but is also used as type QiType.TIME\\n"
                + "\(because it is used in ForRange over type QiType.TIME\\n"
                + "\(because 1 is used in ForRange over type QiType.TIME\\n"
                + "\(because QiVariable\(Y\) is used in QiOp.PLUS calculation of type QiType.TIME\\n"
                + "\(because \(QiVariable\(Z\) \+ QiVariable\(Y\)\) is used in QiOp.PLUS calculation of type QiType.TIME\\n"
                + "\(because QiVariable\(Z\) is used in Assign command with type QiType.TIME\\n"
                + "\(because \(\(QiVariable\(X\) \+ 23\) \* 4\) is used in QiOp.MULT calculation of type QiType.TIME\\n"
                + "\(because 4 has type QiType.TIME\\n"
                + "\(because it has been defined by the user as this type\)\)\)\)\)\)\)\)",
            ):
                with ForRange(QiIntVariable(name="I"), 0, y, 1):
                    pass

    def test_simple_error(self):
        with self.assertRaisesRegex(
            TypeError,
            "42 can not have QiType.NORMAL\\n"
            + "\(because constant float values can not be of type NORMAL\)\\n"
            + "but the type is required.\\n"
            + "\(because it is used in Assign command with type QiType.NORMAL\\n"
            + "\(because QiVariable\(I\) has been defined by the user as this type\)\)",
        ):
            with QiJob() as job:
                Assign(QiIntVariable(name="I"), 42.0)

    def test_integer_multiplication(self):
        with QiJob():
            x = QiIntVariable(name="X")
            y = QiIntVariable(name="Y")

            z = x * y

            with self.assertRaisesRegex(
                TypeError,
                "\(QiVariable\(X\) \* QiVariable\(Y\)\) was of type QiType.NORMAL\\n"
                + "\(because it is used in QiOp.MULT calculation of type QiType.NORMAL\\n"
                + "\(because QiVariable\(Y\) has type QiType.NORMAL\\n"
                + "\(because it has been defined by the user as this type\)\\n"
                + "and QiVariable\(X\) has type QiType.NORMAL\\n"
                + "\(because it has been defined by the user as this type\)\)\)\\n"
                + "but is also used as type QiType.TIME\\n"
                + "\(because it is used as length in wait command\)",
            ):
                Wait(QiCells(1)[0], z)

    def test_constant_state_value(self):
        from qiclib.code.qi_var_definitions import _QiConstValue

        with QiJob():
            cells = QiCells(1)
            x = QiVariable()

            constant_one = _QiConstValue(1)
            Recording(cells[0], 20e-9, state_to=x)

            with If(x != constant_one):
                pass

            self.assertEqual(constant_one.type, QiType.STATE)

    def test_constant_state_value_error(self):
        from qiclib.code.qi_var_definitions import _QiConstValue

        with QiJob():
            cells = QiCells(1)
            x = QiVariable()

            constant_one = _QiConstValue(2)
            Recording(cells[0], 20e-9, state_to=x)

            with self.assertRaises(TypeError):
                with If(x != constant_one):
                    pass
