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
"""This file contains the IQCloudsRamsey experiment description for the QiController."""

import numpy as np

import qiclib.packages.constants as const
from qiclib.experiment.base import BaseExperiment


class ResonatorRingup(BaseExperiment):
    """Experiment performing a ramsey experiment with fixed *delay* between pi/2 pulses,
    performing many measurements and finally returning many single-shot results as IQCloud.

    :param controller:
        The QiController driver
    :param delay:
        The delay between the ramsey pi/2 pulses.
    :param count:
        The number of IQ points received (the default is 100k)
    """

    def __init__(
        self,
        controller,
        delays,
        recording_length=200e-9,
        pulse_offset=80e-9,
        recording_offset=0,
    ):
        super().__init__(controller)
        self.delays = delays
        self.recording_length = recording_length
        self.pulse_offset = pulse_offset
        self.recording_offset = recording_offset

        self.readout_reduction = 0
        self.reduction_delay = 0

    def _configure_sequences(self):
        # Amplitude reduction of readout pulse
        self.qic.readout.triggerset[4].load_pulse(
            np.ones(const.CONTROLLER_SAMPLES_PER_CYCLE) * (1 - self.readout_reduction),
            offset=self.reduction_delay,
            hold=True,
        )

        # Duration of the readout pulse is written into the delay register
        self.qic.sequencer.set_delay_register(1, delay=const.CONTROLLER_CYCLE_TIME)

        # Writing program for the sequencer & load it
        self._built_code_from_sequences(
            {
                "exp": lambda code: (
                    code
                    # TODO Why is here two on triggers?
                    .trigger_immediate(readout=self._r["Tone on"]["trigger"])
                    .trigger_registered(register=1, readout=4)
                    .trigger_recording(
                        delay=self.recording_length + self.pulse_offset, readout=0
                    )
                    .trigger_immediate(readout=self._r["Tone off"]["trigger"])
                )
            },
            add_readout=False,
        )

    def _record_internal(self):
        """
        This method describes the experimental procedure on the measurement pc.

        As multiple repetitions with different delays are needed,
        this is handled here in a separate measurement routine.
        """
        old_offset = self.qic.recording.trigger_offset
        old_reclen = self.qic.recording.recording_duration
        try:
            self.qic.recording.trigger_offset = self.recording_offset
            self.qic.recording.recording_duration = self.recording_length
            data = self._record_internal_1d(
                self.delays, "Recording delay", self._single_execution
            )
        finally:
            self.qic.recording.trigger_offset = old_offset
            self.qic.recording.recording_duration = old_reclen

        return data

    def _single_execution(self, delay):
        return {
            "sequencer_start": self._pc_dict["exp"],
            "delay_registers": [delay - const.CONTROLLER_CYCLE_TIME],
        }
