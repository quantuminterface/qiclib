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
"""This file contains the MultiPiT1 experiment description for the QiController."""

from .t1 import T1


class MultiPiT1(T1):
    """
    Experiment that conditions the qubit with a number of initial pi pulses.
    Afterwards a normal T1 measurement is executed.

    The experiment is based on the paper by Simon Gustavsson et al. (MIT):
    https://arxiv.org/pdf/1612.08462.pdf

    .. warning::
        Readout pulse (on register 1) has to be configured separately!

    :param controller:
        The QiController driver
    :param delays:
        The delays between (final) pi pulse and readout
    :param pi_count:
        The number of initial conditioning pi pulses to perform.
    :param pi_delay:
        The delay between the pi pulse (defaults to 0ns, so no delay)
    """

    def __init__(self, controller, delays, pi_count, pi_delay=0, reset_before_t1=False):
        super().__init__(controller)
        self.delays = delays

        self.pi_delay = pi_delay
        self.pi_count = pi_count
        self.reset_before_t1 = reset_before_t1

    def _configure_sequences(self):
        pi_pulse = self._p["Rx pi"]
        # Initial delay between start of pi pulse and start of measurement
        self.qic.sequencer.set_delay_register(10, pi_pulse["length"] + self.pi_delay)

        # Initial delay for the T1 experiment
        self.qic.sequencer.set_delay_register(1, pi_pulse["length"])

        def _sequence(code):
            for _ in range(self.pi_count):
                code.trigger_registered(register=10, manipulation=pi_pulse["trigger"])
            if self.reset_before_t1:
                code.trigger_active_reset(pi_pulse["trigger"], pi_pulse["length"], 0)
            code.trigger_registered(register=1, manipulation=pi_pulse["trigger"])

        self._built_code_from_sequences({"exp": _sequence})
