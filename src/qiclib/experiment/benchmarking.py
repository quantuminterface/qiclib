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
"""Module containing the benchmarking experiment."""

from qiclib.experiment.base import BaseExperiment


class Benchmarking(BaseExperiment):
    """Experiment that outputs a series of different pi and pi/2 pulses and measures qubit state.
    Performs all possible +-pi,+-pi/2 pulses around X and Y
    and all two pulse combinations of them and outputs the result.

    .. note::
        Readout pulse (on register 1) has to be configured separately!

    :param controller:
        The QiController Driver
    :param delay:
        The delay between two pulses if combined (the default is 0, i.e. no delay)
    """

    def __init__(self, controller, delay=0):
        super().__init__(controller)
        self.delay = delay
        self._pulse_combinations = []

    def _configure_sequences(self):
        pulses = [
            "Rx pi/2",
            "Rx -pi/2",
            "Ry pi/2",
            "Ry -pi/2",
            "Rx pi",
            "Rx -pi",
            "Ry pi",
            "Ry -pi",
        ]
        sequences = {}
        self._pulse_combinations = []

        def _add_sequence(name, sequence):
            self._pulse_combinations.append(name)
            sequences[name] = sequence

        # Readout in zero state
        _add_sequence("zero state", lambda code: None)

        # Single pulses
        def _sequence_single(pulse):
            # Extra function necessary because of closures
            # ("cell variable defined in loop")
            return lambda code: (
                code.trigger_immediate(
                    self._p[pulse]["length"], manipulation=self._p[pulse]["trigger"]
                )
            )

        for pulse in pulses:
            _add_sequence(f"single: {pulse}", _sequence_single(pulse))

        # Combination of two pulses
        def _sequence_two(pulse1, pulse2):
            return lambda code: (
                code.trigger_immediate(
                    self._p[pulse1]["length"] + self.delay,
                    manipulation=self._p[pulse1]["trigger"],
                ).trigger_immediate(
                    self._p[pulse2]["length"], manipulation=self._p[pulse2]["trigger"]
                )
            )

        for pulse1 in pulses:
            for pulse2 in pulses:
                _add_sequence(f"{pulse1}, {pulse2}", _sequence_two(pulse1, pulse2))

        # Load sequencer code
        self._built_code_from_sequences(sequences)

    def _record_internal(self):
        """
        This method describes the experimental procedure on the measurement pc.

        As the sequencer code consists out of multiple measurements separated by the END command
        we start at a different program counter for each pulse combination.
        """
        if not self._pulse_combinations or not self._pc_dict:
            raise Warning(
                "Experiment needs to be initialized first. Please use run() to start the experiment."
            )

        return self._record_internal_1d(
            self._pulse_combinations,
            "Pulse Combination",
            lambda pulse: {"sequencer_start": self._pc_dict[pulse]},
        )

    prediction = (
        0.0,  # zero state
        0.5,  # Rx pi/2
        0.5,  # Rx -pi/2
        0.5,  # Ry pi/2
        0.5,  # Ry -pi/2
        1.0,  # Rx pi
        1.0,  # Rx -pi
        1.0,  # Ry pi
        1.0,  # Ry -pi
        1.0,  # Rx pi/2, Rx pi/2
        0.0,  # Rx pi/2, Rx -pi/2
        0.5,  # Rx pi/2, Ry pi/2
        0.5,  # Rx pi/2, Ry -pi/2
        0.5,  # Rx pi/2, Rx pi
        0.5,  # Rx pi/2, Rx -pi
        0.5,  # Rx pi/2, Ry pi
        0.5,  # Rx pi/2, Ry -pi
        0.0,  # Rx -pi/2, Rx pi/2
        1.0,  # Rx -pi/2, Rx -pi/2
        0.5,  # Rx -pi/2, Ry pi/2
        0.5,  # Rx -pi/2, Ry -pi/2
        0.5,  # Rx -pi/2, Rx pi
        0.5,  # Rx -pi/2, Rx -pi
        0.5,  # Rx -pi/2, Ry pi
        0.5,  # Rx -pi/2, Ry -pi
        0.5,  # Ry pi/2, Rx pi/2
        0.5,  # Ry pi/2, Rx -pi/2
        1.0,  # Ry pi/2, Ry pi/2
        0.0,  # Ry pi/2, Ry -pi/2
        0.5,  # Ry pi/2, Rx pi
        0.5,  # Ry pi/2, Rx -pi
        0.5,  # Ry pi/2, Ry pi
        0.5,  # Ry pi/2, Ry -pi
        0.5,  # Ry -pi/2, Rx pi/2
        0.5,  # Ry -pi/2, Rx -pi/2
        0.0,  # Ry -pi/2, Ry pi/2
        1.0,  # Ry -pi/2, Ry -pi/2
        0.5,  # Ry -pi/2, Rx pi
        0.5,  # Ry -pi/2, Rx -pi
        0.5,  # Ry -pi/2, Ry pi
        0.5,  # Ry -pi/2, Ry -pi
        0.5,  # Rx pi, Rx pi/2
        0.5,  # Rx pi, Rx -pi/2
        0.5,  # Rx pi, Ry pi/2
        0.5,  # Rx pi, Ry -pi/2
        0.0,  # Rx pi, Rx pi
        0.0,  # Rx pi, Rx -pi
        0.0,  # Rx pi, Ry pi
        0.0,  # Rx pi, Ry -pi
        0.5,  # Rx -pi, Rx pi/2
        0.5,  # Rx -pi, Rx -pi/2
        0.5,  # Rx -pi, Ry pi/2
        0.5,  # Rx -pi, Ry -pi/2
        0.0,  # Rx -pi, Rx pi
        0.0,  # Rx -pi, Rx -pi
        0.0,  # Rx -pi, Ry pi
        0.0,  # Rx -pi, Ry -pi
        0.5,  # Ry pi, Rx pi/2
        0.5,  # Ry pi, Rx -pi/2
        0.5,  # Ry pi, Ry pi/2
        0.5,  # Ry pi, Ry -pi/2
        0.0,  # Ry pi, Rx pi
        0.0,  # Ry pi, Rx -pi
        0.0,  # Ry pi, Ry pi
        0.0,  # Ry pi, Ry -pi
        0.5,  # Ry -pi, Rx pi/2
        0.5,  # Ry -pi, Rx -pi/2
        0.5,  # Ry -pi, Ry pi/2
        0.5,  # Ry -pi, Ry -pi/2
        0.0,  # Ry -pi, Rx pi
        0.0,  # Ry -pi, Rx -pi
        0.0,  # Ry -pi, Ry pi
        0.0,  # Ry -pi, Ry -pi
    )
