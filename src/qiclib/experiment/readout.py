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

import qiclib.packages.constants as const
import qiclib.packages.utility as util
from qiclib.experiment.base import BaseExperiment


class IQFtReadout(BaseExperiment):
    """Experiment solely performing a readout and returning IQ fourier coefficients.

    .. deprecated::
        IQFtReadout is deprecated. Please use the new QiCode syntax instead, see
        `qiclib.code`, i.e. write your own `qiclib.code.qi_jobs.QiJob` or use the one
        defined in `qiclib.experiment.qicode.collection` by calling
        `qiclib.jobs.SimpleReadout().run(...)`.

    .. warning::
        Readout pulse (on register 1) has to be configured separately!
    """

    def __init__(self, controller, cell=0):
        super().__init__(controller, cell)
        warnings.warn(
            "IQFtReadout is deprecated. Please use the new QiCode syntax instead, "
            "i.e. write your own `QiJob` or use the one defined in `qiclib.jobs` by "
            "calling `qiclib.jobs.SimpleReadout().run(...)`.",
            FutureWarning,
        )


class IQRawReadout(BaseExperiment):
    """Experiment solely performing a readout and returning IQ raw data.

    .. deprecated::
        IQRawReadout is deprecated. Please use the new QiCode syntax instead, see
        `qiclib.code`, i.e. write your own `qiclib.code.qi_jobs.QiJob` or use the one
        defined in `qiclib.experiment.qicode.collection` by calling
        `qiclib.jobs.SimpleReadout().run(..., data_collection="raw")`.
        You can also use `qiclib.init.record_timetrace(...)`.

    .. warning::
        Readout pulse (on register 1) has to be configured separately!

    :param controller:
        The QiController driver
    :param averages:
        How many averages should be performed for the final time trace
    :param offset:
        The offset between readout pulse and recording.
    :param length:
        The length of the recording window
        (the default is None, which lets the length untouched)
    """

    def __init__(self, controller, averages=1, offset=0, length=400e-9, cell=0):
        super().__init__(controller, cell)
        self.iteration_averages = averages
        self.length = length
        self.offset = offset
        warnings.warn(
            "IQRawReadout is deprecated. Please use the new QiCode syntax instead, "
            "i.e. write your own `QiJob` or use the one defined in `qiclib.jobs` by "
            'calling `qiclib.jobs.SimpleReadout().run(..., data_collection="raw")`. '
            "You can also use `qiclib.init.record_timetrace(...).",
            FutureWarning,
        )
        if not self.qic.taskrunner_available:
            raise NotImplementedError("This experiment requires the Taskrunner to work")

    def _configure_taskrunner(self):
        # Load the task to taskrunner
        self.qic.taskrunner.load_task_source("average_trace.c", "AverageTrace")

        samples = util.conv_time_to_samples(self.length)
        if samples > const.RECORDING_MAX_RAW_SAMPLES:
            warnings.warn(
                "Length is too large for raw recording. "
                + f"Only the first {util.conv_samples_to_time(const.RECORDING_MAX_RAW_SAMPLES) * 1e9:.0f}ns "
                "will be displayed."
            )
            # If we do not do this, this will lead to artifacts as the C code doesn't check it
            samples = const.RECORDING_MAX_RAW_SAMPLES

        # Set task parameters
        self.qic.taskrunner.set_param_list(
            [
                self.iteration_averages,
                util.conv_time_to_cycles(self.offset),
                samples,
                self.cell_index,
            ]
        )

    def _record_internal(self):
        old_offset = self.cell.recording.trigger_offset
        old_length = self.cell.recording.recording_duration
        old_averages = self.cell.sequencer.averages

        # Ensure no averaging on the QiController
        self.cell.sequencer.averages = 1

        try:
            data = np.asarray(
                self._record_internal_taskrunner(self.iteration_averages, "Raw Trace")
            )
        finally:
            self.cell.recording.trigger_offset = old_offset
            self.cell.recording.recording_duration = old_length
            self.cell.sequencer.averages = old_averages

        data = data / (1.0 * self.iteration_averages)
        return data
