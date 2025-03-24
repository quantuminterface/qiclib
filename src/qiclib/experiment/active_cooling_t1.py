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
"""Module containing the ActiveCoolingT1 experiment for the QiController."""

import time

import numpy as np

from .t1 import T1


class ActiveCoolingT1(T1):
    """T1 experiments where waiting times are filled with repeated Active Resets.


    :param controller:
        The QiController driver
    :type controller: qiclib.hardware.controller.QiController
    :param delays:
        List of delays for the T1 experiment.
    :type delays: List[float]
    :param reset_pulses:
        Number of reset pulses after each experiment execution
    :type reset_pulses: int
    :param reset_delay:
        Delay between single AR executions (lower boundary, defaults to 0)
    :type reset_delay: float, optional
    :param averages:
        Number of averages to perform of [Exp, Cooling] (defaults to 100)
    :type averages: int, optional

    .. note::
        Readout pulse (on register 1) has to be configured separately!
        Also, the state discrimination needs to be configured and checked beforehand.
    """

    def __init__(self, controller, delays, reset_pulses, reset_delay=0, averages=100):
        super().__init__(controller)
        self.delays = delays

        self.reset_delay = reset_delay
        self.busy_sleep_delay = 0.1
        self.averages = averages
        self.reset_pulses = reset_pulses

        if not self.qic.taskrunner_available:
            raise NotImplementedError("This experiment requires the Taskrunner to work")

    def _configure_sequences(self):
        pi_pulse = self._p["Rx pi"]
        # Initial delay between start of pi pulse and start of measurement
        self.qic.sequencer.set_delay_register(1, pi_pulse["length"])

        self._built_code_from_sequences(
            {
                # Pi pulse + delay
                "exp": lambda code: code.trigger_registered(
                    1, manipulation=pi_pulse["trigger"]
                ),
                "cooling": lambda code: (
                    code.trigger_active_reset(
                        pi_pulse["trigger"], pi_pulse["length"]
                    ).end_of_experiment(self.reset_delay)
                ),
            }
        )

    def _configure_taskrunner(self):
        self.qic.taskrunner.load_task_source("active_cooling.c", "ActiveCooling")
        self.qic.taskrunner.set_param_list(
            [
                self._pc_dict["exp"],
                self._pc_dict["cooling"],
                self.reset_pulses,
                self.averages,
            ]
        )

    def _single_execution(self, delay):
        self.qic.sequencer.set_delay_register(1, self._p["Rx pi"]["length"] + delay)
        # Do not start sequencer here as task will do that

    def _record_internal_1d(self, variable, name, inner_function):
        """Experiment specific overwrite."""
        count = len(variable)
        sig_amp = np.zeros(count)
        sig_pha = np.zeros(count)

        old_avg = self.qic.sequencer.averages

        # Looping through the different values of the variable
        self._create_progress(count, name)
        try:
            self.qic.sequencer.averages = 1
            for idx, value in enumerate(variable):
                # Set configuration
                inner_function(value)

                # Start execution on the QiController
                self.qic.taskrunner.start_task()

                # Wait until result is available
                while self.qic.taskrunner.busy:
                    time.sleep(self.busy_sleep_delay)

                data = self.qic.taskrunner.get_databoxes_INT32()
                compl = data[0] + 1j * data[1]
                # amp, pha = self._measure_amp_pha(False)
                sig_amp[idx] = np.abs(compl) / self.averages
                sig_pha[idx] = np.angle(compl)

                self._iterate_progress(name)
        finally:
            self.qic.taskrunner.stop_task()
            self.qic.sequencer.averages = old_avg
        return [(sig_amp, sig_pha)]
