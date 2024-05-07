# Copyright © 2017-2023 Quantum Interface (quantuminterface@ipe.kit.edu)
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
import unittest
import warnings

from qiclib import QiController
from qiclib.code import *

from numpy.testing import assert_array_equal

import mocks
from mocks import (
    pimc,
    rfdc,
    unit_cell,
    sequencer,
    servicehub_control,
    recording,
    pulse_gen,
    taskrunner,
    digital_trigger,
)


@mocks.patch(
    pimc,
    rfdc,
    unit_cell,
    sequencer,
    servicehub_control,
    recording,
    pulse_gen,
    taskrunner,
    digital_trigger,
)
class TestExperiments(unittest.TestCase):
    def test_ExperimentReadout(self):
        controller = QiController("IP")
        with QiJob() as job:
            q = QiCells(1)
            Wait(q[0], delay=0)
        experiment = job.create_experiment(controller)
        amp, pha = experiment.readout.readout()
        assert_array_equal(amp, [[1.0], [2.0], [3.0]])
        assert_array_equal(pha, [[4.0], [5.0], [6.0]])

    @unittest.skip(
        "ignoring the error for now as it will become obsolete when the compiler gets pushed to the platform"
    )
    def test_does_not_raise_warning_when_using_a_variable_frequency(self):
        controller = QiController("IP")
        with QiJob() as job:
            q = QiCells(1)
            f = QiVariable()
            with ForRange(f, 0, 2, 1):
                PlayReadout(q[0], QiPulse(12e-6, frequency=f))
        experiment = job.create_experiment(controller)
        with warnings.catch_warnings(record=True) as w:
            experiment.run()
            self.assertFalse(
                [it for it in w if "Readout pulses without frequency" in str(it)],
                "There should be no warnings about readout pulses without frequency",
            )

    def test_raises_warning_when_no_readout_frequency_given(self):
        controller = QiController("IP")
        with QiJob() as job:
            q = QiCells(1)
            PlayReadout(q[0], QiPulse(12e-9, frequency=30e6))
            PlayReadout(q[0], QiPulse(12e-9, frequency=15e6))
        experiment = job.create_experiment(controller)
        print(experiment.qic.readout.internal_frequency)
        experiment.run()
        with self.assertWarnsRegex(
            UserWarning, "Readout pulses without frequency given"
        ):
            experiment.run()
