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


class G2CorrelationConv(GxCorrelationBase):
    """Measurement of the g2 correlator g2(tau).
    This version uses FFTs to speed up the calculation.

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

    def _configure_taskrunner(self):
        # Flashing task to the R5
        self.qic.taskrunner.load_task_source(
            "correlation/g2_correlation_conv.c", "G2CorrelationConv"
        )
        self.qic.taskrunner.set_param_list(
            [
                self.averages,
                self.iterations,
                self._pc_dict["default"],
                self._pc_dict["background"],
                self.measure_background,
            ]
        )

    def _extract_amp_pha_from_databoxes(self):
        # For normalization of g1
        divide_by = 1.0 * self.averages * self._sample_num

        data_fft_real = np.atleast_1d(self._databoxes[0]) / divide_by
        data_fft_imag = np.atleast_1d(self._databoxes[1]) / divide_by

        data_complex = np.fft.ifft(data_fft_real + 1j * data_fft_imag)

        amp = np.abs(data_complex)
        pha = np.angle(data_complex)

        # Remove processed databoxes
        self._databoxes = self._databoxes[2:]

        return amp, pha
