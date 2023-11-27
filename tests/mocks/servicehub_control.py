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

from qiclib.packages.grpc.servicehubcontrol_pb2 import *


class MockServicehubControlService:
    def __init__(self, _):
        pass

    def GetServiceHubVersion(self, _):
        return ServiceHubVersions(
            servicehub_version="1.0-MOCK", proto_version="0.0", common_version="0.0"
        )

    def GetPluginList(self, _):
        return StringVector(str=["TaskRunnerPlugin"])


def patch():
    return mock.patch(
        "qiclib.packages.grpc.servicehubcontrol_pb2_grpc.ServicehubControlServiceStub",
        new=MockServicehubControlService,
    )
