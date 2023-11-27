# Copyright © 2017-2023 Quantum Interface (quantuminterface@ipe.kit.edu)
# Lukas Scheller, IPE, Karlsruhe Institute of Technology
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
from unittest import mock

from qiclib.packages.grpc.qic_unitcell_pb2 import *


class MockUnitCellServiceStub:
    def __init__(self, _):
        pass

    def GetCellInfo(self, _):
        return CellInfo()

    def GetAllCellInfo(self, _):
        return AllCellInfo(cells=[CellInfo()])

    def GetConverterStatus(self, _):
        return ConverterStatus()

    def ClearConverterStatus(self, _):
        pass

    def RunExperiment(self, _):
        yield from (
            ExperimentResults(
                progress=prog,
                max_progress=10,
                finished=prog == 10,
                results=[
                    ExperimentResults.SingleCellResults(
                        data_double_1=[1, 2, 3], data_double_2=[4, 5, 6]
                    )
                ],
            )
            for prog in [0, 5, 10]
        )

    def GetBusyCells(self, _):
        return BusyCellInfo(busy=False)


def patch():
    return mock.patch(
        "qiclib.packages.grpc.qic_unitcell_pb2_grpc.UnitCellServiceStub",
        new=MockUnitCellServiceStub,
    )
