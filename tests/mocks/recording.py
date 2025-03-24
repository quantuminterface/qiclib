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
from qiclib.packages.grpc.recording_pb2 import *


class MockRecordingServiceStub:
    def __init__(self, _):
        pass

    def IsInterferometerMode(self, _):
        return InterferometerMode(index=EndpointIndex(value=0), is_interferometer=False)

    def GetInternalFrequency(self, _):
        return Frequency(index=EndpointIndex(value=0), value=30e6)

    def GetRecordingDuration(self, _):
        return RecordingDuration(index=EndpointIndex(value=0), value=1e-6)

    def GetTriggerOffset(self, _):
        return TriggerOffset(index=EndpointIndex(value=0), value=0)

    def GetInternalPhaseOffset(self, _):
        return PhaseOffset(index=EndpointIndex(value=0), value=0)

    def GetExpectedHighestSignalAmplitude(self, _):
        return Int(value=0)

    def GetAverageShift(self, _):
        return AverageShift(index=EndpointIndex(value=0), value=0)

    def GetAveragedResult(self, _):
        return IQResult(i_value=[1, 2, 3], q_value=[4, 5, 6])

    def ReportStatus(self, _):
        return StatusReport()

    def SetRecordingDuration(self, _):
        pass

    def SetTriggerOffset(self, _):
        pass

    def SetInternalFrequency(self, _):
        pass


def patch():
    return mock.patch(
        "qiclib.packages.grpc.recording_pb2_grpc.RecordingStub",
        new=MockRecordingServiceStub,
    )
