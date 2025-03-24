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
"""This module contains the driver to access the Platform Information and Management
Core/Controller (PIMC) on the hardware platform.

The PIMC is an FPGA module designed to provide standardized access and recognition of
different hardware images. It provides an interface to query the status of the running
image, as well as to perform a global reset operation. The status also includes a
project and a platform ID to identify the built hardware image and the platform for
which it is intended. This information can later be used by other software components to
check for compatibility with the system (like this driver). It also provides information
of the build revision as well as the timestamp when the FPGA firmware was created.
A busy flag indicates if the platform is currently performing an operation.
A ready flag tells the user if the platform is fully initialized and ready to use.
This includes a check if all clocks are configured and running correctly, and if the
connection to the converters is established and working.
"""

import qiclib.packages.grpc.datatypes_pb2 as dt
import qiclib.packages.grpc.pimc_pb2 as proto
import qiclib.packages.grpc.pimc_pb2_grpc as grpc_stub
from qiclib.hardware.platform_component import PlatformComponent
from qiclib.packages.servicehub import ServiceHubCall

_PIMC_SUPPORTED_VERSIONS = {3, 4}


class PIMC(PlatformComponent):
    """Platform Information and Management Core/Controller (PIMC)

    This core provides information about the loaded project and the hardware used.
    """

    def __init__(
        self,
        name: str,
        connection,
        controller,
        qkit_instrument=True,
    ):
        super().__init__(name, connection, controller, qkit_instrument)
        self._stub = grpc_stub.PIMCServiceStub(self._conn.channel)
        self._info = self._get_info()

        if self.core_version not in _PIMC_SUPPORTED_VERSIONS:
            raise RuntimeError(
                "PIMC component not supported! "
                f"(Got {self.core_version}, but supported versions are {', '.join(map(str, sorted(_PIMC_SUPPORTED_VERSIONS)))})"
                " Maybe you have to use an older version of the Python client?"
            )

    @ServiceHubCall(
        errormsg="Could not read board information. "
        "Please make sure the board is connected."
    )
    def _get_info(self):
        return self._stub.GetInfo(dt.Empty())

    @property
    def core_version(self) -> int:
        """The version of the PIMC component."""
        return self._info.pimcVersion

    @property
    @ServiceHubCall(errormsg="Could not read Project information")
    def project(self) -> str:
        """Name of the Project running on the Platform"""
        return self._info.projectName

    @property
    def project_id(self) -> int:
        """The ID of the Project running on the Platform"""
        return self._info.projectId

    @property
    def platform_id(self) -> int:
        """The ID of the connected Platform"""
        return self._info.platformId

    @property
    def platform(self) -> str:
        """Name of the connected Platform"""
        return self._info.platformName

    @property
    def project_revision(self) -> str:
        """The revision of the running Project."""
        return self._info.buildCommit

    @property
    @ServiceHubCall(errormsg="Could not read Build Time")
    def build_time(self) -> str:
        """The build time of the running Project as string."""
        return self._info.buildTime

    @property
    @ServiceHubCall(errormsg="Could not obtain the status of the Platform")
    def status(self) -> proto.PIMCStatus:
        """Information about the status of the Platform.

        :return: A protobuf object containing the following properties:

            * rst_done: bool
                If a software reset was already called (necessary for some initializations)
            * ready: bool
                If the Platform is ready to use.
            * busy: bool
                If the Platform is currently busy.
        """
        return self._stub.GetStatus(dt.Empty())

    @property
    def is_ready(self) -> bool:
        """If the Platform is ready to use."""
        return self.status.ready

    @property
    def is_busy(self) -> bool:
        """If the Platform is currently busy."""
        return self.status.busy

    @property
    def reset_done_flag(self) -> bool:
        """If a software reset was already called (necessary for some initializations)."""
        return self.status.rst_done

    @ServiceHubCall(errormsg="Error resetting the Platform")
    def reset(self):
        """Resets the hardware part of the Platform."""
        self._stub.SetReset(dt.Empty())
