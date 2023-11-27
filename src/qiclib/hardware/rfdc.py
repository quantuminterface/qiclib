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

ADCs and DACs contain a fine-tunable mixer that is implemented using a 48-bit NCO.
Obtain the current frequency of the NCO via the :meth:`RFDataConverter.get_mixer_frequency` method.
Using the :meth:`RFDataConverter.set_mixer_frequency`, the sampling frequency of a mixer can be changed.
The Frequency range is -Fs/2 to Fs/2.
"""
import sys
from dataclasses import dataclass

from qiclib.hardware.platform_component import PlatformComponent

from qiclib.packages.servicehub import ServiceHubCall
import qiclib.packages.grpc.rfdc_pb2 as proto
import qiclib.packages.grpc.rfdc_pb2_grpc as grpc_stub

from enum import Enum

from typing_extensions import Literal

ConverterType = Literal["adc", "dac"]


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


class InvSincFilterState(Enum):
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

    def _endpoint_index(self, converter_type: ConverterType, tile: int, block: int):
        if converter_type == "adc":
            proto_converter_type = proto.ConverterType.ADC
        elif converter_type == "dac":
            proto_converter_type = proto.ConverterType.DAC
        else:
            raise ValueError(
                f"Illegal converter choice {converter_type}. Must be 'dac' or 'adc'"
            )
        return proto.ConverterIndex(
            tile=tile, block=block, converter_type=proto_converter_type
        )

    @ServiceHubCall(errormsg="Could not reset RF data converter status")
    def reset_status(self):
        """Reset the status of the RF data converters.

        This is especially the ADC over voltage conditions.
        """
        self._stub.ResetStatus(proto.Empty())

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
        response = self._stub.ReportStatus(proto.Empty())
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

    @ServiceHubCall(errormsg="Could not obtain ADC block status")
    def adc_block_status(self, tile, block) -> ADCBlockStatus:
        """
        reports the status of an ADC

        :param tile:
            The tile of the ADC
        :param block:
            The block of the ADC

        :return:
            All relevant status information
        """
        index = self._endpoint_index("adc", tile, block)
        status = self._stub.GetBlockStatus(index)
        return ADCBlockStatus(
            sampling_frequency=status.frequency,
            enabled=bool(status.analogstatus & 0x1),
            fifo_status=status.digitalstatus & 0xF,
            decimation_factor=(status.digitalstatus & 0x0F) >> 4,
            mixer_mode=MixerMode((status.digitalstatus & 0x00F) >> 8),
            data_path_clocks_enabled=bool(status.clockstatus),
            fifo_flags_enabled=bool(status.fifoflagsenabled),
            fifo_flags_asserted=bool(status.fifoflagsasserted),
        )

    @ServiceHubCall(errormsg="Could not obtain DAC block status")
    def dac_block_status(self, tile, block) -> DACBlockStatus:
        """
        reports the status of a DAC

        :param tile:
            The tile of the DAC
        :param block:
            The block of the DAC

        :return:
            All relevant status information
        """
        index = self._endpoint_index("dac", tile, block)
        status = self._stub.GetBlockStatus(index)
        return DACBlockStatus(
            sampling_frequency=status.frequency,
            inv_sinc_status=InvSincFilterState(status.analogstatus & 0xF),
            decoder_mode=DecoderMode((status.analogstatus & 0x0F) >> 4),
            fifo_status=(status.digitalstatus & 0xF),
            interpolation_factor=(status.digitalstatus & 0x0F) >> 4,
            adder_status=(status.digitalstatus & 0x00F) >> 8,
            mixer_mode=MixerMode((status.digitalstatus & 0x000F) >> 12),
            data_path_clocks_enabled=bool(status.clockstatus),
            fifo_flags_enabled=bool(status.fifoflagsenabled),
            fifo_flags_asserted=bool(status.fifoflagsasserted),
        )

    @ServiceHubCall(errormsg="Could not obtain mixer frequency")
    def get_mixer_frequency(
        self, converter_type: ConverterType, tile: int, block: int
    ) -> float:
        """
        Get the internal mixer frequency.

        :param converter_type:
            The type; either "adc" or "dac"
        :param tile:
            The tile of the converter
        :param block:
            The block of the converter

        :return:
            The mixer frequency at that DAC or ADC in Hz

        """
        index = self._endpoint_index(converter_type, tile, block)
        return self._stub.GetMixerFrequency(index).value

    @ServiceHubCall(errormsg="Could not set mixer frequency")
    def set_mixer_frequency(
        self, converter_type: ConverterType, tile: int, block: int, frequency: float
    ):
        """
        Set the mixer frequency.
        The mixer frequency must be in the range `-Fs/2` to `Fs/2` where `Fs` is the sampling frequency.

        :param converter_type:
            The type; either "adc" or "dac"
        :param tile:
            The tile of the converter
        :param block:
            The block of the converter
        :param frequency:
            The frequency in Hz

        :return: The mixer frequency of the DAC or ADC

        """
        index = self._endpoint_index(converter_type, tile, block)
        self._stub.SetMixerFrequency(proto.Frequency(value=frequency, index=index))
