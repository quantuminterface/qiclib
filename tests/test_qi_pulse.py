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

import qiclib.packages.utility as util
from qiclib.code.qi_pulse import QiPulse, ShapeLib
from qiclib.code.qi_jobs import (
    QiCellProperty,
    QiVariable,
    QiStateVariable,
    QiCell,
    QiJob,
    _set_job_reference,
    _delete_job_reference,
)
from qiclib.packages.constants import CONTROLLER_SAMPLE_FREQUENCY_IN_HZ as samplerate


class QiPulseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.job = QiJob()
        _set_job_reference(self.job)
        return super().setUp()

    def tearDown(self) -> None:
        _delete_job_reference()
        return super().tearDown()

    def test_shape_error(self):
        with self.assertRaises(NotImplementedError):
            QiPulse(length=QiVariable(), shape=ShapeLib.gauss)

    def test_length_error(self):
        with self.assertRaises(RuntimeError):
            QiPulse(length=util.conv_cycles_to_time(2**32))

    def test_variable_amplitude_error(self):
        with self.assertRaises(RuntimeError):
            QiPulse(length=40e-9, amplitude=QiVariable(int))

    def test_state_var_error(self):
        with self.assertRaises(TypeError):
            QiPulse(length=QiStateVariable())

    def test_pulse_equal_variable_length(self):
        variable1 = QiVariable()
        variable2 = QiVariable()
        pulse1 = QiPulse(length=variable1)
        pulse2 = QiPulse(length=variable2)

        self.assertEqual(pulse1, pulse2)

    def test_pulse_equal_length(self):
        pulse1 = QiPulse(length=40e-9)
        pulse2 = QiPulse(length=40e-9)

        self.assertEqual(pulse1, pulse2)

    def test_pulse_not_equal_length(self):
        pulse1 = QiPulse(length=40e-9)
        pulse2 = QiPulse(length=41e-9)

        self.assertNotEqual(pulse1, pulse2)

    def test_pulse_not_equal_length_variable(self):
        variable1 = QiVariable()
        pulse1 = QiPulse(length=variable1)
        pulse2 = QiPulse(length=41e-9)

        self.assertNotEqual(pulse1, pulse2)

    def test_get_pulse_length(self):
        pulse = QiPulse(length=41e-9)

        self.assertEqual(pulse.length, 41e-9)

    def test_get_pulse_length_cell_property(self):
        cell = QiCell(42)

        pulse = QiPulse(length=cell["test"])

        self.assertIsInstance(pulse.length, QiCellProperty)

        cell["test"] = 52e-9

        envelope = pulse(samplerate)

        self.assertEqual(len(envelope), 52e-9 * samplerate)

    def test_get_pulse_length_variable(self):
        variable = QiVariable()
        pulse = QiPulse(length=variable)

        length = pulse.length

        self.assertIsInstance(length, QiVariable)

        if isinstance(length, QiVariable):
            self.assertEqual(length.id, variable.id)

    def test_cw_pulse_initialization(self):
        pulse_cw = QiPulse("cw", amplitude=0.5, frequency=66e6)

        self.assertEqual(pulse_cw.hold, True)
        self.assertIsInstance(pulse_cw.length, float)
        self.assertEqual(pulse_cw.length, util.conv_cycles_to_time(1))
        self.assertEqual(pulse_cw.amplitude, 0.5)
        self.assertEqual(pulse_cw.frequency, 66e6)

        pulse_off = QiPulse("OFF")  # Case insensitive check (no exception raised)

        self.assertEqual(pulse_off.hold, False)
        self.assertIsInstance(pulse_off.length, float)
        self.assertEqual(pulse_off.length, util.conv_cycles_to_time(1))
        self.assertEqual(pulse_off.amplitude, 0)
        self.assertEqual(pulse_off.frequency, None)

    def test_invalid_length_str_at_init(self):
        with self.assertRaisesRegex(
            ValueError, "QiPulse with str length only accepts 'cw' or 'off'."
        ):
            QiPulse("test")
