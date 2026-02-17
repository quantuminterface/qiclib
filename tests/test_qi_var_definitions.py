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
from qiclib.code.qi_types import QiType
from qiclib.code.qi_var_definitions import _QiVariableBase


def test_contained_variables():
    x = _QiVariableBase(QiType.NORMAL)
    y = _QiVariableBase(QiType.NORMAL)
    z = _QiVariableBase(QiType.NORMAL)

    a = x + y + z

    assert x in a.contained_variables
    assert y in a.contained_variables
    assert z in a.contained_variables
