# Copyright© 2017-2023 Quantum Interface (quantuminterface@ipe.kit.edu)
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
from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Callable

import numpy as np

from .data_provider import DataProvider

if TYPE_CHECKING:
    from ...code.qi_jobs import QiCell, QiResult


class DataHandler(ABC):
    """
    Each subclass of this one handles a different way to process result data, depending on the type of experiment run.
    This usually includes splitting it up for the different boxes.
    It takes a list of cells and the recording data provider and processes it however it sees fit.
    In order to find out the box in which to store a recording it can access the `_result_recording_order` of a cell
    which provides the correct QiResult for the n-th executed recording.
    For examples, see the subclasses.

    :param data_provider: to access the experiments results
    :param cell_list: to store processed results there
    """

    @staticmethod
    def _data_handler_factories() -> (
        dict[str, Callable[[DataProvider, list[QiCell], int], DataHandler]]
    ):
        """
        This is a method instead of a static variable, because forward references to the subclasses are not possible in
        static variable assignments.
        """
        return {
            "average": lambda data_provider, cell_list, averages: _DefaultDataHandler(
                data_provider, cell_list
            ),
            "amp_pha": lambda data_provider,
            cell_list,
            averages: _AmplitudePhaseDataHandler(data_provider, cell_list),
            "iqcloud": lambda data_provider, cell_list, averages: _IQCloudDataHandler(
                data_provider, cell_list
            ),
            "raw": lambda data_provider, cell_list, averages: _RawDataHandler(
                data_provider, cell_list
            ),
            "states": _StateDataHandler,
            "counts": lambda data_provider, cell_list, averages: _CountDataHandler(
                data_provider, cell_list
            ),
            "quantum_jumps": lambda data_provider,
            cell_list,
            averages: _QuantumJumpsDataHandler(data_provider, cell_list),
            "custom": lambda data_provider,
            cell_list,
            averages: _NotImplementedDataHandler(data_provider, cell_list),
        }

    @staticmethod
    def names():
        return DataHandler._data_handler_factories().keys()

    @classmethod
    def get_factory_by_name(
        cls, name: str
    ) -> Callable[[DataProvider, list[QiCell], int], DataHandler] | None:
        factories = DataHandler._data_handler_factories()
        if name not in factories:
            return None
        return factories[name]

    @classmethod
    def get_custom_wrapper_factory(
        cls, custom_data_handler: Callable[[list[QiCell], DataProvider], None]
    ) -> Callable[[DataProvider, list[QiCell], int], DataHandler]:
        return lambda data_provider, cell_list, averages: _CustomDataHandlerWrapper(
            data_provider, cell_list, custom_data_handler
        )

    def __init__(self, data_provider: DataProvider, cell_list: list[QiCell]):
        self.data_provider = data_provider
        self.cell_list = cell_list

    @abstractmethod
    def process_results(self):
        pass


class _StandardDataHandler(DataHandler):
    def process_results(self):
        for cell_index, cell in enumerate(self.cell_list):
            count: int = cell.get_number_of_recordings()
            if count == 0:
                continue
            self.process_cell_results(cell_index, cell, count)

    @abstractmethod
    def process_cell_results(self, cell_index: int, cell: QiCell, count: int):
        pass


class _DefaultDataHandler(_StandardDataHandler):
    def process_cell_results(self, cell_index: int, cell: QiCell, count: int):
        distributed_result: dict[QiResult, tuple[list[Any], list[Any]]] = defaultdict(
            lambda: ([], [])
        )
        for i in range(count):
            box: QiResult = cell._result_recording_order[i]

            distributed_result[box][0].append(
                self.data_provider.get_default_i(cell_index, i)
            )
            distributed_result[box][1].append(
                self.data_provider.get_default_q(cell_index, i)
            )

        for box, values in distributed_result.items():
            box.data = [
                np.array(values[0], dtype=np.float64),
                np.array(values[1], dtype=np.float64),
            ]


class _AmplitudePhaseDataHandler(_StandardDataHandler):
    def process_cell_results(self, cell_index: int, cell: QiCell, count: int):
        distributed_result: dict[QiResult, tuple[list[Any], list[Any]]] = defaultdict(
            lambda: ([], [])
        )
        for i in range(count):
            box: QiResult = cell._result_recording_order[i]

            distributed_result[box][0].append(
                self.data_provider.get_amp_pha_i(cell_index, i)
            )
            distributed_result[box][1].append(
                self.data_provider.get_amp_pha_q(cell_index, i)
            )

        for box, values in distributed_result.items():
            box.data = [
                np.array(values[0], dtype=np.float64),
                np.array(values[1], dtype=np.float64),
            ]


class _RawDataHandler(_StandardDataHandler):
    def process_cell_results(self, cell_index: int, cell: QiCell, count: int):
        # Only one box relevant in raw mode (the one of last recording)
        box: QiResult = cell._result_recording_order[-1]
        box.data = [
            np.array(self.data_provider.get_raw_i(cell_index), dtype=np.float64),
            np.array(self.data_provider.get_raw_q(cell_index), dtype=np.float64),
        ]


class _IQCloudDataHandler(_StandardDataHandler):
    def process_cell_results(self, cell_index: int, cell: QiCell, count: int):
        distributed_result: dict[QiResult, list] = defaultdict(list)
        for i in range(count):
            box: QiResult = cell._result_recording_order[i]

            distributed_result[box].extend(
                (
                    self.data_provider.get_iq_cloud_i(cell_index, i, count),
                    self.data_provider.get_iq_cloud_q(cell_index, i, count),
                )
            )

        for box, values in distributed_result.items():
            box.data = values


class _StateDataHandler(_StandardDataHandler):
    def __init__(
        self, data_provider: DataProvider, cell_list: list[QiCell], averages: int
    ):
        super().__init__(data_provider, cell_list)
        self.averages = averages

    def process_cell_results(self, cell_index: int, cell: QiCell, count: int):
        # Each data box contains the states obtained from one cell
        # States are compressed as 3bits in 32bit unsigned integers
        data = [
            (value >> (3 * i)) & 0b111
            for value in self.data_provider.get_states(cell_index)
            for i in range(10)
        ][
            0 : self.averages  # Last value maybe only partially filled
        ]
        # There has to be only exactly one box.
        box: QiResult = cell._result_recording_order[0]
        box.data = data


class _CountDataHandler(_StandardDataHandler):
    def process_cell_results(self, cell_index: int, cell: QiCell, count: int):
        digits = sum(cell.get_number_of_recordings() > 0 for cell in self.cell_list)
        counts = {
            f"{i:0{digits}b}": count
            for i, count in enumerate(self.data_provider.get_counts())
        }
        # We store the same result in all cells that contributed
        # This mode counts the result of last executed recording.
        # Earlier recordings are ignored
        box: QiResult = cell._result_recording_order[-1]
        box.data = counts


class _QuantumJumpsDataHandler(_StandardDataHandler):
    def process_cell_results(self, cell_index: int, cell: QiCell, count: int):
        print(
            '\033[93m WARNING:\033[00m The data collection mode "quantum_jumps" has not yet been tested with '
            "a real qubit."
        )
        box = cell._result_recording_order[-1]
        box.data = self.data_provider.get_states(cell_index)  # state


class _NotImplementedDataHandler(DataHandler):
    def process_results(self):
        raise NotImplementedError("User needs to provide data handler for result data.")


class _CustomDataHandlerWrapper(DataHandler):
    def __init__(
        self,
        data_provider,
        cell_list: list[QiCell],
        custom_data_handler: Callable[[list[QiCell], DataProvider], None],
    ):
        super().__init__(data_provider, cell_list)
        self.custom_data_handler = custom_data_handler

    def process_results(self):
        self.custom_data_handler(self.cell_list, self.data_provider)
