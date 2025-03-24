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
"""Contains the Driver to control a Storage Module on the Hardware Platform.."""

import qiclib.packages.grpc.datatypes_pb2 as dt
import qiclib.packages.grpc.qic_storage_pb2 as proto
import qiclib.packages.grpc.qic_storage_pb2_grpc as grpc_stub
from qiclib.hardware.platform_component import PlatformComponent
from qiclib.packages.servicehub import ServiceHubCall


class Storage(PlatformComponent):
    """Driver to control a Storage Module on the Hardware Platform."""

    def __init__(
        self,
        name: str,
        connection,
        controller,
        qkit_instrument=True,
        index=0,
    ):
        super().__init__(name, connection, controller, qkit_instrument)
        self._stub = grpc_stub.StorageStub(self._conn.channel)
        self._index = index
        self._component = dt.EndpointIndex(value=self._index)

        self._bram = [
            _StorageBRAM(
                f"{self.name} Memory #{i}",
                self._conn,
                self._qip,
                qkit_instrument=False,
                index=i,
                storage=self,
            )
            for i in range(4)
        ]

    def extract_states(self, val, dense=False):
        if dense:
            return [(val >> i) & 0x1 for i in range(32)]
        else:
            return [((val) >> (3 * i)) & 0x7 for i in range(10)]

    @property
    @ServiceHubCall
    def reset(self):
        self._stub.Reset(self._component)

    @property
    @ServiceHubCall
    def state_handling(self):
        """Returns the current handling configuration of states, containing store enable, accumulate enable and the selected BRAM index"""
        handling = self._stub.GetStateHandling(self._component)
        return (
            handling.store,
            handling.accumulate,
            handling.dense_mode,
            handling.destination,
        )

    @state_handling.setter
    @ServiceHubCall
    def state_handling(self, state_handling):
        self._stub.SetStateHandling(
            proto.StateHandling(
                index=self._component,
                store=state_handling[0],
                accumulate=state_handling[1],
                dense_mode=state_handling[2],
                destination=state_handling[3],
            )
        )

    @property
    @ServiceHubCall
    def get_state_accumulation(self):
        """Returns up to 10 states accumulated in a register."""
        accumulation = self._stub.GetStateAccumulation(self._component)
        states = self.extract_states(accumulation.accu_states, self.state_handling[2])
        return states, accumulation.accu_counter

    @property
    @ServiceHubCall
    def result_handling(self):
        """Returns the current handling configuration of result data, containing the store enable flag and the selected BRAM index"""
        handling = self._stub.GetResultHandling(self._component)
        return (handling.store, handling.destination)

    @result_handling.setter
    @ServiceHubCall
    def result_handling(self, result_handling):
        self._stub.SetResultHandling(
            proto.ResultHandling(
                index=self._component,
                store=result_handling[0],
                destination=result_handling[1],
            )
        )

    @property
    @ServiceHubCall
    def averaged_handling(self):
        """Returns the current handling configuration of averaged data, containing the store enable flag and the selected BRAM index"""
        handling = self._stub.GetAveragedHandling(self._component)
        return (handling.store, handling.destination)

    @averaged_handling.setter
    @ServiceHubCall
    def averaged_handling(self, averaged_handling):
        self._stub.SetAveragedHandling(
            proto.AveragedHandling(
                index=self._component,
                store=averaged_handling[0],
                destination=averaged_handling[1],
            )
        )

    @property
    @ServiceHubCall
    def get_result_data(self):
        """Returns the I anf Q components of the result data."""
        result = self._stub.GetBramResultData(self._component)
        return result.result_i, result.result_q

    @property
    @ServiceHubCall
    def get_averaged_data(self):
        """Returns the averaged data."""
        return self._stub.GetBramAveragedData(self._component).averaged

    @property
    @ServiceHubCall
    def get_state_data(self):
        states_raw = self._stub.GetBramStateData(self._component).state
        _, accumulate, dense_mode, _ = self.state_handling
        if accumulate:
            states = []
            for x in states_raw:
                # Returns the state data.
                states.append(self.extract_states(x, dense_mode))
            return states
        else:
            return states_raw

    @property
    @ServiceHubCall
    def result_lost(self):
        """If single result data is lost due to full buffer."""
        return self._stub.IsDataLost(self._component).single_result

    @property
    @ServiceHubCall
    def accumulation_lost(self):
        """If accumulated state data is lost due to full buffer."""
        return self._stub.IsDataLost(self._component).state_accumulation

    @property
    @ServiceHubCall
    def state_lost(self):
        """If qubit state data is lost due to full buffer."""
        return self._stub.IsDataLost(self._component).qubit_state

    @property
    @ServiceHubCall
    def averaged_lost(self):
        """If averaged result data is lost due to full buffer."""
        return self._stub.IsDataLost(self._component).averaged_result

    @property
    @ServiceHubCall
    def sequencer_lost(self):
        """If data from the sequencer is lost due to full buffer."""
        return self._stub.IsDataLost(self._component).bram_input

    @property
    def memory(self):
        return self._bram

    def get_configuration_dict(self):
        configuration_dict = {
            "averaged_handling": self.averaged_handling,
            "result_handling": self.result_handling,
            "state_handling": self.state_handling,
        }
        return configuration_dict


class _StorageBRAM(PlatformComponent):
    """Single BRAM of the storage module."""

    def __init__(
        self,
        name: str,
        connection,
        controller,
        qkit_instrument,
        storage: Storage,
        index=0,
    ):
        super().__init__(name, connection, controller, qkit_instrument)
        self._storage: Storage = storage
        self._stub = self._storage._stub

        self._index = index
        self._indexset = proto.BramIndex(
            index=self._storage._component, bram=self._index
        )

    def reset(self):
        """Resets configuration and data of this memory block."""
        self.reset_config()
        self.reset_data()

    @ServiceHubCall
    def reset_config(self):
        """Resets the selected BRAM.

        .. note::
            This function only resets the BRAM to a default state, such that previous values can be
            overwritten beginning from the first address. To erase the BRAM data use reset_data.
        """
        self._stub.SetBramControl(
            proto.BramControl(index=self._storage._component, bram=self._index, reset=1)
        )

    @ServiceHubCall
    def reset_data(self):
        """Resets the state and erases data in the selected BRAM."""
        self._stub.ResetBramData(self._indexset)

    @ServiceHubCall
    def wrap(self, wrap_en):
        """Enables circular buffer for the selected BRAM."""
        self._stub.SetBramControl(
            proto.BramControl(
                index=self._storage._component, wrap=wrap_en, bram=self._index
            )
        )

    @property
    @ServiceHubCall
    def empty(self):
        """If the selected BRAM is empty."""
        return self._stub.GetBramStatus(self._indexset).empty

    @property
    @ServiceHubCall
    def full(self):
        """If the selected BRAM is full"""
        return self._stub.GetBramStatus(self._indexset).full

    @property
    @ServiceHubCall
    def overflow(self):
        """If an overflow happened in the selected BRAM"""
        return self._stub.GetBramStatus(self._indexset).overflow

    @property
    @ServiceHubCall
    def next_address(self):
        """Returns the next address of the selected BRAM"""
        return self._stub.GetBramStatus(self._indexset).next_address

    @property
    @ServiceHubCall
    def latest_data(self):
        """Returns the last data that was written into selected BRAM"""
        return self._stub.GetBramLatestData(self._indexset).data

    @ServiceHubCall
    def get_data_uint32(self):
        """Returns the data of the selected BRAM interpreted as an 32-Bit unsigned integer."""
        return self._stub.GetBramDataUInt32(self._indexset).data

    @ServiceHubCall
    def get_data_int32(self):
        """Returns the data of the selected BRAM interpreted as an 32-Bit signed integer."""
        return self._stub.GetBramDataInt32(self._indexset).data
