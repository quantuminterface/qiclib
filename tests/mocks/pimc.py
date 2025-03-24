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

from qiclib.packages.grpc.pimc_pb2 import *


class MockPIMCService:
    def __init__(self, _):
        pass

    def GetInfo(self, _):
        return Info(pimcVersion=4, projectId=3, platformId=0x23)


module = "qiclib.packages.grpc.pimc_pb2_grpc.PIMCServiceStub"


def patch():
    return mock.patch(module, new=MockPIMCService)
