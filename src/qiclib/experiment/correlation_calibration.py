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
from qiclib.experiment.base import BaseExperiment


class CorrelationCalibration(BaseExperiment):
    """Demo experiment to test (small) recalibration of the two branches of a correlation measurement.

    :param controller:
        The QiController driver
    :param averages:
        The number of averages to perform.
    :param value_shift:
        The value shift to use for the calibration measurements.
        (Defaults to -1 meaning unchanged.)
    """

    def __init__(self, controller, averages, value_shift=-1, repetition_time=0):
        super().__init__(controller)
        self.use_taskrunner = True

        self.averages = averages
        self.value_shift = value_shift
        self._trep = repetition_time

        raise NotImplementedError(
            "This experiment needs adaptations for new QiController with cells."
        )
        # if not self.qic.taskrunner_available:
        #     raise NotImplementedError("This experiment requires the Taskrunner to work")

    def _configure_sequences(self):
        self._built_code_from_sequences(
            {
                "calibration": lambda code: (
                    code
                    # Synchronize NCOs of recording modules
                    .trigger_immediate(0, readout=15, recording=15, external=15)
                    .trigger_readout(delay=self._readout_delay)
                    # Overwrite T_rep -> do not need to wait (faster averaging)
                    .end_of_experiment(self._trep)
                )
            },
            add_readout=False,
            add_sync=False,
        )

        # Simulate similar situation as in correlation measurements
        self.qic.recording.recording_duration = 24e-9
        # FIXME: self.qic.recording2.recording_duration = 24e-9
        self.qic.sequencer.averages = 1

    def _configure_taskrunner(self):
        self.qic.taskrunner.load_task_source(
            "correlation/calibration.c", "CorrelationCalibration"
        )
        self.qic.taskrunner.set_param_list(
            [
                self._pc_dict["calibration"],
                self.averages,
                self.value_shift,
                util.conv_time_to_cycles(self.qic.sample.rec_duration),
            ]
        )

    def _record_internal(self):
        data = self._record_internal_taskrunner(14, "Calibration")
        return [
            self._convert_amp_pha(data[1][0], data[1][1]),
            self._convert_amp_pha(data[1][2], data[1][3]),
        ]

    def _convert_amp_pha(self, i, q):
        data_complex = i + 1j * q
        return (np.abs(data_complex), np.angle(data_complex))
