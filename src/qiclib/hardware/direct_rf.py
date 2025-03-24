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

import abc
from typing import TYPE_CHECKING

import qiclib.packages.grpc.direct_rf_pb2 as dt
import qiclib.packages.grpc.direct_rf_pb2_grpc as grpc_stub
from qiclib.hardware.direct_rf_addon import AdcChannel, DacChannel
from qiclib.hardware.platform_component import PlatformComponent
from qiclib.hardware.rfdc import ADC, DAC

if TYPE_CHECKING:
    from qiclib.hardware.controller import QiController


class _Channel(abc.ABC):
    def __init__(
        self,
        controller: "QiController",
        stub: grpc_stub.DirectRfServiceStub,
        channel: int,
        index: dt.ConverterIndex,  # type: ignore
    ) -> None:
        self._controller = controller
        self._channel = channel
        self._stub = stub
        self._index = index

    @property
    def frequency(self):
        return self._stub.GetFrequency(self._index).value

    @frequency.setter
    def frequency(self, new_frequency: float):
        self._stub.SetFrequency(
            dt.IndexedDouble(index=self._index, value=new_frequency)
        )

    @property
    def attenuation(self) -> float:
        return self._stub.GetAttenuation(self._index)

    @attenuation.setter
    def attenuation(self, new_value: float):
        self._stub.SetAttenuation(dt.IndexedDouble(index=self._index, value=new_value))


class OutputChannel(_Channel):
    def __init__(
        self,
        controller: "QiController",
        stub: grpc_stub.DirectRfServiceStub,
        channel: int,
    ) -> None:
        super().__init__(
            controller,
            stub,
            channel,
            dt.ConverterIndex(index=channel, type=dt.ConverterType.DAC),
        )

    @property
    def rf_dac(self) -> DAC:
        index = self._stub.ToRfdcIndex(self._index)
        return self._controller.rfdc.dac(index.tile, index.block)

    @property
    def board_channel(self) -> DacChannel:
        index = self._stub.ToChannelIndex(self._index)
        return self._controller.direct_rf_board.dac(index.value)


class InputChannel(_Channel):
    def __init__(
        self,
        controller: "QiController",
        stub: grpc_stub.DirectRfServiceStub,
        channel: int,
    ) -> None:
        super().__init__(
            controller,
            stub,
            channel,
            dt.ConverterIndex(index=channel, type=dt.ConverterType.ADC),
        )

    @property
    def rf_adc(self) -> ADC:
        index = self._stub.ToRfdcIndex(self._index)
        return self._controller.rfdc.adc(index.tile, index.block)

    @property
    def board_channel(self) -> AdcChannel:
        index = self._stub.ToChannelIndex(self._index)
        return self._controller.direct_rf_board.adc(index.value)


class DirectRf(PlatformComponent):
    def __init__(
        self, name: str, connection, controller: "QiController", qkit_instrument=False
    ):
        super().__init__(name, connection, controller, qkit_instrument)
        self._stub = grpc_stub.DirectRfServiceStub(self._conn.channel)

    def output_channel(self, number):
        return OutputChannel(self._qip, self._stub, number)

    def input_channel(self, number):
        return InputChannel(self._qip, self._stub, number)
