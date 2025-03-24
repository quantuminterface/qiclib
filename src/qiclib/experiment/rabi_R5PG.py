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
"""This file contains the  experiment description for the QiController and R5 processor,
where manipulation waveforms are generated and loaded from R5."""

import numpy as np

import qiclib.packages.utility as util
from qiclib.coding.sequencercode import SequencerCode
from qiclib.experiment.base import BaseExperiment

# TODO improve pulsegen.c to make it able to do RabiDrag experiment
# So fat this class only generates rectangle or gauss shape pulse from R5


class RabiR5PG(BaseExperiment):
    def __init__(
        self,
        controller,
        duration_min=0,
        duration_max=1e-6,
        duration_step=24e-9,
        drag_amplitude=1,
    ):
        super().__init__(controller)
        self.durations = np.arange(duration_min, duration_max, duration_step)
        self._drag_amplitude = drag_amplitude
        if not self.qic.taskrunner_available:
            raise NotImplementedError("This experiment requires the Taskrunner to work")

    def _configure_sequences(self):
        # Duration of the pulse will be written into the delay registers
        code = SequencerCode()
        code.trigger_nco_sync()
        code.trigger_registered(1, manipulation=1)
        code.trigger_readout()
        code.end_of_experiment(self.qic.sample.T_rep)

        self.qic.sequencer.load_program(code)

    def _configure_taskrunner(self):
        # Make sure that taskrunner is used
        self.use_taskrunner = True
        self.qic.taskrunner.load_task_source("rabi_r5.c", "rabi-osc")

        duration_list = [
            util.conv_time_to_cycles(duration) for duration in self.durations
        ]

        # alpha is counted in maximum positive 16 bit values it will be devided back on the R5
        # TODO set a limitation value of alpha
        alpha = int(0x7FFF * self._drag_amplitude)

        parameters = [
            self.iteration_averages,
            alpha,
            len(self.durations),
            *duration_list,
        ]

        self.qic.taskrunner.set_param_list(parameters)

    def _record_internal(self):
        data = np.asarray(
            self._record_internal_taskrunner(
                len(self.durations) * self.iteration_averages, "Pulse-duration"
            )
        )
        data = data / (1.0 * self.iteration_averages * self.qic.sequencer.averages)
        return data[: len(self.durations)], data[len(self.durations) :]
