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

import warnings

import qiclib.packages.constants as const

from .resonator_ringup import ResonatorRingup


class ResonatorRingupWindow(ResonatorRingup):
    """Experiment performing a ramsey experiment with fixed *delay* between pi/2 pulses,
    performing many measurements and finally returning many single-shot results as IQCloud.

    .. warning::
        Readout pulse (on register 1) has to be configured separately!

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
        recording_lengths,
        delay=8e-9,
        pulse_offset=2080e-9,
        recording_offset=0,
    ):
        super().__init__(controller, [], 0, pulse_offset, recording_offset)
        self.recording_lengths = recording_lengths
        self.delay = delay

    def _record_internal(self):
        """
        This method describes the experimental procedure on the measurement pc.

        As multiple repetitions with different delays are needed,
        this is handled here in a separate measurement routine.
        """
        if self.use_taskrunner:
            warnings.warn("Taskrunner mode is not (yet) supported by this experiment!")
            self.use_taskrunner = False

        self.qic.sequencer.set_delay_register(
            1, self.delay - const.CONTROLLER_CYCLE_TIME
        )

        old_offset = self.qic.recording.trigger_offset
        old_reclen = self.qic.recording.recording_duration
        try:
            self.qic.recording.trigger_offset = self.recording_offset
            return self._record_internal_1d(
                self.recording_lengths, "Recording length", self._single_execution
            )
        finally:
            self.qic.recording.trigger_offset = old_offset
            self.qic.recording.recording_duration = old_reclen

    def _single_execution(self, delay):
        self.qic.recording.recording_duration = delay
        return {"sequencer_start": self._pc_dict["exp"], "delay_registers": []}
