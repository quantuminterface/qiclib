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

import numpy as np

import qiclib.packages.utility as util
from qiclib.experiment.base import BaseExperiment


class RabiDRAG(BaseExperiment):
    r"""Rabi experiment driving the qubit between the states \|0> and \|1> using DRAG pulses.
    Outputs pulses at the qubit frequency of
    different duration and measures in which state the qubit is. Can be
    used to determine pulse duration for pi and pi/2 rotation pulses.

    .. warning::
        Readout pulse (on register 1) has to be configured separately!

    :param controller:
        The QiController driver
    :param duration_min:
        The minimum duration of the manipulation pulse
    :param duration_max:
        The maximum duration of the manipulation pulse
    :param duration_step:
        The increment of the duration between two iterations of the measurement
    :param drag_amplitude:
        DRAG amplitude
        (the default is 0, i.e. Gaussian pulses)
    """

    def __init__(
        self,
        controller,
        duration_min=0,
        duration_max=1e-6,
        duration_step=24e-9,
        drag_amplitude=0,
    ):
        super().__init__(controller)

        self.durations = np.arange(duration_min, duration_max, duration_step)
        self.drag_amplitude = drag_amplitude

    def _configure_drive_pulses(self):
        # The drive pulses will be loaded during the experiment so we dont have to do it here
        pass

    def _configure_sequences(self):
        self._built_code_from_sequences(
            {
                "normal": lambda code: (code.trigger_registered(1, manipulation=1)),
                "zero_pulse": lambda code: (code),
            }
        )

    def _record_internal(self):
        """
        This method describes the experimental procedure on the measurement pc.

        As multiple repetitions with different pulse durations are needed,
        this is handled here in a separate measurement routine.
        """
        if self.use_taskrunner:
            warnings.warn("Taskrunner mode is not (yet) supported by this experiment!")
            self.use_taskrunner = False

        return self._record_internal_1d(
            self.durations, "Durations", self._single_execution
        )

    def _single_execution(self, duration):
        # Reset pulse generator envelope memory
        self.qic.manipulation.reset_env_mem()
        # Generate new pulse
        pulse = util.generate_pulseform(duration, "end", self.drag_amplitude)
        if len(pulse) > 0:
            self.qic.manipulation.triggerset[1].load_pulse(pulse)
        return {
            "sequencer_start": self._pc_dict["zero_pulse"]
            if len(pulse) == 0
            else self._pc_dict["normal"],
            "delay_registers": [duration],
        }
