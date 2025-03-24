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
import functools

import grpc
import wrapt


class Connection:
    def __init__(self, ip="0.0.0.0", port=50058, silent=False):
        self.ip = ip
        self.port = port
        self.grpc_connection = f"{self.ip}:{self.port}"
        self._silent = silent
        self._channel = None
        self._open = False
        self.open()

    def open(self):
        """Opens the connection to the platform."""
        if self._channel is not None:
            self.close()
        self._channel = grpc.insecure_channel(self.grpc_connection)
        if not self._silent:
            print(f"Establishing gRPC connection to {self.grpc_connection}...")
        self._open = True

    def close(self):
        """Closes the connection to the platform."""
        self._channel.close()
        del self._channel
        self._channel = None  # type: grpc.Channel
        if not self._silent:
            print(f"Closed gRPC connection to {self.grpc_connection}.")
        self._open = False

    @property
    def channel(self):
        """The gRPC connection channel to the platform."""
        return self._channel if self._open else None

    @property
    def is_open(self):
        """If the gRPC connection to the platform is open."""
        return self._open


def ServiceHubCall(call=None, errormsg="Error executing command", tries=5):
    if call is None:
        return functools.partial(ServiceHubCall, errormsg=errormsg, tries=tries)

    @wrapt.decorator
    def call_wrapper(call, instance, args, kwargs):
        if instance is None:
            instance = args[0]
        if not instance._conn.is_open:
            raise RuntimeError("No connection! Create a new QiController instance.")
        for attempt in range(tries):
            try:
                return call(*args, **kwargs)
            except grpc.RpcError as error:
                code = error.code()  # pylint: disable=no-member
                details = error.details()  # pylint: disable=no-member
                if code == grpc.StatusCode.NOT_FOUND:
                    raise  # No retry
                if code == grpc.StatusCode.INVALID_ARGUMENT:
                    raise ValueError(details) from error
                if code == grpc.StatusCode.UNIMPLEMENTED:
                    raise NotImplementedError(details) from error

                if attempt < tries - 1:
                    print(f"Internal Error. Retry {attempt+1} of {tries-1}...")
            raise RuntimeError(f"{errormsg} ({code}). Error message:\n{details}")

    return call_wrapper(call)  # pylint: disable=no-value-for-parameter
