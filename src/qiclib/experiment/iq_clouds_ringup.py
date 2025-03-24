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
"""This file contains the IQCloudsRingup experiment description for the QiController."""

from qiclib.experiment.iq_clouds import IQClouds


class IQCloudsRingup(IQClouds):
    """TODO Update description

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
        delay,
        count=1000,
        recording_length=200e-9,
        pulse_offset=80e-9,
        recording_offset=0,
    ):
        super().__init__(controller, 0, count)
        self.delay = delay
        self.recording_length = recording_length
        self.pulse_offset = pulse_offset
        self.recording_offset = recording_offset

    def _configure_sequences(self):
        # Duration of the readout pulse is written into the delay register
        self.qic.sequencer.set_delay_register(1, delay=self.delay)

        self._built_code_from_sequences(
            {
                "exp": lambda code: (
                    code.trigger_registered(
                        register=1, readout=self._r["Tone on"]["trigger"]
                    )
                    .trigger_readout(
                        delay=self.recording_length + self.pulse_offset, readout=0
                    )
                    .trigger_immediate(readout=self._r["Tone off"]["trigger"])
                )
            },
            add_readout=False,
        )

    def _record_internal(self):
        old_offset = self.qic.recording.trigger_offset
        old_reclen = self.qic.recording.recording_duration
        try:
            self.qic.recording.trigger_offset = self.recording_offset
            self.qic.recording.recording_duration = self.recording_length
            super()._record_internal()
        finally:
            self.qic.recording.trigger_offset = old_offset
            self.qic.recording.recording_duration = old_reclen
