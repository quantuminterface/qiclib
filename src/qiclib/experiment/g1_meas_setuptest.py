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

from qiclib.experiment.base import BaseExperiment
from qiclib.hardware.taskrunner import TaskRunner


class G1setuptest(BaseExperiment):
    """Measurement of the g1 correlator g1(tau).

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
        measure_background=False,
        drive_offset=800e-9,
    ):
        super().__init__(controller)
        self.tau_step = tau_step
        self.tau_max = tau_max
        self._tau_max_in_steps = int(np.round(self.tau_max / self.tau_step))
        self._sample_num = 1024 - self._tau_max_in_steps
        self.averages = averages
        self.drive_offset = drive_offset
        self.measure_background = measure_background

        self.shift_result = None

        raise NotImplementedError(
            "This experiment needs adaptations for new QiController with cells."
        )
        # if not self.qic.taskrunner_available:
        #     raise NotImplementedError("This experiment requires the Taskrunner to work")

    def _configure_sequences(self):
        self._built_code_from_sequences(
            {
                "default": lambda code: (
                    code
                    # Synchronize NCOs of recording modules
                    .trigger_immediate(0, readout=15, recording=14, external=14)
                    # TODO: Is this necessary to get a stable phase relation?
                    .trigger_immediate(
                        self.drive_offset, readout=self._r["Tone on"]["trigger"]
                    )
                    # Start continuous mode on both recording modules
                    .trigger_registered(1, recording=6, external=6)
                    # Stop the continuous measurement again when memory is full
                    .trigger_immediate(0, recording=7, external=7)
                    # Turn off the drive again
                    .trigger_immediate(0, readout=self._r["Tone off"]["trigger"])
                ),
                "background": lambda code: (
                    code
                    # Synchronize NCOs of recording modules
                    .trigger_immediate(0, readout=15, recording=14, external=14)
                    # Here we do not turn on the drive tone
                    .trigger_immediate(self.drive_offset, readout=0)
                    # Start continuous mode on both recording modules
                    .trigger_registered(1, recording=6, external=6)
                    # Stop the continuous measurement again when memory is full
                    .trigger_immediate(0, recording=7, external=7)
                    # Turn off the drive again (or not in this case)
                    .trigger_immediate(0, readout=0)
                ),
            },
            add_readout=False,
            add_sync=False,
        )

        self.qic.recording.recording_duration = self.tau_step
        # FIXME: self.qic.recording2.recording_duration = self.tau_step

        self._tau_max_in_steps = int(np.round(self.tau_max / self.tau_step))
        self._sample_num = 1024 - self._tau_max_in_steps
        if self.shift_result is None:
            self.shift_result = int(np.ceil(np.log2(self.averages * self._sample_num)))

        # Number of samples to take (1024) times recording duration
        self.qic.sequencer.set_delay_register(1, 1024 * self.tau_step)

    def _configure_taskrunner(self):
        # Flashing task to the R5
        # if self.measure_background:
        self.qic.taskrunner.load_task_source(
            "correlation/g1_meas_setuptest.c", "G1setuptest"
        )
        self.qic.taskrunner.set_param_list(
            [
                self._tau_max_in_steps,
                self.averages,
                self._pc_dict["default"],
                self._pc_dict["background"],
                self.shift_result,
            ]
        )

        # Calculate total number of experiment executions for progress bar
        self.total_num_of_executions = self.averages

    def _record_internal(self):
        old_averages = self.qic.sequencer.averages
        try:
            # Ensure no averaging
            self.qic.sequencer.averages = 1

            data = self._record_internal_taskrunner(
                self.total_num_of_executions,
                "G1setuptest",
                data_mode=TaskRunner.DataMode.INT32,
            )
        finally:
            self.qic.sequencer.averages = old_averages

        # For normalization of g2 (i.e. make it at least independent of experiment parameters)
        divide_by = 1.0 * self.averages
        data = np.atleast_1d(data) / divide_by

        if self.measure_background:
            return data
        else:
            return data[:4]
