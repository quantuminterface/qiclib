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
"""This file contains the QuantumJumps experiment description for the QiController."""

import warnings

import numpy as np

from qiclib.experiment.base import BaseExperiment


class QuantumJumps(BaseExperiment):
    """Experiment performing many single-shot readouts and returning
    the calculated states.

    .. deprecated::
        QuantumJumps is deprecated. Please use the new QiCode syntax instead, see
        `qiclib.code`, i.e. write your own `qiclib.code.qi_jobs.QiJob` or use the one
        defined in `qiclib.experiment.qicode.collection` by calling
        `qiclib.jobs.MultiQuantumJumps(shots, qubits)`.

    .. warning::
        Readout pulse (on register 1) has to be configured separately!

    :param controller:
        The QiController driver
    :param count:
        The number of IQ points received
        (the default is 100k)
    :param averaging:
        If averaging on the card should be allowed (no real single-shot then)
        (the default is False)
    :param wait_time:
        The (minimum) time between two experiment repetitions
        (the default is 2mus)
    """

    def __init__(self, controller, count=100000, averaging=False, wait_time=2e-6):
        super().__init__(controller)
        self.count = int(count)
        self.averaging = averaging
        self.wait_time = wait_time
        self.raw_data = False
        self.continuous_readout = False
        self._pc_dict = {}
        warnings.warn(
            "QuantumJumps is deprecated. Please use the new QiCode syntax instead, i.e."
            " write your own `QiJob` or use the one defined in `qiclib.jobs` by calling"
            " `qiclib.jobs.MultiQuantumJumps(shots, qubits)`.",
            FutureWarning,
        )
        if not self.qic.taskrunner_available:
            raise NotImplementedError("This experiment requires the Taskrunner to work")

    def _configure_sequences(self):
        self._built_code_from_sequences(
            {
                "record": lambda code: (code.trigger_nco_sync().trigger_readout()),
                "start_readout": lambda code: (
                    code.trigger_nco_sync().trigger_immediate(
                        readout=self._r["Tone on"]["trigger"]
                    )
                ),
                "record_continuous": lambda code: code.trigger_readout(readout=0),
                "stop_readout": lambda code: code.trigger_immediate(
                    readout=self._r["Tone off"]["trigger"]
                ),
            },
            add_readout=False,
            add_sync=False,
        )

    def _configure_taskrunner(self):
        if self.continuous_readout:
            start_pc = self._pc_dict["record_continuous"]
        else:
            start_pc = self._pc_dict["record"]

        # Flashing task to the R5
        self.qic.taskrunner.load_task_source("quantum_jumps.c", "QuantumJumps")
        self.qic.taskrunner.set_param_list([self.count, start_pc])

    def _record_internal(self):
        old_averages = self.qic.sequencer.averages
        if not self.averaging:
            # Ensure no averaging
            self.qic.sequencer.averages = 1

        if self.continuous_readout:
            self.qic.sequencer.start_at(self._pc_dict["start_readout"])
            old_offset = self.qic.recording.trigger_offset
            self.qic.recording.trigger_offset = 0

        try:
            data = self._record_internal_taskrunner(
                self.count, name="Quantum Jumps", allow_partial_data=True
            )
        finally:
            if self.continuous_readout:
                self.qic.sequencer.start_at(self._pc_dict["stop_readout"])
                self.qic.recording.trigger_offset = old_offset

        if not self.averaging:
            self.qic.sequencer.averages = old_averages

        if self.raw_data:
            return data

        return self._convert_data_to_state_list(data)

    def _convert_data_to_state_list(self, data):
        return np.reshape(
            [[(number >> i) & 1 for i in np.arange(32)] for number in data],
            (len(data) * 32, self.count),
        )
