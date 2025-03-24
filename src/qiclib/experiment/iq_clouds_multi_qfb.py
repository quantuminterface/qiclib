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
"""This file contains the IQCloudsMultiQFB experiment description for the QiController."""

from qiclib.experiment.iq_clouds import IQClouds


class IQCloudsMultiQFB(IQClouds):
    """Experiment preparing the qubit state and then performing
    *repetitions* active reset quantum feedback operations
    returning the resulting IQ fourier coefficients.

    :param controller:
        The QiController driver
    :param state:
        The state in which the qubit should be initialized (the default is 0)
    :param count:
        The number of IQ points received (the default is 100k)
    :param repetitions:
        The number of active resets to perform in a row before final readout.
    """

    def __init__(self, controller, state=0, count=100000, repetitions=1, delay=0):
        super().__init__(controller, 0, count)
        self.repetitions = repetitions
        self.delay = delay

    def _configure_sequences(self):
        def _sequence(code):
            pi_pulse = self._p["Rx pi"]
            if self.state == 1:
                # Prepare initial state to |1>
                code.trigger_immediate(
                    pi_pulse["length"], manipulation=pi_pulse["trigger"]
                )

            for _ in range(self.repetitions):
                if self.delay > 0:
                    code.trigger_immediate(self.delay)
                code.trigger_active_reset(
                    pi_trigger=pi_pulse["trigger"], pi_length=pi_pulse["length"]
                )

        self._built_code_from_sequences({"exp": _sequence})
