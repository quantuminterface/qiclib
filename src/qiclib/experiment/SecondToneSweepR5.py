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
import numpy as np

import qiclib.packages.utility as util
from qiclib.experiment.base import BaseExperiment


class SecondToneSweep_R5(BaseExperiment):
    def __init__(
        self, controller, averages=1, freq_min=10e6, freq_max=60e6, freq_step=1e6
    ):
        super().__init__(controller)
        self.averages = averages
        self.freq_min = freq_min
        self.freq_max = freq_max
        self.freq_step = freq_step
        self.freqs = np.arange(freq_min, freq_max, freq_step)

        if not self.qic.taskrunner_available:
            raise NotImplementedError("This experiment requires the Taskrunner to work")

    def _configure_sequences(self):
        self._built_code_from_sequences(
            {
                "start": lambda code: (
                    code.trigger_immediate(manipulation=self._p["Drive on"]["trigger"])
                ),
                "default": lambda code: (code.trigger_readout()),
                "stop": lambda code: (
                    code.trigger_immediate(manipulation=self._p["Drive off"]["trigger"])
                ),
            },
            add_readout=False,
            add_sync=False,
        )

    def _configure_taskrunner(self):
        self.qic.taskrunner.load_task_source("qubit_freq_sweep_task.c", "freq_sweep")
        # Set parameters
        freq_min = util.conv_freq_to_nco_phase_inc(self.freq_min)
        freq_max = util.conv_freq_to_nco_phase_inc(self.freq_max)
        freq_step = util.conv_freq_to_nco_phase_inc(self.freq_step)

        self.qic.taskrunner.set_param_list(
            [
                self.iteration_averages,
                freq_min,
                freq_max,
                freq_step,
                self._pc_dict["start"],
                self._pc_dict["default"],
                self._pc_dict["stop"],
            ]
        )

    def _record_internal(self):
        # Start the task
        data = np.asarray(
            self._record_internal_taskrunner(
                len(self.freqs) * self.iteration_averages, "Freq-Points"
            )
        )
        data = data / (1.0 * self.iteration_averages * self.qic.sequencer.averages)
        return data
