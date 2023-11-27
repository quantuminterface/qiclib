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
    QiJob,
    QiVariable,
)


class QiCalcTest(unittest.TestCase):
    def test_contained_variables(self):
        with QiJob():
            x = QiVariable(int)
            y = QiVariable(int)
            z = QiVariable(int)
            a = x + y + z

            self.assertIn(x, a.contained_variables)
            self.assertIn(y, a.contained_variables)
            self.assertIn(z, a.contained_variables)
