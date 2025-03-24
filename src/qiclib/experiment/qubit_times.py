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

import warnings

import numpy as np

import qiclib.packages.utility as util
from qiclib.experiment.base import BaseExperiment


class QubitTimes(BaseExperiment):
    """Interleaved execution of T1, Ramsey and SpinEcho experiments.

    .. deprecated::
        QubitTimes is deprecated. Please use the new QiCode syntax instead, see
        `qiclib.code`, i.e. write your own `qiclib.code.qi_jobs.QiJob` or use the one
        defined in `qiclib.experiment.qicode.qubit_times`.

    .. warning::
        Readout pulse (on register 1) has to be configured separately!

    :param controller:
        The QiController driver
    :param delays_t1:
        List of delays for the T1 experiment.
    :param delays_ramsey:
        List of delays for the Ramsey experiment.
    :param delays_spinecho:
        List of delays for the SpinEcho experiment. The delays are the sum of both delays.
    :param order:
        List specifying the order of the experiments within a single repetition.
        0 - T1, 1 - Ramsey, 2 - SpinEcho
    :param ramsey_detuning:
        The detuning (in Hz) for the Ramsey experiment.
    :param spinecho_phase:
        The relative phase of the correcting pi pulse between the pi/2 pulses. Defaults to pi/2 (Y instead of X rotation).
    """

    def __init__(
        self,
        controller,
        delays_t1,
        delays_ramsey,
        delays_echo,
        order=[0, 1, 2],
        ramsey_detuning=0,
        spinecho_phase=np.pi / 2,
    ):
        super().__init__(controller)
        self._name = "Qubit Times (Interleaved T1, Ramsey, SpinEcho)"

        self.delays_t1 = np.atleast_1d(delays_t1)
        self.delays_ramsey = np.atleast_1d(delays_ramsey)
        self.delays_echo = np.atleast_1d(delays_echo)
        self.order = order  # [2, 0, 2, 1, 2, 2]

        self.spinecho_phase = spinecho_phase

        freq_inc = util.conv_freq_to_nco_phase_inc(self.qic.manipulation.if_frequency)
        detuning = util.conv_freq_to_nco_phase_inc(
            self.qic.manipulation.if_frequency + ramsey_detuning
        )
        self.manip_freqs = [freq_inc, detuning, freq_inc]

        self.raw_results = False
        warnings.warn(
            "QubitTimes is deprecated. Please use the new QiCode syntax instead, i.e. "
            "write your own `QiJob` or use the one defined in "
            "`qiclib.experiment.qicode.qubit_times`.",
            FutureWarning,
        )
        if not self.qic.taskrunner_available:
            raise NotImplementedError("This experiment requires the Taskrunner to work")

    def _configure_sequences(self):
        # Ry pi pulse is used for spinecho, but the phase is altered for this experiment
        self.qic.manipulation.triggerset[
            self._p["Ry pi"]["trigger"]
        ].phase_offset = self.spinecho_phase

        self._built_code_from_sequences(
            {
                # Wait: Pi-Time + Delay
                "T1": lambda code: code.trigger_registered(
                    1, manipulation=self._p["Rx pi"]["trigger"]
                ),
                "Ramsey": lambda code: (
                    code
                    # Wait: Pi/2-Time + Delay
                    .trigger_registered(1, manipulation=self._p["Rx pi/2"]["trigger"])
                    # Second pi/2 Pulse
                    .trigger_immediate(
                        delay=self._p["Rx pi/2"]["length"],
                        manipulation=self._p["Rx pi/2"]["trigger"],
                    )
                ),
                "SpinEcho": lambda code: (
                    code
                    # Wait: Pi/2-Time + Delay
                    .trigger_registered(1, manipulation=self._p["Rx pi/2"]["trigger"])
                    # Pi Pulse, but wait only Pi/2-Time
                    .trigger_immediate(
                        self._p["Ry pi"]["length"] - self._p["Rx pi/2"]["length"],
                        manipulation=self._p["Ry pi"]["trigger"],
                    )
                    # Now wait Pi/2-Time + Delay (can use same delay register)
                    .trigger_registered(1)
                    .trigger_immediate(
                        self._p["Rx pi/2"]["length"],
                        manipulation=self._p["Rx pi/2"]["trigger"],
                    )
                ),
            }
        )

    def _configure_taskrunner(self):
        # Generate Parameters for the task
        task_num_of_experiments = 3
        task_experiment_order = self.order
        task_experiments_per_loop = len(self.order)
        task_experiment_sequence_pc = [
            self._pc_dict["T1"],
            self._pc_dict["Ramsey"],
            self._pc_dict["SpinEcho"],
        ]
        task_experiment_executions = [
            len(self.delays_t1),
            len(self.delays_ramsey),
            len(self.delays_echo),
        ]
        task_experiment_nco_freq = self.manip_freqs
        task_experiment_delays = np.concatenate(
            (
                self.delays_t1 + self._p["Rx pi"]["length"],
                self.delays_ramsey + self._p["Rx pi/2"]["length"],
                # Total delay = 2 * delay between single pulses => / 2
                self.delays_echo / 2.0 + self._p["Rx pi/2"]["length"],
            )
        )
        task_experiment_delays = [
            util.conv_time_to_cycles(delay, "ceil") for delay in task_experiment_delays
        ]

        parameters = [
            item
            for sublist in [
                [task_num_of_experiments],
                [task_experiments_per_loop],
                task_experiment_order,
                task_experiment_sequence_pc,
                task_experiment_executions,
                task_experiment_nco_freq,
                task_experiment_delays,
            ]
            for item in sublist
        ]

        # Flashing task to the R5
        self.qic.taskrunner.load_task_source("interleaved.c", "Interleaved")
        self.qic.taskrunner.set_param_list(parameters)

        # Calculate total number of experiment executions for progress bar
        self.total_num_of_executions = np.sum(task_experiment_executions)

    def _record_internal(self):
        old_manip_freq = self.qic.manipulation.internal_frequency
        try:
            data = self._record_internal_taskrunner(
                self.total_num_of_executions,
                "QubitTimes",
                start_callback=self._callback_after_task_start,
            )
        finally:
            # We reset the internal frequency here without adapting the LO
            # as it was used to willingly tune the frequency without changing the LO
            # So resetting it will lead to the old RF frequency
            self.qic.manipulation.internal_frequency = old_manip_freq

        if self.raw_results:
            return data
        else:
            return self.format_data(data)

    def _callback_after_task_start(self):
        pass

    def format_data(self, data):
        """Formats raw output data to dictionary containing amplitude and phase values."""

        def _convert(datalist):
            data_temp = np.array(datalist[::2], copy=False) + 1j * np.array(
                datalist[1::2], copy=False
            )
            return (np.abs(data_temp), np.angle(data_temp))

        return {
            "t1": _convert(data[0]),
            "ramsey": _convert(data[1]),
            "echo": _convert(data[2]),
        }
