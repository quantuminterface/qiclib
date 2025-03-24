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
"""The SpinEcho experiment for the QiController."""

import warnings

import numpy as np

from qiclib.experiment.base import BaseExperiment


class SpinEcho(BaseExperiment):
    """Spin-Echo experiment consisting of a pi/2 pulse,
    *number_of_pi_pulses* pi pulse(s) and another pi/2 pulse.
    Depending on the time between the pulses different end states are reached.

    With default *phase* and *number_of_pi_pulses*, the experiment pulses are the following:
    X(Pi/2) -> Delay/2 -> Y(Pi) -> Delay/2 -> X(Pi/2) -> Readout

    .. deprecated::
        SpinEcho is deprecated. Please use the new QiCode syntax instead, see
        `qiclib.code`, i.e. write your own `qiclib.code.qi_jobs.QiJob` or use the one
        defined in `qiclib.experiment.qicode.collection` by calling
        `qiclib.jobs.SpinEcho(start, stop, step)`.

    .. warning::
        Readout pulse (on register 1) has to be configured separately!

    :param controller:
        The QiController driver
    :param delay_min:
        The minimum total delay between the pi/2 and pi pulses
    :param delay_max:
        The maximum total delay between the pi/2 and pi pulses
    :param delay_step:
        The increment of the total delay between pi/2 and pi pulses
    :param delay_between_pi:
        The delay between pi pulses in the middle
    :param phase:
        The phase of the pi pulses with respect to the pi/2 pulsed
        (the default is pi/2, so rotation around Y axis of the Bloch sphere)
    :param number_of_pi_pulses:
        The number of pi pulses inbetween the pi/2 pulses (the default is 1)
    """

    def __init__(
        self,
        controller,
        delay_min=0,
        delay_max=800e-9,
        delay_step=16e-9,
        delay_between_pi=48e-9,
        phase=np.pi / 2,
        number_of_pi_pulses=1,
    ):
        self.delays = np.arange(delay_min, delay_max, delay_step)
        super().__init__(controller)
        self.delay_between_pi = delay_between_pi
        self.number_of_pi_pulses = number_of_pi_pulses
        self.phase = phase
        warnings.warn(
            "SpinEcho is deprecated. Please use the new QiCode syntax instead, i.e. "
            "write your own `QiJob` or use the one defined in `qiclib.jobs` by calling "
            "`qiclib.jobs.SpinEcho(start, stop, step)`.",
            FutureWarning,
        )

    def _single_execution(self, delay):
        return {
            "sequencer_start": self._pc_dict["exp"],
            "delay_registers": [
                self._p["Rx pi/2"]["length"] + delay,
                self._p["Ry pi"]["length"] + self.delay_between_pi,
                self._p["Ry pi"]["length"] + delay,
            ],
        }

    def _configure_sequences(self):
        # Ry pi pulse is used, but the phase is altered for this experiment
        self.qic.manipulation.triggerset[
            self._p["Ry pi"]["trigger"]
        ].phase_offset = self.phase

        # ======== Writing delays into the pulse generator registers
        self.qic.sequencer.set_delay_register(
            2, self._p["Ry pi"]["length"] + self.delay_between_pi
        )  # delay pi -> pi
        # The following delays are updated directly before the measurement
        self.qic.sequencer.set_delay_register(
            1, self._p["Rx pi/2"]["length"] + 0
        )  # delay pi/2 -> pi
        self.qic.sequencer.set_delay_register(
            3, self._p["Ry pi"]["length"] + 0
        )  # delay pi -> pi/2

        def _sequence(code):
            # 1st pi/2 pulse
            code.trigger_registered(
                register=1, manipulation=self._p["Rx pi/2"]["trigger"]
            )

            # pi pulses in between pi/2-pulses
            for _ in range(self.number_of_pi_pulses - 1):
                # accounts for number_of_pi_pulses-1 pi pulses
                code.trigger_registered(
                    register=2, manipulation=self._p["Ry pi"]["trigger"]
                )
            # last (number_of_pi_pulses-th) pi-pulse --> has different delay
            code.trigger_registered(
                register=3, manipulation=self._p["Ry pi"]["trigger"]
            )

            # last pi/2-pulse
            code.trigger_immediate(
                delay=self._p["Rx pi/2"]["length"],
                manipulation=self._p["Rx pi/2"]["trigger"],
            )

        self._built_code_from_sequences({"exp": _sequence})

    def _record_internal(self):
        return self._record_internal_1d(
            np.array(self.delays) / 2.0, "Delays", self._single_execution
        )
