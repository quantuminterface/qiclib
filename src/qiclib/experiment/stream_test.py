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


class StreamTest(BaseExperiment):
    """StreamTest"""

    def __init__(self, controller, length, repetitions):
        super().__init__(controller)
        self._databox_streaming = True
        self.use_taskrunner = True
        if not self.qic.taskrunner_available:
            raise NotImplementedError("This experiment requires the Taskrunner to work")

        self.length = length
        self.repetitions = repetitions

    @property
    def readout(self):
        """A readout object for Qkit's Measure_td class."""
        return TaskrunnerReadout(
            experiment=self,
            count=self.length * self.repetitions,
            name="Numbers",
            data_mode=TaskRunner.DataMode.UINT32,
            tones=1,
        )

    def _configure_sequences(self):
        pass

    def _configure_taskrunner(self):
        self.qic.taskrunner.load_task_source("test/stream_test.c", "StreamTest")
        self.qic.taskrunner.set_param_list([self.length, self.repetitions])

    def _record_databox_extract(self):
        if not self._databoxes:
            raise ValueError("Not enough databoxes available to extract data from...")

        amp, pha = self._extract_amp_pha_from_databoxes()
        result = [(amp, pha)]
        return result

    def _extract_amp_pha_from_databoxes(self):
        amp = self._databoxes[0]
        pha = np.arange(0, len(amp), 1)

        # Remove processed databox
        self._databoxes = self._databoxes[1:]

        return amp, pha
