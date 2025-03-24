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

from qiclib.experiment.base import BaseExperiment, TaskrunnerReadout
from qiclib.hardware.taskrunner import TaskRunner


class GxCorrelationBase(BaseExperiment):
    """Base experiment for two channel correlation measurements.

    .. note::
        This experiment outputs a continuous tone through the manipulation pulse generator.

    :param controller:
        The QiController driver
    :param tau_step:
        The step size of tau in seconds.
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
        averages,
        iterations=1,
        measure_background=False,
        drive_offset=800e-9,
    ):
        super().__init__(controller)
        self._databox_streaming = True
        self.use_taskrunner = True

        self._recorded_samples = 1024
        self._sample_num = self._recorded_samples
        self.tau_step = tau_step
        self._tau_steps = self._recorded_samples
        self.averages = averages
        self.iterations = iterations
        self.drive_offset = drive_offset
        self.measure_background = measure_background

        raise NotImplementedError(
            "This experiment needs adaptations for new QiController with cells."
        )
        # if not self.qic.taskrunner_available:
        #     raise NotImplementedError("This experiment requires the Taskrunner to work")

    @property
    def tau_list(self):
        """List containing the tau values corresponding to the resulting correlation values."""
        return np.arange(0, self._tau_steps, 1) * self.tau_step

    @property
    def readout(self):
        """A readout object for Measure_td class."""
        return TaskrunnerReadout(
            experiment=self,
            count=self.averages * self.iterations,
            name="Averages",
            data_mode=TaskRunner.DataMode.INT64,
            tones=[self.qic.readout.frequency]
            + ([0] if self.measure_background else []),
        )

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
                "calibration": lambda code: (
                    code
                    # Synchronize NCOs of recording modules
                    .trigger_immediate(0, readout=15, recording=15, external=15)
                    .trigger_readout(delay=self._readout_delay)
                    # Overwrite T_rep -> do not need to wait (faster averaging)
                    .end_of_experiment(0)
                ),
            },
            add_readout=False,
            add_sync=False,
        )

        self.qic.recording.recording_duration = self.tau_step
        # FIXME: self.qic.recording2.recording_duration = self.tau_step

        # Number of samples to take (1024) times recording duration for each
        self.qic.sequencer.set_delay_register(1, self._recorded_samples * self.tau_step)

        # Ensure no averaging
        self.qic.sequencer.averages = 1

    def _record_databox_extract(self):
        if not self._databoxes or len(self._databoxes) < (
            4 if self.measure_background else 2
        ):
            raise ValueError("Not enough databoxes available to extract data from...")

        amp, pha = self._extract_amp_pha_from_databoxes()
        result = [(amp, pha)]

        if self.measure_background:
            # Also obtain background data
            amp_ss, pha_ss = self._extract_amp_pha_from_databoxes()
            result.append((amp_ss, pha_ss))

        return result

    def _extract_amp_pha_from_databoxes(self, divide_by=None):
        # For normalization of gx
        if divide_by is None:
            divide_by = 1.0 * self.averages

        data_real = np.atleast_1d(self._databoxes[0])
        data_imag = np.atleast_1d(self._databoxes[1])

        data_complex = data_real + 1j * data_imag
        amp = np.abs(data_complex) / divide_by
        pha = np.angle(data_complex)

        # Remove processed databoxes
        self._databoxes = self._databoxes[2:]

        return amp, pha
