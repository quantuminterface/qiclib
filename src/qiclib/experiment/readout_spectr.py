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
"""Readout traces averaging done at the R5 rpocessor"""

import warnings

import numpy as np

import qiclib.packages.utility as util
from qiclib.experiment.base import BaseExperiment


class IQFtReadout(BaseExperiment):
    """Experiment solely performing a readout and returning IQ fourier coefficients.

    .. warning::
        Readout pulse (on register 1) has to be configured separately!
    """


class IQRawReadout_Spectr(BaseExperiment):
    """Experiment solely performing a readout and returning IQ raw data.

    .. warning::
        Readout pulse (on register 1) has to be configured separately!

    :param controller:
        The QiController driver
    :param averages:
        How many averages should be performed for the final time trace
    :param offset:
        The offset between readout pulse and recording.
        (the default is None, which lets the offset untouched)
    :param length:
        The length of the recording window
        (the default is None, which lets the length untouched)
    """

    def __init__(
        self, controller, averages: int = 1, offset: float = 0, length: float = 400e-9
    ):
        super().__init__(controller)
        self.iteration_averages = averages
        self.length = length
        self.offset = offset
        self.recording_module = 0
        if not self.qic.taskrunner_available:
            raise NotImplementedError("This experiment requires the Taskrunner to work")

        if not np.log2(util.conv_time_to_samples(length)).is_integer():
            warnings.simplefilter("always")
            warnings.warn("Recording length should be power of 2 to perform FFT")

    def _record_internal(self):
        old_offset = self.qic.recording.trigger_offset
        old_length = self.qic.recording.recording_duration
        old_averages = self.qic.sequencer.averages

        # Convert stuff to values
        length = util.conv_time_to_samples(self.length)

        # Ensure no averaging on the QiController
        self.qic.sequencer.averages = 1

        # Load the task to taskrunner
        self.qic.taskrunner.load_task_source("trace_fft.c", "AverageTraceFFT")
        # Set task parameters
        self.qic.taskrunner.set_param_list(
            [self.iteration_averages, length, self.recording_module]
        )

        try:
            data = np.asarray(
                self._record_internal_taskrunner(
                    length * self.iteration_averages, "Raw Trace"
                )
            )
        finally:
            self.qic.recording.trigger_offset = old_offset
            self.qic.recording.recording_duration = old_length
            self.qic.sequencer.averages = old_averages

        data = data / (1.0 * self.iteration_averages)
        return data
