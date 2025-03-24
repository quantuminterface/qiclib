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
"""This file contains the rabi experiment description for the QiController."""

import warnings

import qiclib.packages.utility as util
from qiclib.experiment.base import BaseExperiment


class SinglePulse(BaseExperiment):
    """Outputs a single pulse. Can be used to perform pseudo VNA scans.
    Also provides some extra methods to turn on/off a continuous pulse.

    .. deprecated::
        SinglePulse is deprecated. Please use the new QiCode syntax instead, see
        `qiclib.code`, i.e. write your own `qiclib.code.qi_jobs.QiJob`.

    :param controller:
        The QiController driver
    :param duration:
        The duration of the pulse
    """

    def __init__(self, controller, duration=24e-9, overlap=False):
        super().__init__(controller)
        self.duration = duration
        self.overlap = overlap
        warnings.warn(
            "SinglePulse is deprecated. Please use the new QiCode syntax instead, i.e. "
            "write your own `QiJob` or use a predefined one from `qiclib.jobs`.",
            FutureWarning,
        )

    def _record_internal(self):
        short_pulse = util.conv_time_to_cycles(self.duration, "ceil") < 2**8
        if self.drag_amplitude and (not short_pulse or self.overlap):
            raise RuntimeError(
                "Cannot generate DRAG pulses larger 1µs at the moment!"
                + " DRAG pulses are also not allowed to overlap right now..."
            )

        # Set duration if a varlength sequence is used
        self.qic.sequencer.set_delay_register(1, self.duration)

        if self.drag_amplitude:
            start_pc = self._pc_dict["default"]
        elif self.overlap:
            start_pc = self._pc_dict["varlength_overlap"]
        else:
            start_pc = self._pc_dict["varlength"]

        self.qic.sequencer.start_at(start_pc)
        return self._measure_amp_pha()

    def _configure_sequences(self):
        # Generating pulses to be loading into the manipulation pulse generator
        pulse = util.generate_pulseform(self.duration, "start", self.drag_amplitude)
        self.qic.manipulation.triggerset[10].load_pulse(pulse)

        self._built_code_from_sequences(
            {
                "default": lambda code: (
                    code.trigger_immediate(
                        delay=self.duration, manipulation=10
                    ).trigger_readout(self._readout_delay)
                ),
                # Longer pulses require registered trigger
                "varlength": lambda code: (
                    code.trigger_registered(
                        1, manipulation=self._p["Drive on"]["trigger"]
                    ).trigger_readout(
                        self._readout_delay,
                        manipulation=self._p["Drive off"]["trigger"],
                    )
                ),
                # Variation with manipulation until end of readout
                "varlength_overlap": lambda code: (
                    code.trigger_registered(
                        1, manipulation=self._p["Drive on"]["trigger"]
                    )
                    .trigger_readout(self._readout_delay)
                    .trigger_immediate(manipulation=self._p["Drive off"]["trigger"])
                ),
                # Additional code for manually starting and ending (infinite) pulses
                "start_manip": lambda code: code.trigger_immediate(
                    manipulation=self._p["Drive on"]["trigger"]
                ),
                "stop_manip": lambda code: code.trigger_immediate(
                    manipulation=self._p["Drive off"]["trigger"]
                ),
                "start_readout": lambda code: code.trigger_immediate(
                    readout=self._r["Tone on"]["trigger"]
                ),
                "stop_readout": lambda code: code.trigger_immediate(
                    readout=self._r["Tone off"]["trigger"]
                ),
                "start_both": lambda code: code.trigger_immediate(
                    manipulation=self._p["Drive on"]["trigger"],
                    readout=self._r["Tone on"]["trigger"],
                ),
                "stop_both": lambda code: code.trigger_immediate(
                    manipulation=self._p["Drive off"]["trigger"],
                    readout=self._r["Tone off"]["trigger"],
                ),
            },
            add_readout=False,
        )

    def start_pulse(self, pulsegen="manip"):
        """Starts a continuous pulse at the given *pulsegen* (readout/manip).

        Do not forget to call configure() in advance to setup the QiController.

        """
        self._do_pulse(pulsegen, "start")

    def stop_pulse(self, pulsegen="manip"):
        """Stops a continuous pulse at the given *pulsegen* (readout/manip).

        Do not forget to call configure() in advance to setup the QiController.

        """
        self._do_pulse(pulsegen, "stop")

    def _do_pulse(self, pulsegen="manip", action="start"):
        if action not in ["start", "stop"]:
            raise Warning("action must be either start or stop.")
        # TODO NCO Disable should be after sequencer!
        if pulsegen == "manip":
            self.qic.manipulation.nco_enable(action == "start")
        elif pulsegen == "readout":
            self.qic.readout.nco_enable(action == "start")
        elif pulsegen == "both":
            self.qic.manipulation.nco_enable(action == "start")
            self.qic.readout.nco_enable(action == "start")
        else:
            raise Warning("pulsegen must be either manip, readout or both.")
        self.qic.sequencer.start_at(self._pc_dict[f"{action}_{pulsegen}"])
