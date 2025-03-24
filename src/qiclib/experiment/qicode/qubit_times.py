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
import numpy as np

import qiclib.packages.utility as util
from qiclib.code import (
    Assign,
    Else,
    If,
    QiCells,
    QiJob,
    QiSample,
    QiTimeVariable,
    QiVariable,
    Wait,
)
from qiclib.hardware.controller import QiController

from .base import QiCodeExperiment
from .collection import PiHalfPulse, PiPulse, Readout, Thermalize


class QubitTimes(QiCodeExperiment):
    """Interleaved execution of T1, Ramsey and SpinEcho experiments
    on multiple cells in parallel.

    :param controller:
        The QiController driver
    :param sample:
        Sample object containing qubit and setup properties
    :param delays_t1:
        List of delays for the T1 experiment.
    :type delays_t1: List[number]
    :param delays_ramsey:
        List of delays for the Ramsey experiment.
    :type delays_ramsey: List[number]
    :param delays_spinecho:
        List of delays for the SpinEcho experiment. The delays are the sum of both delays.
    :type delays_spinecho: List[number]
    :param order:
        List specifying the order of the experiments within a single repetition.
        0 - T1, 1 - Ramsey, 2 - SpinEcho
    :type order: List[number]
    :param ramsey_detuning:
        The detuning (in Hz) for the Ramsey experiment.
    :type ramsey_detuning: number
    :param spinecho_phase:
        The relative phase of the correcting pi pulse between the pi/2 pulses.
        Defaults to pi/2 (Y instead of X rotation).
    :type spinecho_phase: number


    .. warning::
        Readout pulse (on register 1) has to be configured separately!
    """

    def __init__(
        self,
        controller: QiController,
        sample: QiSample,
        delays_t1,
        delays_ramsey,
        delays_echo,
        averages=1,
        order=[0, 1, 2],
        ramsey_detuning=0,
        spinecho_phase=np.pi / 2,
        cell_map=None,
    ):
        # If a cell_map is given it determines on which qubits (and how many) to act
        # Otherwise, all qubits of the sample object are used
        if cell_map is None:
            cell_map = list(range(len(sample)))
        job = self._create_job(len(cell_map), spinecho_phase)
        super().__init__(
            *job._prepare_experiment_params(controller, sample, averages, cell_map)
        )
        if not self.qic.taskrunner_available:
            raise NotImplementedError("This experiment requires the Taskrunner to work")

        self._name = "Qubit Times (Interleaved T1, Ramsey, SpinEcho)"

        self.delays_t1 = np.atleast_1d(delays_t1)
        self.delays_ramsey = np.atleast_1d(delays_ramsey)
        self.delays_echo = np.atleast_1d(delays_echo)
        self.order = order  # [2, 0, 2, 1, 2, 2]
        self.averages = averages

        self.ramsey_detuning = ramsey_detuning
        self.spinecho_phase = spinecho_phase

        self.raw_results = False

    def _create_job(self, num, spinecho_phase):
        with QiJob() as job:
            delay = QiTimeVariable(name="delay")
            expsel = QiVariable(int, name="experiment")
            delay2 = QiTimeVariable()
            Assign(delay2, delay >> 1)
            for q in QiCells(num):
                with If(delay == 0):
                    # Special case with no delay
                    with If(expsel == 0):
                        # T1 Experiment
                        PiPulse(q)
                        Readout(q)
                    with If(expsel == 1):
                        # Ramsey
                        PiHalfPulse(q)
                        PiHalfPulse(q)
                        Readout(q)
                    with If(expsel == 2):
                        # SpinEcho
                        PiHalfPulse(q)
                        PiPulse(q, phase=spinecho_phase)
                        PiHalfPulse(q)
                        Readout(q)
                with Else():
                    with If(expsel == 0):
                        # T1 Experiment
                        PiPulse(q)
                        Wait(q, delay)
                        Readout(q)
                    with If(expsel == 1):
                        # Ramsey
                        PiHalfPulse(q)
                        Wait(q, delay)
                        PiHalfPulse(q)
                        Readout(q)
                    with If(expsel == 2):
                        # SpinEcho
                        PiHalfPulse(q)
                        Wait(q, delay2)
                        PiPulse(q, phase=spinecho_phase)
                        Wait(q, delay2)
                        PiHalfPulse(q)
                        Readout(q)
                Thermalize(q)
        return job

    def _configure_taskrunner(self):
        # Generate Parameters for the task
        task_num_of_experiments = 3
        task_experiment_cell_map = self.cell_map
        task_experiment_order = self.order
        task_experiments_per_loop = len(self.order)
        task_experiment_executions = [
            len(self.delays_t1),
            len(self.delays_ramsey),
            len(self.delays_echo),
        ]
        task_experiment_delays = np.concatenate(
            (
                self.delays_t1,
                self.delays_ramsey,
                self.delays_echo,
            )
        )
        task_experiment_delays = [
            util.conv_time_to_cycles(delay, "ceil") for delay in task_experiment_delays
        ]

        task_experiment_nco_freq = []
        for _, cell, _ in self.cell_iterator():
            freq = cell.initial_manipulation_frequency
            freq_inc = util.conv_freq_to_nco_phase_inc(freq)
            detuning = util.conv_freq_to_nco_phase_inc(freq + self.ramsey_detuning)
            task_experiment_nco_freq.append([freq_inc, detuning, freq_inc])
        task_experiment_nco_freq = util.flatten(task_experiment_nco_freq)

        parameters = util.flatten(
            [
                [task_num_of_experiments],
                [task_experiments_per_loop],
                [len(self.cell_list)],
                task_experiment_cell_map,
                task_experiment_order,
                task_experiment_executions,
                task_experiment_nco_freq,
                task_experiment_delays,
            ]
        )

        # Flashing task to the R5
        self.qic.taskrunner.load_task_source("interleaved_multi.c", "InterleavedMulti")
        self.qic.taskrunner.set_param_list(parameters)

        # Calculate total number of experiment executions for progress bar
        self.total_num_of_executions = np.sum(task_experiment_executions)

    def _record_internal(self):
        for _, _, qic_cell in self.cell_iterator():
            qic_cell.sequencer.averages = self.averages

        try:
            data = self._record_internal_taskrunner(
                self.total_num_of_executions,
                "QubitTimesMulti",
                start_callback=self._callback_after_task_start,
            )
        finally:
            for _, cell, qic_cell in self.cell_iterator():
                qic_cell.manipulation.internal_frequency = (
                    cell.initial_manipulation_frequency
                )

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

        return [
            {
                "t1": _convert(data[3 * i + 0]),
                "ramsey": _convert(data[3 * i + 1]),
                "echo": _convert(data[3 * i + 2]),
            }
            for i, _, _ in self.cell_iterator()
        ]
