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
"""This file contains the IQCloudsRamsey experiment description for the QiController."""

from qiclib.experiment.iq_clouds import IQClouds


class IQCloudsRamsey(IQClouds):
    """Experiment performing a ramsey experiment with fixed *delay* between pi/2 pulses,
    performing many measurements and finally returning many single-shot results as IQCloud.

    :param controller:
        The QiController driver
    :param delay:
        The delay between the ramsey pi/2 pulses.
    :param count:
        The number of IQ points received (the default is 100k)
    """

    def __init__(self, controller, delay, count=100000):
        super().__init__(controller, 0, count)
        self.delay = delay

    def _configure_sequences(self):
        pi2_pulse = self._p["Rx pi/2"]

        self._built_code_from_sequences(
            {
                "exp": lambda code: (
                    code.trigger_immediate(
                        delay=pi2_pulse["length"] + self.delay,
                        manipulation=pi2_pulse["trigger"],
                    ).trigger_immediate(
                        delay=pi2_pulse["length"], manipulation=pi2_pulse["trigger"]
                    )
                )
            }
        )
