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

"""
The direct_rf addon board is an adaptor board for the ZCU216 board capable of generating
signals in various nyquist zones (Bands with various GHz of bandwidth).
This platform component is capable of choosing that nyquist zone and manually setting the attenuation
for ADC and DAC channels.
"""

import abc

import qiclib.packages.grpc.balunatten_pb2 as dt
import qiclib.packages.grpc.balunatten_pb2_grpc as grpc_stub
from qiclib.hardware.platform_component import PlatformComponent


class _Channel(abc.ABC):
    def __init__(self, stub: grpc_stub.BalUnAttenServiceStub, channel: dt.Channel):  # type: ignore
        self._channel = channel
        self._stub = stub

    @property
    def attenuation(self) -> float:
        return self._stub.GetAttenuation(self._channel).value

    @attenuation.setter
    def attenuation(self, value: float):
        """
        Sets the attenuation. Will be rounded to nearest .5 value.
        :param attenuation: 0..31.5 The attenuation in dB
        """
        self._stub.SetAttenuation(dt.Float(channel=self._channel, value=value))

    @property
    def nyquist(self) -> int:
        return self._stub.GetNyquist(self._channel).value

    @nyquist.setter
    def nyquist(self, value: int):
        """
        Sets the attenuation. Will be rounded to nearest .5 value.
        :param attenuation: 0..31.5 The attenuation in dB
        """
        self._stub.SwitchNyquist(dt.Number(channel=self._channel, value=value))

    def off(self):
        """
        Switch given ADC-channel off.
        """
        self._stub.SwitchOff(self._channel)


class AdcChannel(_Channel):
    def __init__(self, stub: grpc_stub.BalUnAttenServiceStub, chno: int):
        super().__init__(stub, dt.Channel(type=dt.Channel.Type.ADC, channel=chno))


class DacChannel(_Channel):
    def __init__(self, stub: grpc_stub.BalUnAttenServiceStub, chno: int):
        super().__init__(stub, dt.Channel(type=dt.Channel.Type.DAC, channel=chno))

    def switch_dc(self):
        """
        Sets this DAC to DC operation mode (can be understood as 0th nyquist zone).
        """
        self._stub.SwitchDC(self._channel)


class DirectRfAddon(PlatformComponent):
    """
    BalUnAtten is an RF frontend for the control and readout of cryogenic circuits via an SDR
    system, which can be controlled by an FPGA platform via GPIO. This plugin offers the most commonly
    used functionality (as defined in the original python scripts). So far, read back is not supported.

    Further details can be found at 'Valentin Stümpert. "A frontend for direct RF-synthesis on
    the basis of a ZCU216 board". Master thesis. Karlsruher Institut für Technologie, Feb. 2023'
    """

    def __init__(self, name: str, connection, controller, qkit_instrument=False):
        super().__init__(name, connection, controller, qkit_instrument)
        self._stub = grpc_stub.BalUnAttenServiceStub(self._conn.channel)

    def adc(self, number):
        return AdcChannel(self._stub, number)

    def dac(self, number):
        return DacChannel(self._stub, number)
