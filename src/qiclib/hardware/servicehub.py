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
"""This module contains the driver to access the ServiceHub Control interface on the
hardware platform.

The ServiceHub Control Interface is a standardized interface to query which
functionalities are available within the current platform.
"""

from __future__ import annotations

import qiclib.packages.grpc.datatypes_pb2 as dt
import qiclib.packages.grpc.servicehubcontrol_pb2 as proto
import qiclib.packages.grpc.servicehubcontrol_pb2_grpc as grpc_stub
from qiclib.hardware.platform_component import PlatformComponent
from qiclib.packages.servicehub import ServiceHubCall


class ServiceHub(PlatformComponent):
    """ServiceHub Control Interface

    This interface provides information about the available functionalities.
    """

    def __init__(
        self,
        name: str,
        connection,
        controller,
        qkit_instrument=True,
    ):
        super().__init__(name, connection, controller, qkit_instrument)
        self._stub = grpc_stub.ServicehubControlServiceStub(self._conn.channel)
        self._info = self._get_version()

    @ServiceHubCall(
        errormsg="Could not read ServiceHub information. "
        "Please make sure that your connection is working!"
    )
    def _get_version(self):
        return self._stub.GetServiceHubVersion(dt.Empty())

    @property
    @ServiceHubCall(errormsg="Could not get list of loaded ServiceHub plugins")
    def plugin_list(self) -> list[str]:
        """A list of all loaded ServiceHub plugins."""
        return self._stub.GetPluginList(dt.Empty()).str

    @property
    def taskrunner_available(self) -> bool:
        """If the Taskrunner is available on the connected platform."""
        return "TaskRunnerPlugin" in self.plugin_list

    @property
    def has_rfdc(self) -> bool:
        """If the RF Data Converter is available on the connected platform."""
        return "TaskRunnerPlugin" in self.plugin_list

    @property
    def has_direct_rf(self) -> bool:
        """If the Direct RF plugin is available on the connected platform."""
        return "DirectRfPlugin" in self.plugin_list

    def reboot(self):
        """Reboots the whole platform."""
        self._stub.Reboot(dt.Empty())

    def get_endpoints_of_plugin(self, plugin: str) -> list[str]:
        return list(self._stub.GetEndpointsOfPlugin(proto.String(str=plugin)).str)

    def get_endpoint_index_from_plugin(self, plugin: str, endpoint: str) -> int:
        return self._stub.GetEndpointIndexOfPlugin(
            proto.EndpointIndexRequest(plugin_name=plugin, endpoint_name=endpoint)
        ).val
