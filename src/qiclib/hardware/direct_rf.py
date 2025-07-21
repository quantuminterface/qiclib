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

import abc
from typing import TYPE_CHECKING, Literal

import google.protobuf.wrappers_pb2 as wrappers

import qiclib.packages.grpc.direct_rf_pb2 as dt
import qiclib.packages.grpc.direct_rf_pb2_grpc as grpc_stub
from qiclib.hardware.platform_component import PlatformComponent
from qiclib.hardware.rfdc import ADC, DAC

if TYPE_CHECKING:
    from qiclib.hardware.controller import QiController


class _Channel(abc.ABC):
    def __init__(
        self,
        controller: QiController,
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
        return self._stub.GetAttenuation(self._index).value

    @attenuation.setter
    def attenuation(self, new_value: float):
        self._stub.SetAttenuation(dt.IndexedDouble(index=self._index, value=new_value))


class OutputChannel(_Channel):
    def __init__(
        self,
        controller: QiController,
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
    def analog_data_path(self) -> str:
        setting = self._stub.GetDacAnalogDataPath(
            wrappers.UInt32Value(value=self._channel)
        ).setting
        return {
            dt.DacAnalogPath.Setting.OFF: "off",
            dt.DacAnalogPath.Setting.NYQUIST_1: "nz1",
            dt.DacAnalogPath.Setting.NYQUIST_2: "nz2",
            dt.DacAnalogPath.Setting.DC: "dc",
        }[setting]

    @analog_data_path.setter
    def analog_data_path(
        self, new_value: Literal["off", "nz1", "nz2", "dc"] | Literal[1, 2]
    ):
        if new_value == 1:
            setting = dt.DacAnalogPath.Setting.NYQUIST_1
        elif new_value == 2:
            setting = dt.DacAnalogPath.Setting.NYQUIST_2
        else:
            if isinstance(new_value, int):
                raise ValueError(f"Nyquist zone must be 0 or 1, was {new_value}")
            setting = {
                "off": dt.DacAnalogPath.Setting.OFF,
                "nz1": dt.DacAnalogPath.Setting.NYQUIST_1,
                "nz2": dt.DacAnalogPath.Setting.NYQUIST_2,
                "dc": dt.DacAnalogPath.Setting.DC,
            }[new_value.lower()]
        self._stub.SetDacAnalogDataPath(
            dt.DacAnalogPath(index=self._index.index, setting=setting)
        )


class InputChannel(_Channel):
    def __init__(
        self,
        controller: QiController,
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
    def analog_data_path(self) -> str:
        setting = self._stub.GetAdcAnalogDataPath(
            wrappers.UInt32Value(value=self._channel)
        ).setting
        return {
            dt.AdcAnalogPath.Setting.OFF: "off",
            dt.AdcAnalogPath.Setting.NYQUIST_1: "nz1",
            dt.AdcAnalogPath.Setting.NYQUIST_2: "nz2",
            dt.AdcAnalogPath.Setting.NYQUIST_6: "nz6",
            dt.AdcAnalogPath.Setting.NYQUIST_7: "nz7",
        }[setting]

    @analog_data_path.setter
    def analog_data_path(
        self,
        new_value: Literal["off", "nz1", "nz2", "nz6", "nz7"] | Literal[1, 2, 6, 7],
    ):
        if new_value == 1:
            setting = dt.AdcAnalogPath.Setting.NYQUIST_1
        elif new_value == 2:
            setting = dt.AdcAnalogPath.Setting.NYQUIST_2
        elif new_value == 6:
            setting = dt.AdcAnalogPath.Setting.NYQUIST_6
        elif new_value == 7:
            setting = dt.AdcAnalogPath.Setting.NYQUIST_7
        else:
            if isinstance(new_value, int):
                raise ValueError(f"Nyquist zone must be 1, 2, 6, or 7, was {new_value}")
            setting = {
                "off": dt.AdcAnalogPath.Setting.OFF,
                "nz1": dt.AdcAnalogPath.Setting.NYQUIST_1,
                "nz2": dt.AdcAnalogPath.Setting.NYQUIST_2,
                "nz6": dt.AdcAnalogPath.Setting.NYQUIST_6,
                "nz7": dt.AdcAnalogPath.Setting.NYQUIST_7,
            }[new_value.lower()]
        self._stub.SetAdcAnalogDataPath(
            dt.AdcAnalogPath(index=self._index.index, setting=setting)
        )


class DirectRf(PlatformComponent):
    def __init__(
        self, name: str, connection, controller: QiController, qkit_instrument=False
    ):
        super().__init__(name, connection, controller, qkit_instrument)
        self._stub = grpc_stub.DirectRfServiceStub(self._conn.channel)

    def output_channel(self, number):
        return OutputChannel(self._qip, self._stub, number)

    def input_channel(self, number):
        return InputChannel(self._qip, self._stub, number)
