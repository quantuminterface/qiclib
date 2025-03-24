# Copyright© 2024 Quantum Interface (quantuminterface@ipe.kit.edu)
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
from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import numpy.typing as npt

import qiclib.packages.grpc.datatypes_pb2 as dt
import qiclib.packages.grpc.pulse_player_pb2 as proto
import qiclib.packages.grpc.pulse_player_pb2_grpc as grpc_stub
from qiclib.hardware.platform_component import (
    PlatformComponent,
    platform_attribute_collector,
)


@platform_attribute_collector
class PulsePlayer(PlatformComponent):
    """
    The pulse player is similar to the :class:`qiclib.hardware.pulsegen.PulseGen` component.
    The main difference is that this component stores real data and has no integrated digital up-conversion.
    The benefit is that this module can hold more samples than the :py:`PulseGen` component.
    """

    class _PulsesProxy:
        def __init__(self, pulse_player: PulsePlayer):
            self._player = pulse_player

        def __setitem__(self, key: int | slice | tuple, value: Sequence[float]):
            if isinstance(key, slice):
                start = key.start or 0
                stop = key.stop or 3
                step = key.step or 1
                for i in range(start, stop, step):
                    self[i] = value[i]
            elif isinstance(key, tuple):
                for i, pulse in zip(key, value):
                    self[i] = pulse
            else:
                self._player._stub.SetPulse(
                    proto.IndexedPulses(
                        index=self._player._index,
                        pulse=proto.Pulse(values=value, index=key),
                    )
                )

        def __getitem__(self, item: int | slice | tuple) -> npt.NDArray[np.float64]:
            if isinstance(item, slice):
                start = item.start or 0
                stop = item.stop or 4
                step = item.step or 1
                return np.array([self[i] for i in range(start, stop, step)])
            elif isinstance(item, tuple):
                return np.array([self[i] for i in item])
            else:
                return np.array(
                    self._player._stub.GetPulse(
                        proto.PulseIndex(index=self._player._index, pulse=item)
                    ).values
                )

    def __init__(
        self,
        name: str,
        connection,
        controller,
        index=0,
        qkit_instrument=True,
    ):
        super().__init__(name, connection, controller, qkit_instrument)
        self._pulses = PulsePlayer._PulsesProxy(self)
        self._stub = grpc_stub.PulsePlayerServiceStub(self._conn.channel)
        self._index = dt.EndpointIndex(value=index)
        self._triggerset: list[np.ndarray | None] = [None]

    @property
    def pulses(self) -> _PulsesProxy:
        """
        Returns a list-like object that can be used to assign pulses and read pulses.
        Pulses that are assigned to using the :py:`PulsePlayer.pulses[1] = np.array(...)`
        syntax are directly forwarded to the platform.
        Similarly, pulses read using the :py:`PulsePlayer.pulses[1]` syntax return a numpy array containing the pulses.

        Pulses are quantized on the platform.
        Arrays passed to this function are expected to be in the range (-1, 1).

        This function allows slicing and indexing multiple pulses.
        For example, the syntax :py:`PulsePlayer.pulses[:]` retrieves all pulses from the platform.
        """
        return self._pulses

    def reset(self):
        """
        Resets the pulse player and clears all pulses.
        """
        self._stub.Reset(self._index)

    def trigger(self, index: int):
        """
        Manually trigger a pulse.
        """
        self._stub.Trigger(proto.PulseIndex(index=self._index, pulse=index))

    @property
    def offset(self) -> float:
        """
        Get offset value.
        """
        getoffset = self._stub.GetOffset(self._index)
        return getoffset.offset_value

    @offset.setter
    def offset(self, offset_value: float):
        """
        Set offset value.
        """
        self._stub.SetOffset(proto.Offset(index=self._index, offset_value=offset_value))

    @property
    def pulse_capacity(self) -> int:
        """
        Returns the number of pulses this player can store. Note that the assignable amount is :py:`pulse_capacity - 1`.
        The first pulse is read-only and always empty.
        """
        return self._stub.GetPulseCapacity(self._index).value

    @property
    def sample_rate(self) -> float:
        """
        Returns the rate that this module samples pulses in Hz.
        """
        return self._stub.GetSampleRate(self._index).value
