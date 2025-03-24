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
"""This file contains the Active Reset version of a T1 experiment for the QiController."""

from qiclib.experiment.t1 import T1


class ActiveResetT1(T1):
    r"""Experiment to demonstrate quantum feedback by actively resetting the qubit to state \|0>
    by measuring it, applying a pi pulse if state is detected to be \|1>
    and finally performing another readout to check on the pulse.

    At the beginning, the qubit is prepared in state \|1>
    and some delay as in a T1 measurement is included.
    By performing this experiment twice, one time with valid stater config
    and once with some artificial values so the QiController detects the qubit always in state \|0>
    we can compare the normal T1 decay with an actively resetted version.
    If the states are perfectly separable and we have no response delay,
    we would simply get always state 0 after active reset.
    As this will most likely not be the case, at least a suppression should be visible
    compared to the normal T1.
    """

    def _configure_sequences(self):
        # Initial delay between start of pi pulse and start of reset
        self.qic.sequencer.set_delay_register(1, self._p["Rx pi"]["length"])

        self._built_code_from_sequences(
            {
                # Pi pulse + delay
                "exp": lambda code: (
                    code.trigger_registered(
                        1, manipulation=self._p["Rx pi"]["trigger"]
                    ).trigger_active_reset(
                        pi_trigger=self._p["Rx pi"]["trigger"],
                        pi_length=self._p["Rx pi"]["length"],
                    )
                )
            }
        )
