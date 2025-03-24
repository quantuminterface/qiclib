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
"""This file contains the InvertedT1 experiment for the QiController."""

from qiclib.experiment.t1 import T1


class InvertedT1(T1):
    r"""Experiment that measures the decay out of a initialized \|0> state
    into thermal equilibrium.

    At the beginning, the qubit is prepared in state \|0>
    followed by some delay as in a T1 measurement where the qubit state thermalizes.

    .. note::
        Readout pulse (on register 1) has to be configured separately!
        Also, the state discrimination needs to be configured and checked beforehand.

    :param controller:
        The QiController driver
    :param delays:
        The delays between pi pulse and readout (the default is from 0 to 1000ns in 24ns steps)
    :param repetition_time:
        The delay between the recording finishes and the next repetition starts.
    """

    def __init__(self, controller, delays=None, repetition_time=None):
        super().__init__(controller)
        if delays:
            self.delays = delays

        # Activate reset
        self.set_qubit_initialization(0, 0, repetition_time)

    def _single_execution(self, delay):
        # This function must be overwritten as the delay does not include a pi pulse here
        return {"sequencer_start": self._pc_dict["exp"], "delay_registers": [delay]}
