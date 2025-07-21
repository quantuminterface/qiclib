# Copyright© 2017-2023 Quantum Interface (quantuminterface@ipe.kit.edu)
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
"""This module contains the drivers to interface with the RF data converters (ADCs/DACs)
on the QiController.

Sampling Frequency
==================

While not usually the case, the sampling frequency `Fs` can be different based on any given converter.
It can be obtained using the :python:`sampling_frequency` field in the objects returned by the
:meth:`RFDataConverter.adc_block_status` and :meth:`RFDataConverter.dac_block_status` methods.

Mixing Capabilities
===================

ADCs and DACs contain a fine-tunable mixer implemented using a 48-bit NCO.
Obtain the current frequency of the NCO via the :meth:`RFDataConverter.get_mixer_frequency` method.
Using the :meth:`RFDataConverter.set_mixer_frequency`, the sampling frequency of a mixer can be changed.
The Frequency range is -Fs/2 to Fs/2.
"""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Literal

import qiclib.packages.grpc.datatypes_pb2 as dt
import qiclib.packages.grpc.rfdc_pb2 as proto
import qiclib.packages.grpc.rfdc_pb2_grpc as grpc_stub
from qiclib.hardware.platform_component import PlatformComponent
from qiclib.packages.servicehub import ServiceHubCall


class MixerMode(Enum):
    """
    Represents possible mixer modes.
    """

    OFF = 0
    """
    The mixer is turned off
    """
    COMPLEX_TO_COMPLEX = 1
    """
    The mixer is in complex-to-complex mode, i.e. mixes IQ signals to IQ signals
    """
    COMPLEX_TO_REAL = 2
    """
    The mixer is in complex-to-real mode, i.e. mixes IQ signals to a real signal
    """
    REAL_TO_COMPLEX = 3
    """
    The mixer is in real-to-complex mode, i.e. mixes real signals to IQ signals
    """

    @staticmethod
    def from_str(value: str) -> MixerMode:
        value_lower = value.lower()
        if value_lower == "off":
            return MixerMode.OFF
        if value_lower == "c2c":
            return MixerMode.COMPLEX_TO_COMPLEX
        if value_lower == "c2r":
            return MixerMode.COMPLEX_TO_REAL
        if value_lower == "r2c":
            return MixerMode.REAL_TO_COMPLEX
        raise ValueError(
            f"Mixer mode as string must be 'off', 'c2c' (complex to complex), 'c2r' (complex to real) or 'r2c' (real to complex), not {value}"
        )


class InvSincFilterState(Enum):
    """
    Normally, the output spectrum of the RF-DAC used in the RFdc has a sin(x)/x characteristic.
    If a flat-output response is desired, the inverse sinc filter can be enabled.
    See more at the `official documentation <https://docs.xilinx.com/r/en-US/pg269-rf-data-converter/RF-DAC-Inverse-Sinc-Filter>`_
    """

    DISABLED = 0
    """
    No inverse sinc filter is implemented
    """
    FIRST_NYQUIST = 1
    """
    The inverse sinc filter is active for the first nyquist zone
    """
    SECOND_NYQUIST = 2
    """
    The inverse sinc filter is active for the second nyquist zone.
    Note that this is only available for Gen3 / DFE devices (i.e. only for the ZCU216 platform)
    """

    def is_on(self) -> bool:
        return self != InvSincFilterState.DISABLED


class DecoderMode(Enum):
    """
    Inside the RFdc, a trade-off can be chosen between maximizing the SNR or the linearity.
    """

    UNSET = 0
    MAX_SNR = 1
    """
    Optimize for the highest possible Signal-to Noise Ratio
    """
    MAX_LINEARITY = 2
    """
    Optimize for the best linearity
    """


@dataclass
class ADCBlockStatus:
    """
    Dataclass containing status information about an ADC
    """

    sampling_frequency: float
    """
    The sampling frequency in GHz
    """
    enabled: bool
    fifo_status: int
    decimation_factor: int
    mixer_mode: MixerMode
    data_path_clocks_enabled: bool
    fifo_flags_enabled: bool
    fifo_flags_asserted: bool


@dataclass
class DACBlockStatus:
    """
    Dataclass containing status information about a DAC
    """

    sampling_frequency: float
    """
    The sampling frequency in GHz
    """
    inv_sinc_status: InvSincFilterState
    decoder_mode: DecoderMode
    fifo_status: int
    interpolation_factor: int
    adder_status: int
    mixer_mode: MixerMode
    data_path_clocks_enabled: bool
    fifo_flags_enabled: bool
    fifo_flags_asserted: bool


class Tile(ABC):
    def __init__(self, stub: grpc_stub.RFdcServiceStub, tile: int):
        self._stub = stub
        self.tile = tile

    @abstractmethod
    def _endpoint_index(self) -> proto.TileIndex:  # type: ignore
        pass

    def shut_down(self):
        self._stub.Shutdown(self._endpoint_index())

    def start_up(self):
        self._stub.StartUp(self._endpoint_index())

    def reset(self):
        self._stub.Reset(self._endpoint_index())


class DacTile(Tile):
    def _endpoint_index(self):
        return proto.TileIndex(tile=self.tile, converter_type=proto.ConverterType.DAC)


class AdcTile(Tile):
    def _endpoint_index(self):
        return proto.TileIndex(tile=self.tile, converter_type=proto.ConverterType.ADC)


class DataConverter(ABC):
    def __init__(self, stub: grpc_stub.RFdcServiceStub, tile: int, block: int):
        self._stub = stub
        self.tile = tile
        self.block = block

    @abstractmethod
    def _endpoint_index(self) -> proto.ConverterIndex:  # type: ignore
        pass

    @property
    def mixer_frequency(self) -> float:
        """
        Get the internal mixer frequency.

        :return:
            The mixer frequency at that DAC or ADC in Hz

        """
        return self._stub.GetMixerFrequency(self._endpoint_index()).value

    @mixer_frequency.setter
    def mixer_frequency(self, frequency: float):
        """
        Set the mixer frequency.
        The mixer frequency must be in the range `-Fs/2` to `Fs/2` where `Fs` is the sampling frequency.

        :param frequency:
            The frequency in Hz

        :return: The mixer frequency of the DAC or ADC

        """
        self._stub.SetMixerFrequency(
            proto.Frequency(value=frequency, index=self._endpoint_index())
        )

    @property
    def frequency_resolution(self):
        """
        Returns the frequency resolution of the mixers of this converter.
        """
        return self._stub.GetFrequencyResolution(self._endpoint_index()).value

    @property
    def mixer_phase(self) -> float:
        """
        Get the phase of the mixer

        :return:
            The mixer's phase in ?
        """
        return self._stub.GetPhase(self._endpoint_index()).value

    @mixer_phase.setter
    def mixer_phase(self, phase: float):
        """
        Set the phase of the mixer

        :param phase:
            The mixer's phase in ?
        """
        self._stub.SetPhase(proto.Phase(value=phase, index=self._endpoint_index()))

    @property
    def mixer_mode(self) -> MixerMode:
        """
        Get the mixer mode.
        If the mixer mode is not MixerMode.OFF, for
        - DACs, this is either MixerMode.COMPLEX_TO_COMPLEX or MixerMode.COMPLEX_TO_REAL
        - ADCs, this is either MixerMode.COMPLEX_TO_COMPLEX or MixerMode.REAL_TO_COMPLEX

        If the mode is MixerMode.COMPLEX_TO_COMPLEX, two DACs or ADCs (always neighboring) are used.
        Otherwise, one ADC and one DAC is used.

        :return:
            The mode tha the DAC currently operates at

        """
        return MixerMode(self._stub.GetMixerMode(self._endpoint_index()).mode)

    @mixer_mode.setter
    def mixer_mode(self, new_value: MixerMode | Literal["c2c", "c2r", "r2c"]):
        if isinstance(new_value, str):
            mm = MixerMode.from_str(new_value)
        else:
            mm = new_value

        if mm == MixerMode.OFF:
            raise ValueError(
                "Cannot disable the signal. Either remove the output signal or shut down the tile."
            )

        typ = self._endpoint_index().converter_type

        # disallow real to complex and complex to real for invalid converter types
        if typ == proto.ConverterType.DAC and mm == MixerMode.REAL_TO_COMPLEX:
            raise ValueError("real to complex is not supported for DACs")

        if typ == proto.ConverterType.ADC and mm == MixerMode.COMPLEX_TO_REAL:
            raise ValueError("complex to real is not supported for ADCs")

        self._stub.SetMixerMode(
            proto.IndexedMode(index=self._endpoint_index(), mode=mm.value)
        )

    @property
    def nyquist_zone(self) -> int:
        return self._stub.GetNyquistZone(self._endpoint_index()).value

    @nyquist_zone.setter
    def nyquist_zone(self, zone: int):
        self._stub.SetNyquistZone(
            proto.NyquistZone(index=self._endpoint_index(), value=zone)
        )


class DAC(DataConverter):
    def _endpoint_index(self) -> proto.ConverterIndex:  # type: ignore
        return proto.ConverterIndex(
            tile=self.tile, block=self.block, converter_type=proto.ConverterType.DAC
        )

    @property
    def output_current(self) -> float:
        return self._stub.GetOutputCurrent(self._endpoint_index())

    @output_current.setter
    def output_current(self, value: float):
        self._stub.SetOutputCurrent(
            proto.IndexedDouble(index=self._endpoint_index(), value=value)
        )

    @property
    def status(self) -> DACBlockStatus:
        """
        reports the status of a DAC

        :return:
            All relevant status information
        """
        status = self._stub.GetBlockStatus(self._endpoint_index())
        return DACBlockStatus(
            sampling_frequency=status.frequency,
            inv_sinc_status=InvSincFilterState(status.analogstatus & 0xF),
            decoder_mode=DecoderMode((status.analogstatus & 0x0F) >> 4),
            fifo_status=(status.digitalstatus & 0xF),
            interpolation_factor=(status.digitalstatus & 0x0F) >> 4,
            adder_status=(status.digitalstatus & 0x00F) >> 12,
            mixer_mode=MixerMode((status.digitalstatus & 0xF000) >> 12),
            data_path_clocks_enabled=bool(status.clockstatus),
            fifo_flags_enabled=bool(status.fifoflagsenabled),
            fifo_flags_asserted=bool(status.fifoflagsasserted),
        )

    @property
    def inv_sinc_filter(self) -> InvSincFilterState:
        proto_state = self._stub.GetInvSincFIR(
            proto.InvSincFIR(index=self._endpoint_index())
        ).value
        if proto_state == proto.InvSincFIR_Enum.DISABLED:
            return InvSincFilterState.DISABLED
        elif proto_state == proto.InvSincFIR_Enum.FIRST_NYQUIST:
            return InvSincFilterState.FIRST_NYQUIST
        elif proto_state == proto.InvSincFIR_Enum.SECOND_NYQUIST:
            return InvSincFilterState.SECOND_NYQUIST
        else:
            raise ValueError(f"Illegal state {proto_state} returned from protobuf call")


class ADC(DataConverter):
    def _endpoint_index(self) -> proto.ConverterIndex:  # type: ignore
        return proto.ConverterIndex(
            tile=self.tile, block=self.block, converter_type=proto.ConverterType.ADC
        )

    @property
    def status(self) -> ADCBlockStatus:
        """
        reports the status of this ADC

        :return:
            All relevant status information
        """
        status = self._stub.GetBlockStatus(self._endpoint_index())
        return ADCBlockStatus(
            sampling_frequency=status.frequency,
            enabled=bool(status.analogstatus & 0x1),
            fifo_status=status.digitalstatus & 0xF,
            decimation_factor=(status.digitalstatus & 0x0F) >> 4,
            mixer_mode=MixerMode((status.digitalstatus & 0xF00) >> 8),
            data_path_clocks_enabled=bool(status.clockstatus),
            fifo_flags_enabled=bool(status.fifoflagsenabled),
            fifo_flags_asserted=bool(status.fifoflagsasserted),
        )

    @property
    def attenuation(self) -> float:
        return self._stub.GetDigitalAttenuation(self._endpoint_index()).value

    @attenuation.setter
    def attenuation(self, value: float):
        return self._stub.SetDigitalAttenuation(
            proto.IndexedDouble(index=self._endpoint_index(), value=value)
        )


class RFDataConverter(PlatformComponent):
    """
    Driver to interface with the RF data converters (ADCs/DACs) on the QiController.

    The ADCs and DACs are organized in tiles and blocks. Most functions accept that tile and block as argument.
    """

    def __init__(
        self,
        name: str,
        connection,
        controller,
        qkit_instrument=True,
    ):
        super().__init__(name, connection, controller, qkit_instrument)
        self._stub = grpc_stub.RFdcServiceStub(self._conn.channel)

    def dac(self, tile: int, block: int) -> DAC:
        """
        Get a reference to a DAC at a certain tile and block index.

        Using the returned object, properties of the corresponding DAC can be set
        that will be updated on the QiController.
        """
        return DAC(self._stub, tile, block)

    def adc(self, tile: int, block: int) -> ADC:
        """
        Get a reference to an ADC ar a certain tile and block index.

        Using the returned object, properties of the corresponding ADC can be set
        that will be updated on the QiController.
        """
        return ADC(self._stub, tile, block)

    def dac_tile(self, tile: int) -> DacTile:
        """
        Get a reference to a DAC tile

        Using the returned object, properties of the corresponding DAC tile can be set
        and will be updated on the QiController.

        :param tile: The tile number
        """
        return DacTile(self._stub, tile)

    def adc_tile(self, tile: int) -> AdcTile:
        """
        Get a reference to an ADC tile

        Using the returned object, properties of the corresponding ADC tile can be set
        and will be updated on the QiController.

        :param tile: The tile number
        """
        return AdcTile(self._stub, tile)

    @ServiceHubCall(errormsg="Could not reset RF data converter status")
    def reset_status(self):
        """Reset the status of the RF data converters.

        This is especially the ADC over voltage conditions.
        """
        self._stub.ResetStatus(dt.Empty())

    @ServiceHubCall(errormsg="Could not check RF data converter status")
    def check_status(self, raise_exceptions: bool = True) -> bool:
        """Check if a converter reported an error and if so, forward it to the user.

        .. warning::
            Currently, this is not working as reliable as the information provided by the
            UnitCells, so better use this for the moment.

        :param raise_exceptions:
            if assigned status flags will result in an exception or just in a warning
            output

        :return:
            if everything is fine and no status flags have been raised.
        """
        response = self._stub.ReportStatus(dt.Empty())
        status_report = response.report

        if response.failure:
            self.reset_status()
            status_report = (
                "The data converters reported the following issue(s):\n" + status_report
            )
            if raise_exceptions:
                raise Warning(status_report)
            sys.stderr.write(status_report)

        return not response.failure
