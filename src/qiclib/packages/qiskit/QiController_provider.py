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

from typing import Callable

from qiskit.providers import ProviderV1 as Provider
from qiskit.providers.providerutils import filter_backends

from qiclib.packages.qiskit.QiController_backend import QiController_backend


def remove_duplicates(input_list):
    for element in input_list:
        for x in range(input_list.index(element), len(input_list) - 1):
            if (input_list[x] == element) or ([element[1], element[0]]):
                raise RuntimeError(
                    "Duplicated element: only add one coupling map per two qubits"
                )
    return input_list


class QiController_provider(Provider):
    """Provider for backends from the QiController hardware

    :ivar backend:
        Name of the backend
    :ivar sample:
        The sample object storing the backend properties for an experiment
    :ivar backends:
        List of backends supported by the QiController provider
    """

    def __init__(self, backend, sample, coupling_map=[]):
        super().__init__()
        self.backend = backend
        self.sample = sample
        self.coupling_map = remove_duplicates(coupling_map)
        self.backends = [QiController_backend(provider=self)]

    def backends(self, name=None, filters: Callable | None = None, **kwargs):
        """A listing of all backends from the QiController provider

        :param name:
            The name of a given backend

        :param filters:
            A filter function
        :param kwargs:
            A dictionary of other keyword arguments

        :return: A list of backends, if any

        """
        if name:
            backends = [backend for backend in self.backends if backend.name() == name]
        return filter_backends(backends, filters=filters, **kwargs)
