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
"""The Ramsey Experiment for the QiController."""

import warnings

import numpy as np

from qiclib.experiment.base import BaseExperiment


class Ramsey(BaseExperiment):
    """Ramsey experiment consisting of two pi/2 pulses separated by a varying time.
    The reached end state oscillates as a function of the delay between the two pulses.

    .. deprecated::
        Ramsey is deprecated. Please use the new QiCode syntax instead, see `qiclib.code`,
        i.e. write your own `qiclib.code.qi_jobs.QiJob` or use the one defined
        in `qiclib.experiment.qicode.collection` by calling
        `qiclib.jobs.Ramsey(start, stop, step, detuning)`.


    .. warning::
        Readout pulse (on register 1) has to be configured separately!

    :param controller:
        The QiController driver
    :param delay_min:
        The minimum delay between the two pulses
    :param delay_max:
        The maximum delay between the two pulses
    :param delay_step:
        The increment of the delay between two iterations
    :param phase:
        The relative phase between the two pulses
    """

    def __init__(
        self, controller, delay_min=0, delay_max=800e-9, delay_step=16e-9, phase=0
    ):
        self.delays = np.arange(delay_min, delay_max, delay_step)
        super().__init__(controller)
        warnings.warn(
            "Ramsey is deprecated. Please use the new QiCode syntax instead, i.e. "
            "write your own `QiJob` or use the one defined in `qiclib.jobs` by calling "
            "`qiclib.jobs.Ramsey(start, stop, step, detuning)`.",
            FutureWarning,
        )

    def _single_execution(self, duration):
        return {
            "sequencer_start": self._pc_dict["exp"],
            "delay_registers": [duration + self._p["Rx pi/2"]["length"]],
        }

    def _configure_sequences(self):
        self._built_code_from_sequences(
            {
                "exp": lambda code: (
                    code.trigger_registered(
                        register=1, manipulation=self._p["Rx pi/2"]["trigger"]
                    ).trigger_immediate(
                        delay=self._p["Rx pi/2"]["length"],
                        manipulation=self._p["Rx pi/2"]["trigger"],
                    )
                )
            }
        )

    def _record_internal(self):
        return self._record_internal_1d(self.delays, "Delays", self._single_execution)
