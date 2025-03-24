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
"""This file contains the RabiShort experiment description for the QiController."""

import qiclib.packages.utility as util

from .rabi import Rabi


class RabiShort(Rabi):
    r"""Rabi experiment driving the qubit between the states \|0> and \|1>.
    Especially built for short pi pulses that need higher accuracy than
    the one clock cycle offered by the standard Rabi experiment.
    In this case the full sample rate can be used.

    .. warning::
        Readout pulse (on register 1) has to be configured separately!

    :param controller:
        The QiController driver
    :param durations:
        The durations of the manipulation pulse
    """

    def __init__(self, controller, durations):
        super().__init__(controller)
        self.durations = durations

    def _configure_drive_pulses(self):
        super()._configure_drive_pulses(
            {
                "0 sample": {
                    "trigger": 14,
                    "length": util.conv_cycles_to_time(1),
                    "amplitude": 0,
                },
                "1 sample": {"trigger": 1, "length": util.conv_samples_to_time(1)},
                "2 sample": {"trigger": 2, "length": util.conv_samples_to_time(2)},
                "3 sample": {"trigger": 3, "length": util.conv_samples_to_time(3)},
                "Rx pi": {
                    "trigger": 4,
                    "length": self.qic.sample.tpi,
                    "amplitude": 1,
                    "phase": 0,
                },
                "Drive on": {
                    "trigger": 13,
                    "length": util.conv_cycles_to_time(1),
                    "hold": True,
                },
            }
        )

    def _configure_sequences(self):
        # Duration of the pulse will be written into the delay register
        # Register is initialized with 1 clock cycle delay
        self.qic.sequencer.set_delay_register(1, None, clock_cycles=1)

        self._built_code_from_sequences(
            {
                # One clock cycle delay (to simulate turning off the Drive which also takes 1 cycle at '4 sample')
                "0 sample": lambda code: code.trigger_immediate(
                    manipulation=self._p["0 sample"]["trigger"]
                ),
                "1 sample": lambda code: code.trigger_immediate(
                    manipulation=self._p["1 sample"]["trigger"]
                ),
                "2 sample": lambda code: code.trigger_immediate(
                    manipulation=self._p["2 sample"]["trigger"]
                ),
                "3 sample": lambda code: code.trigger_immediate(
                    manipulation=self._p["3 sample"]["trigger"]
                ),
                "4 sample": lambda code: (
                    code.trigger_registered(
                        1, manipulation=self._p["Drive on"]["trigger"]
                    ).trigger_immediate(manipulation=self._p["0 sample"]["trigger"])
                ),
                "5 sample": lambda code: (
                    code.trigger_registered(
                        1, manipulation=self._p["Drive on"]["trigger"]
                    ).trigger_immediate(manipulation=self._p["1 sample"]["trigger"])
                ),
                "6 sample": lambda code: (
                    code.trigger_registered(
                        1, manipulation=self._p["Drive on"]["trigger"]
                    ).trigger_immediate(manipulation=self._p["2 sample"]["trigger"])
                ),
                "7 sample": lambda code: (
                    code.trigger_registered(
                        1, manipulation=self._p["Drive on"]["trigger"]
                    ).trigger_immediate(manipulation=self._p["3 sample"]["trigger"])
                ),
            }
        )

    def _single_execution(self, duration):
        samples = util.conv_time_to_samples(duration, round_cycles=False)
        # samples 4 -> 1 cycle, 7 -> 1, 8 -> 2, 9 -> 2, ...
        cycles = int(util.conv_samples_to_cycles(samples + 1) - 1)
        self.qic.sequencer.set_delay_register(1, None, clock_cycles=cycles)

        if cycles > 1:
            # 8+ samples: Modify for right sequencer command
            samples = samples - util.conv_cycles_to_samples(cycles - 1)

        self.qic.sequencer.start_at(self._pc_dict[f"{samples} sample"])
