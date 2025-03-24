# Copyright© 2017-2023 Quantum Interface (quantuminterface@ipe.kit.edu)
# Cedric Becker, IPE, Karlsruhe Institute of Technology
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
from abc import ABC, abstractmethod


class DataProvider(ABC):
    """
    Provides uniform access to experiment result data.

    Result data is received either from the taskrunner plugin or the unit cell plugin and comes in different formats.
    This class encapsulates the format differences, to allow for further processing of the data to be handled
    independently.
    """

    @classmethod
    def create(cls, result, use_taskrunner: bool):
        if use_taskrunner:
            return _TaskrunnerDataProvider(result)
        return _InternalPluginDataProvider(result)

    def __init__(self, result):
        self._result = result

    @abstractmethod
    def get_raw_i(self, cell_index: int):
        pass

    @abstractmethod
    def get_raw_q(self, cell_index: int):
        pass

    def get_default_i(self, cell_index: int, index: int):
        return self.get_raw_i(cell_index)[index]

    def get_default_q(self, cell_index: int, index: int):
        return self.get_raw_q(cell_index)[index]

    def get_amp_pha_i(self, cell_index: int, index: int):
        return self.get_default_i(cell_index, index)

    def get_amp_pha_q(self, cell_index: int, index: int):
        return self.get_default_q(cell_index, index)

    @abstractmethod
    def get_iq_cloud_i(self, cell_index: int, index: int, recording_count: int):
        pass

    @abstractmethod
    def get_iq_cloud_q(self, cell_index: int, index: int, recording_count: int):
        pass

    def get_states(self, cell_index: int):
        return self._result[cell_index]

    def get_counts(self):
        return self.get_states(0)


class _TaskrunnerDataProvider(DataProvider):
    """
    Implements access to the experiment result data returned by the taskrunner
    """

    def get_raw_i(self, cell_index: int):
        return self._result[2 * cell_index]

    def get_raw_q(self, cell_index: int):
        return self._result[2 * cell_index + 1]

    def get_amp_pha_i(self, cell_index: int, index: int):
        return self._result[cell_index][0][index]

    def get_amp_pha_q(self, cell_index: int, index: int):
        return self._result[cell_index][1][index]

    def get_iq_cloud_i(self, cell_index: int, index: int, recording_count: int):
        return self._result[recording_count * cell_index + index][0::2]

    def get_iq_cloud_q(self, cell_index: int, index: int, recording_count: int):
        return self._result[recording_count * cell_index + index][1::2]


class _InternalPluginDataProvider(DataProvider):
    """
    Implements access to the experiment result data returned by the unit cell plugin
    """

    def get_raw_i(self, cell_index: int):
        return self._result[cell_index][0]

    def get_raw_q(self, cell_index: int):
        return self._result[cell_index][1]

    @staticmethod
    def _get_iq_cloud(data, index: int, recording_count: int):
        return data[
            index * (len(data) // recording_count) : (index + 1)
            * (len(data) // recording_count)
        ]

    def get_iq_cloud_i(self, cell_index: int, index: int, recording_count: int):
        data = self._result[cell_index][0]
        return self._get_iq_cloud(data, index, recording_count)

    def get_iq_cloud_q(self, cell_index: int, index: int, recording_count: int):
        data = self._result[cell_index][1]
        return self._get_iq_cloud(data, index, recording_count)
