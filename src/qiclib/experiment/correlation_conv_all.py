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

import qiclib.packages.utility as util
from qiclib.experiment.gx_correlation_base import GxCorrelationBase, TaskrunnerReadout
from qiclib.hardware.taskrunner import TaskRunner


class CorrelationConvAll(GxCorrelationBase):
    """Measurement of the g2 and g1 correlator g2(tau).
    This version uses FFTs to speed up the calculation.

    .. note::
        This experiment outputs a continuous tone through the readout pulse generator.

    :param controller:
        The QiController driver
    :param tau_step:
        The step size of tau in seconds.
    :param averages:
        The number of trace averages/repetitions to perform.
    :param drive_offset:
        The delay between turning on the drive and starting the measurement.
    """

    def __init__(
        self,
        controller,
        tau_step,
        averages,
        iterations=1,
        calib_averages=100000,
        calib_repetition=1,
        drive_offset=800e-9,
    ):
        super().__init__(controller, tau_step, averages, iterations, True, drive_offset)
        self.calib_averages = calib_averages
        self.calib_mod_selection = calib_repetition

    @property
    def readout(self):
        """A readout object for Measure_td class."""
        return TaskrunnerReadout(
            experiment=self,
            count=self.averages * self.iterations,
            name="Averages",
            data_mode=TaskRunner.DataMode.INT64,
            tones=[self.qic.readout.frequency] * 2
            + [0] * 2
            + [self.qic.readout.frequency] * 2,
        )

    def _configure_taskrunner(self):
        # Flashing task to the R5
        self.qic.taskrunner.load_task_source(
            "correlation/correlation_conv.c", "CorrelationConvAll"
        )
        self.qic.taskrunner.set_param_list(
            [
                self.averages,
                self.iterations,
                self._pc_dict["default"],
                self._pc_dict["background"],
                self._pc_dict["calibration"],
                self.calib_averages,
                self.qic.recording.value_shift_initial
                - self.qic.sample.rec_shift_offset,
                util.conv_time_to_cycles(self.qic.sample.rec_duration),
                self.calib_mod_selection,
            ]
        )

    def _record_databox_extract(self):
        if not self._databoxes or len(self._databoxes) < 8:
            raise ValueError("Not enough databoxes available to extract data from...")

        compl_g1 = self._extract_complex_from_databoxes()
        compl_g2 = self._extract_complex_from_databoxes()
        compl_g1_ss = self._extract_complex_from_databoxes()
        compl_g2_ss = self._extract_complex_from_databoxes()

        norm_g1 = compl_g1 - compl_g1_ss
        norm_g2 = (
            compl_g2
            - compl_g2_ss
            - 2.0 * np.ones(len(norm_g1)) * norm_g1[0] * compl_g1_ss[0]
            - np.conjugate(norm_g1) * np.conjugate(compl_g1_ss)
            - norm_g1 * compl_g1_ss
        ) / np.abs(norm_g1[0]) ** 2

        return [
            self._complex_to_amp_pha(compl_g1),
            self._complex_to_amp_pha(compl_g2),
            self._complex_to_amp_pha(compl_g1_ss),
            self._complex_to_amp_pha(compl_g2_ss),
            self._complex_to_amp_pha(norm_g1),
            self._complex_to_amp_pha(norm_g2),
        ]

    def _extract_complex_from_databoxes(self):
        divide_by = 1.0 * self.averages
        data_fft_real = np.atleast_1d(self._databoxes[0]) / divide_by
        data_fft_imag = np.atleast_1d(self._databoxes[1]) / divide_by

        # Remove processed databoxes
        self._databoxes = self._databoxes[2:]

        # Somehow we have to multiply the result by the sample number to get right normalization
        return np.fft.ifft(data_fft_real + 1j * data_fft_imag) * self._sample_num

    def _complex_to_amp_pha(self, data_complex):
        return np.abs(data_complex), np.angle(data_complex)
