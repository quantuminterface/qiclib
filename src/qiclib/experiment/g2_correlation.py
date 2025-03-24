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
"""This file contains the IQCloud experiment description for the QiController."""

import numpy as np

from qiclib.experiment.gx_correlation_base import GxCorrelationBase


class G2Correlation(GxCorrelationBase):
    """Measurement of the g2 correlator g2(tau).

    .. note::
        This experiment outputs a continuous tone through the manipulation pulse generator.

    :param controller:
        The QiController driver
    :param tau_step:
        The step size of tau in seconds.
    :param tau_max:
        The maximum value of tau in seconds.
    :param averages:
        The number of trace averages/repetitions to perform.
    :param measure_background:
        If the background should be measured in parallel (two additional lists at record output; defaults to False)
    :param drive_offset:
        The delay between turning on the drive and starting the measurement.

    :ivar shift_result:
        Divides the result by 1^shift_result to prevent an overflow during averaging.
        (Defaults to a reasonable value regarding averages and summed up sample count)
    """

    def __init__(
        self,
        controller,
        tau_step,
        tau_max,
        averages,
        iterations=1,
        measure_background=False,
        drive_offset=800e-9,
    ):
        super().__init__(
            controller, tau_step, averages, iterations, measure_background, drive_offset
        )
        if not self.qic.taskrunner_available:
            raise NotImplementedError("This experiment requires the Taskrunner to work")

        self.tau_max = tau_max
        self._tau_steps = int(np.round(self.tau_max / self.tau_step))
        self._sample_num = self._recorded_samples - self._tau_steps

        # Estimation: int(np.ceil(np.log2(self.averages * self._sample_num)))
        self.shift_result = 0

    def _configure_taskrunner(self):
        self.qic.taskrunner.load_task_source(
            "correlation/g2_correlation.c", "G2Correlation"
        )
        self.qic.taskrunner.set_param_list(
            [
                self.averages,
                self.iterations,
                self._tau_steps,
                self._pc_dict["default"],
                self._pc_dict["background"],
                self.measure_background * 1,
                self.shift_result,
            ]
        )

    def _extract_amp_pha_from_databoxes(self):
        # For normalization of g2 (i.e. make it at least independent of experiment parameters)
        divide_by = 1.0 * self.averages * self._sample_num / (1 << self.shift_result)
        return super()._extract_amp_pha_from_databoxes(divide_by)
