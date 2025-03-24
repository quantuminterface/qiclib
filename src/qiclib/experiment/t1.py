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
"""This file contains the T1 experiment description for the QiController."""

import warnings

import numpy as np

from qiclib.experiment.base import BaseExperiment


class T1(BaseExperiment):
    """
    Experiment to measure T1 decay time consisting of a pi pulse followed by a measurement pulse.
    Depending on the time between the pulses the probability that the qubit has decayed increases.

    .. deprecated::
        T1 is deprecated. Please use the new QiCode syntax instead, see
        `qiclib.code`, i.e. write your own `qiclib.code.qi_jobs.QiJob` or use the one
        defined in `qiclib.experiment.qicode.collection` by calling
        `qiclib.jobs.T1(start, stop, step)`.

    .. warning::
        Readout pulse (on register 1) has to be configured separately!


    :param controller:
        The QiController driver
    :param delay_min:
        The minimum delay between pi pulse and readout
    :param delay_max:
        The maximum delay between pi pulse and readout
    :param delay_step: {float}, optional
        The delay increment between two iterations
    """

    def __init__(self, controller, delay_min=0, delay_max=1e-6, delay_step=24e-9):
        self.delays = np.arange(delay_min, delay_max, delay_step)
        super().__init__(controller)
        warnings.warn(
            "T1 is deprecated. Please use the new QiCode syntax instead, i.e. "
            "write your own `QiJob` or use the one defined in `qiclib.jobs` by calling "
            "`qiclib.jobs.T1(start, stop, step)`.",
            FutureWarning,
        )

    def _single_execution(self, delay):
        return {
            "sequencer_start": self._pc_dict["exp"],
            "delay_registers": [delay + self._p["Rx pi"]["length"]],
        }

    def _configure_sequences(self):
        self._built_code_from_sequences(
            {
                # Pi pulse + delay
                "exp": lambda code: code.trigger_registered(
                    1, manipulation=self._p["Rx pi"]["trigger"]
                )
            }
        )

    def _record_internal(self):
        return self._record_internal_1d(self.delays, "Delays", self._single_execution)
