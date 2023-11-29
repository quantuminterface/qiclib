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
from qiclib.code.qi_jobs import (
    QiJob,
    QiVariable,
    QiTimeVariable,
    ForRange,
    _set_job_reference,
    _delete_job_reference,
)
from qiclib.code.qi_util import _get_for_range_end_value, _get_for_range_iterations
from qiclib.code.qi_types import QiPostTypecheckVisitor


class UtilFunctionTest(unittest.TestCase):
    def setUp(self) -> None:
        job = QiJob()
        _set_job_reference(job)

    def tearDown(self) -> None:
        _delete_job_reference()
        return super().tearDown()

    def test_end_val(self):
        fr_cm = ForRange(QiVariable(int), 1, 20, 5)

        end_val = _get_for_range_end_value(fr_cm.start, fr_cm.end, fr_cm.step)

        self.assertEqual(end_val, 21)

        fr_cm = ForRange(QiTimeVariable(), 0, 24e-9, 4e-9)
        fr_cm.accept(QiPostTypecheckVisitor())

        end_val = _get_for_range_end_value(fr_cm.start, fr_cm.end, fr_cm.step)

        self.assertEqual(
            end_val, util.conv_time_to_cycles(24e-9)
        )  # gets converted to cycles, so 6 cycles == 24e-9

    def test_iterations(self):
        fr_cm = ForRange(QiVariable(int), 1, 20, 5)
        iterations = _get_for_range_iterations(fr_cm.start, fr_cm.end, fr_cm.step)

        self.assertEqual(iterations, 4)

        fr_cm = ForRange(QiTimeVariable(), 0, 24e-9, 4e-9)
        fr_cm.accept(QiPostTypecheckVisitor())
        iterations = _get_for_range_iterations(fr_cm.start, fr_cm.end, fr_cm.step)

        self.assertEqual(iterations, 6)
