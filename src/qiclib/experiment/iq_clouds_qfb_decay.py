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
"""This file contains the IQCloudsQFBDecay experiment description for the QiController."""

from qiclib.experiment.iq_clouds import IQClouds


class IQCloudsQFBDecay(IQClouds):
    """Experiment preparing the qubit state by a pi pulse followed by a specified delay
    and then performing an active reset quantum feedback operation and a final measurement.

    :param controller:
        The QiController driver
    :param delay:
        The delay between pi pulse and active reset.
    :param count:
        The number of IQ points received (the default is 100k)
    """

    def __init__(self, controller, delay=0, count=100000):
        super().__init__(controller, 0, count)
        self.delay = delay

    def _configure_sequences(self):
        pi_pulse = self._p["Rx pi"]

        self._built_code_from_sequences(
            {
                "exp": lambda code: (
                    code.trigger_immediate(
                        delay=pi_pulse["length"] + self.delay,
                        manipulation=pi_pulse["trigger"],
                    ).trigger_active_reset(
                        pi_trigger=pi_pulse["trigger"], pi_length=pi_pulse["length"]
                    )
                )
            }
        )
