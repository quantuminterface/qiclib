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
"""This file contains the MultiPi experiment description for the QiController."""

import warnings

from qiclib.experiment.base import BaseExperiment


class MultiPi(BaseExperiment):
    """
    Experiment to check fidelity of pi pulse. Executes an increasing number of pi pulses.
    State should swap with each added pi pulse, but errors will cause result to deviate
    further and further for an increasing number of pi pulses.

    .. deprecated::
        MultiPi is deprecated. Please use the new QiCode syntax instead, see
        `qiclib.code`, i.e. write your own `qiclib.code.qi_jobs.QiJob` or use the one
        defined in `qiclib.experiment.qicode.collection` by calling
        `qiclib.jobs.MultiPi(max, step, min)`.



    .. warning::
        Readout pulse (on register 1) has to be configured separately!

    :param controller:
        The QiController driver
    :param max_count:
        The maximum number of pi pulses to perform.
    """

    def __init__(self, controller, max_count, pulse_delay=0):
        super().__init__(controller)

        self.pulse_delay = pulse_delay

        import numpy as np

        self.pulse_counts = np.arange(max_count + 1, dtype=int)

        warnings.warn(
            "MultiPi is deprecated. Please use the new QiCode syntax instead, i.e. "
            "write your own `QiJob` or use the one defined in `qiclib.jobs` by calling "
            "`qiclib.jobs.MultiPi(max, step, min)`.",
            FutureWarning,
        )

    # pylint: disable=arguments-differ
    def _configure_sequences(self, pulse_count=0):
        # Initial delay between start of pi pulse and start of measurement
        self.qic.sequencer.set_delay_register(
            1, self._p["Rx pi"]["length"] + self.pulse_delay
        )

        def _sequence(code):
            for i in range(pulse_count):
                if i == pulse_count - 1:
                    # Last pulse -> do not wait with readout after pulse
                    code.trigger_immediate(
                        delay=self._p["Rx pi"]["length"],
                        manipulation=self._p["Rx pi"]["trigger"],
                    )
                else:
                    code.trigger_registered(
                        register=1, manipulation=self._p["Rx pi"]["trigger"]
                    )

        self._built_code_from_sequences({"exp": _sequence})

    def _record_internal(self):
        """
        This method describes the experimental procedure on the measurement pc.
        """
        if self.use_taskrunner:
            warnings.warn("Taskrunner mode is not (yet) supported by this experiment!")
            self.use_taskrunner = False

        return self._record_internal_1d(
            self.pulse_counts, "Pulse count", self._single_execution
        )

    def _single_execution(self, pulse_count):
        self._configure_sequences(pulse_count)
        return {"sequencer_start": self._pc_dict["exp"], "delay_registers": []}
