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

from qiclib.packages.grpc.datatypes_pb2 import *
from qiclib.packages.grpc.pulsegen_pb2 import *


class MockPulseGenServiceStub:
    def __init__(self, _):
        pass

    def GetNCOFrequency(self, _):
        return Frequency(cindex=EndpointIndex(value=0), value=10e3)

    def GetDuration(self, _):
        return Duration(value=1e-6)

    def GetStatusFlags(self, _):
        return StatusFlags()

    def ResetEnvelopeMemory(self, _):
        pass

    def LoadPulse(self, _):
        pass

    def SetNCOFrequency(self, _):
        pass


def patch():
    return mock.patch(
        "qiclib.packages.grpc.pulsegen_pb2_grpc.PulseGenServiceStub",
        new=MockPulseGenServiceStub,
    )
