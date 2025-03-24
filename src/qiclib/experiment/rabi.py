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
"""This file contains the rabi experiment description for the QiController and R5 processor.
Iteration averaging is done on R5"""

import warnings

import numpy as np

import qiclib.packages.utility as util
from qiclib.experiment.base import BaseExperiment


class Rabi(BaseExperiment):
    r"""Rabi experiment driving the qubit between the states \|0> and \|1>.

    This experiment outputs pulses at the qubit frequency of
    different duration and measures in which state the qubit is. Can be
    used to determine pulse duration for pi and pi/2 rotation pulses.

    .. deprecated::
        Rabi is deprecated. Please use the new QiCode syntax instead, see `qiclib.code`,
        i.e. write your own `qiclib.code.qi_jobs.QiJob` or use the one defined
        in `qiclib.experiment.qicode.collection` by calling
        `qiclib.jobs.Rabi(start, stop, step)`.

    .. warning::
        Readout pulse (on register 1) has to be configured separately!

    :param controller:
        The QiController driver
    :param duration_min:
        The minimum duration of the manipulation pulse (the default is 0s, so no pulse)
    :param duration_max:
        The maximum duration of the manipulation pulse (the default is 1000ns)
    :param duration_step:
        The increment of the duration between two iterations of the measurement
        (the default is 24ns)
    """

    def __init__(
        self, controller, duration_min=0, duration_max=1e-6, duration_step=24e-9
    ):
        self.durations = np.arange(duration_min, duration_max, duration_step)
        super().__init__(controller)
        warnings.warn(
            "Rabi is deprecated. Please use the new QiCode syntax instead, i.e. write "
            "your own `QiJob` or use the one defined in `qiclib.jobs` by calling "
            "`qiclib.jobs.Rabi(start, stop, step)`.",
            FutureWarning,
        )

    def _single_execution(self, duration):
        return {
            "sequencer_start": self._pc_dict["zero pulse"]
            if duration == 0
            else self._pc_dict["normal"],
            "delay_registers": [duration],
        }

    def _configure_sequences(self):
        # Duration of the pulse will be written into the delay register
        # Register is initialized with 1 clock cycle delay
        self.qic.sequencer.set_delay_register(1, delay=util.conv_cycles_to_time(1))

        self._built_code_from_sequences(
            {
                "normal": lambda code: (
                    code.trigger_registered(
                        1, manipulation=self._p["Drive on"]["trigger"]
                    ).trigger_immediate(manipulation=self._p["Drive off"]["trigger"])
                ),
                # One clock cycle delay (to simulate turning off the Drive which also takes 1 cycle)
                "zero pulse": lambda code: code.trigger_immediate(0),
            }
        )

    def _record_internal(self):
        return self._record_internal_1d(
            self.durations, "Durations", self._single_execution
        )
