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
"""File providing TestTwoPulse QiController Experiment."""

import warnings

import qiclib.packages.utility as util
from qiclib.coding.sequencercode import SequencerCode
from qiclib.experiment.base import BaseExperiment


class TestTwoPulse(BaseExperiment):
    """Experiment that outputs two configurable square shaped pulses.

    .. deprecated::
        TestTwoPulse is deprecated. Please use the new QiCode syntax instead, see
        `qiclib.code`, i.e. write your own `qiclib.code.qi_jobs.QiJob` or use a
        predefined one from `qiclib.experiment.qicode.collection`.

    Remark: No readout pulse is included.

    :param controller:
        The QiController driver
    :param delay:
        The delay between the two pulses
    :param p1_pulse:
        The duration of the first pulse
    :param p1_phase:
        The phase of the first pulse
    :param p1_ampl:
        The amplitude of the first pulse, can also be complex
    :param p2_pulse:
        The duration of the second pulse
    :param p2_phase:
        The phase of the second pulse
    :param p2_ampl:
        The amplitude of the second pulse, can also be complex
    """

    # TODO Refactor pulse settings to own struct/interface/whatsoever. 3 args -> 1 arg
    def __init__(
        self,
        controller,
        delay=16e-9,
        p1_pulse=32e-9,
        p1_phase=0,
        p1_ampl=1,
        p2_pulse=32e-9,
        p2_phase=0,
        p2_ampl=1,
    ):
        """ """
        super().__init__(controller)

        self.p1_pulse = p1_pulse
        self.p2_pulse = p2_pulse

        self.delay = delay
        self.p1_phase = p1_phase
        self.p2_phase = p2_phase
        self.p1_ampl = p1_ampl
        self.p2_ampl = p2_ampl
        warnings.warn(
            "TestTwoPulse is deprecated. Please use the new QiCode syntax instead, i.e."
            " write your own `QiJob` or use a predefined one from `qiclib.jobs`.",
            FutureWarning,
        )

    def configure(self):
        """Prepares everything for the execution of the experiment."""

        # check if this method was called
        self._configure_called = True

        # Generating pulses to be loading into the manipulation pulse generator
        pulse1 = util.generate_pulseform(self.p1_pulse, align="end")
        pulse2 = util.generate_pulseform(self.p2_pulse, align="start")

        # Reset pulse generator envelope memory
        self.qic.manipulation.reset_env_mem()

        # Loading pulse shapes into the pulse generator
        self.qic.manipulation.triggerset[1].load_pulse(pulse1, self.p1_phase)
        self.qic.manipulation.triggerset[2].load_pulse(pulse2, self.p2_phase)

        # Writing delays into the sequencer delay registers
        self.qic.sequencer.set_delay_register(1, self.p1_pulse + self.delay)

        # Writing program for the sequencer
        code = SequencerCode()
        code.trigger_nco_sync()

        code.trigger_registered(register=1, manipulation=1)
        code.trigger_immediate(delay=self.p2_pulse, manipulation=2)
        code.end_of_experiment(decay_time=self.qic.sample.T_rep)

        # Load sequencer code
        self.qic.sequencer.load_program(code)
