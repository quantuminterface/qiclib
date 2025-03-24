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
"""Driver to control the Sequencer on the Hardware Platform."""

from collections.abc import Sequence

import qiclib.packages.grpc.datatypes_pb2 as dt
import qiclib.packages.grpc.sequencer_pb2 as proto
import qiclib.packages.grpc.sequencer_pb2_grpc as grpc_stub
from qiclib.hardware.platform_component import (
    PlatformComponent,
    platform_attribute,
    platform_attribute_collector,
)
from qiclib.packages.servicehub import ServiceHubCall


class _SequencerRegisters(Sequence):
    def __init__(self, endpoint: int, stub: grpc_stub.SequencerServiceStub):
        self._endpoint = endpoint
        self._stub = stub

    def get_all(self):
        """Returns a list with all 32bit unsigned int register values."""
        return self._stub.GetAllRegisters(dt.EndpointIndex(value=self._endpoint)).list

    def __len__(self):
        return 32

    def __getitem__(self, index):
        self._check_index(index)
        register_index = proto.RegisterIndex(endpoint=self._endpoint, index=index)
        return self._stub.GetRegister(register_index).value

    def __setitem__(self, index, value):
        self._check_index(index)
        register_index = proto.RegisterIndex(endpoint=self._endpoint, index=index)
        self._stub.SetRegister(proto.Register(index=register_index, value=value))

    def _check_index(self, index):
        if not isinstance(index, int) or index < 0:
            raise IndexError("Index needs to be a non-negative integer.")
        if index > 31:
            raise IndexError("Register index has to be between 0 and 31.")

    def _check_value(self, value):
        if not isinstance(value, int) or value < 0:
            raise IndexError("Value needs to be a non-negative integer.")
        if value >= 2**32:
            raise IndexError("Register value is limited to 32 bits.")

    def __str__(self):
        return "[" + ", ".join(map(str, self)) + "]"


@platform_attribute_collector
class Sequencer(PlatformComponent):
    """Driver to control the Sequencer on the Hardware Platform."""

    def __init__(
        self, name: str, connection, controller, qkit_instrument=True, index=0
    ):
        super().__init__(name, connection, controller, qkit_instrument)
        self._stub = grpc_stub.SequencerServiceStub(self._conn.channel)
        self._index = index
        self._component = dt.EndpointIndex(value=self._index)
        self._registers = _SequencerRegisters(self._index, self._stub)
        self._program_description = "Nothing loaded"

    @property
    def register(self):
        """The 32 registers of the Sequencer."""
        return self._registers

    @property
    @ServiceHubCall(errormsg="Failed to check if the Sequencer is busy")
    def busy(self):
        """If the sequencer is still busy.

        Readout should only be performed after sequencer has executed every command
        and reached the END command (will not be busy) waiting for the qubit to relax.
        """
        return self._stub.GetBusy(self._component).value

    @property
    @platform_attribute
    @ServiceHubCall(errormsg="Could not read the average count from the Sequencer")
    def averages(self):
        """The current count of repetitions done for averaging."""
        return self._stub.GetAverages(self._component).value

    @averages.setter
    @ServiceHubCall(errormsg="Could not set the average count in the Sequencer")
    def averages(self, averages):
        self._stub.SetAverages(proto.Average(index=self._component, value=averages))

    @property
    @ServiceHubCall(errormsg="Could not read the start address from the Sequencer")
    def start_address(self):
        """The position in the sequencer code where to start execution.

        This is most likely just the value of the last execution as it will
        be overwritten by the `startAt` method of the sequencer.
        """
        return self._stub.GetStartAddress(self._component).value

    @start_address.setter
    @ServiceHubCall(errormsg="Could not set the start address in the Sequencer")
    def start_address(self, start_address):
        self._stub.SetStartAddress(
            proto.ProgramCounter(index=self._component, value=start_address)
        )

    @property
    @ServiceHubCall(errormsg="Could not obtain the program counter in the Sequencer")
    def program_counter(self):
        """The current program counter as integer."""
        return self._stub.GetProgramCounter(self._component).value

    @ServiceHubCall(errormsg="Could not set the delay register of the Sequencer")
    def set_delay_register(self, register, delay=0, clock_cycles=0):
        """Sets the delay in seconds for the specified delay register.
        If delay is zero, a delay in clock cycles can be given as clock_cycles.

        :param register: int
            the delay register where the delay gets stored
        :parma delay: float, optional
            The delay in seconds, by default 0
        :param clock_cycles: int, optional
            The number of clock cycles, by default 0
        """
        self._stub.SetDelay(
            proto.Delay(
                index=self._component, reg=register, time=delay, cycles=clock_cycles
            )
        )

    def load_program(self, code, description="No Description"):
        """Loads the SequencerCode object into the Sequencer module on the Platform.

        :param code: SequencerCode
            The program data to write into the program memory.
        :param description: str, optional
            A string describing the program to load.
            Can be queried later on, by default "No Description"

        :raise ValueError:
            if the code is a string
        """
        if isinstance(code, str):
            raise ValueError(
                "Sequencer program needs to be passed as SequencerCode! Hex String format is deprecated."
            )
        # TODO Update all experiments to use the new format
        return self.load_program_code(code.to_command_values(), description)

    @ServiceHubCall(errormsg="Could not load the program onto the Sequencer")
    def load_program_code(self, program_data, description="No Description"):
        """Loads the program data into the sequencer module on the QiController.

        :param program_data:
            The program data (as list of command values) to write into the program memory.
        :param description:
            A string describing the program to load.
            Can be queried later on
        """
        self._stub.LoadProgram(
            proto.Program(
                index=self._component,
                program_data=program_data,
                description=description,
            )
        )
        # TODO Move description to server
        self._program_description = description

    @property
    @platform_attribute
    def program_description(self):
        return self._program_description

    @ServiceHubCall(errormsg="Could not start the Sequencer")
    def start_at(self, program_counter):
        """Sequencer gets started at the given program counter program_counter.

        :param program_counter: int
            The program counter at which the sequencer should start.
        """
        self._stub.StartAt(
            proto.ProgramCounter(index=self._component, value=program_counter)
        )

    @ServiceHubCall(errormsg="Could not resume the Sequencer operation")
    def resume(self):
        """Sequencer resumes after an END command with the next following command."""
        self._stub.Resume(self._component)

    @ServiceHubCall(errormsg="Could not reset the Sequencer")
    def reset(self):
        """Sequencer module gets resetted."""
        self._stub.Reset(self._component)

    @ServiceHubCall(errormsg="Could not stop the Sequencer")
    def stop(self):
        """Sequencer module gets stopped."""
        self._stub.Stop(self._component)

    def get_configuration_dict(self):
        configuration_dict = {
            "start_address": self.start_address,
            "averages": self.averages,
        }
        return configuration_dict

    @property
    def is_enabled(self) -> bool:
        return self._stub.IsEnabled(self._component).value

    @is_enabled.setter
    def is_enabled(self, value: bool):
        self._stub.SetEnabled(dt.IndexedBool(value=value, index=self._component))
