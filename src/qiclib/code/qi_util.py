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
def _get_for_range_end_value(start, end, step):
    """Returns end value of ForRange or None if start or end are QiVariables.
    Stupid but no need to check validity of input, in case of unrolled loop"""
    from .qi_var_definitions import QiCellProperty, _QiConstValue, _QiVariableBase

    if (
        isinstance(start, _QiVariableBase)
        or start is None
        or isinstance(end, _QiVariableBase)
        or end is None
    ):
        return None

    if isinstance(start, (_QiConstValue, QiCellProperty)):
        start = start.value
    if isinstance(end, (_QiConstValue, QiCellProperty)):
        end = end.value
    if isinstance(step, (_QiConstValue, QiCellProperty)):
        step = step.value

    end_val = start
    for _ in range(start, end, step):
        end_val += step
    return end_val


def _get_for_range_iterations(start, end, step):
    """Returns number of iterations of ForRange or None if start or end are QiVariables.
    Stupid but no need to check validity of input, in case of unrolled loop"""
    from .qi_var_definitions import QiCellProperty, _QiConstValue, _QiVariableBase

    if (
        isinstance(start, _QiVariableBase)
        or start is None
        or isinstance(end, _QiVariableBase)
        or end is None
    ):
        return None

    if isinstance(start, (_QiConstValue, QiCellProperty)):
        start = start.value
    if isinstance(end, (_QiConstValue, QiCellProperty)):
        end = end.value
    if isinstance(step, (_QiConstValue, QiCellProperty)):
        step = step.value

    iterations = 0
    for _ in range(start, end, step):
        iterations += 1
    return iterations
