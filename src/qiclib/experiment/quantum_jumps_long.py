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
"""This file contains the IQCloud experiment description for the QiController."""

import datetime
import os

import numpy as np

from qiclib.experiment.quantum_jumps import QuantumJumps
from qiclib.packages.qkit_polyfill import QKIT_ENABLED, DateTimeGenerator


class QuantumJumpsLong(QuantumJumps):
    """Experiment performing many single-shot readouts and returning
    the calculated states.
    The data will be stored into the Qkit measurement folders.
    One file per iteration.

    .. warning::
        Readout pulse (on register 1) has to be configured separately!

    :param controller:
        The QiController driver
    :param count:
        The number of IQ points received
    :param averaging:
        If averaging on the card should be allowed (no real single-shot then)
        (the default is False)
    :param wait_time:
        The (minimum) time between two experiment repetitions on the QiController
    :param iterations:
        The number of iterations to perform. Each iteration happens on the QiController,
        and between two iterations the data is collected.
    """

    def __init__(
        self, controller, count=100000, averaging=False, wait_time=2e-6, iterations=1
    ):
        if not QKIT_ENABLED:
            raise RuntimeError(
                "This experiment can only be executed when Qkit is installed!"
            )
        super().__init__(controller, count, averaging, wait_time)
        self.raw_data = True  # Necessary to fetch the data
        self.iterations = int(iterations)
        self.dirname = "quantum-jumps"

    def record_internal(self):
        filename = DateTimeGenerator().new_filename(self.dirname)["_filepath"]
        filename_prefix = filename[:-3]
        directory = os.path.dirname(filename)
        if not os.path.exists(directory):
            os.makedirs(directory)

        self._create_progress(self.iterations, name="Iterations")

        for i in range(self.iterations):
            self.raw_data = True  # Ensure that we really get raw data
            data = super().record_internal()

            # Store data to file
            timestamp = (
                datetime.datetime.now().isoformat().split(".")[0].replace(":", "-")
            )
            description = f"{filename_prefix}_{i}_{timestamp}.dat"
            filename = os.path.join(directory, description)
            np.atleast_1d(data).astype("int32").tofile(filename)

            self._iterate_progress(name="Iterations")

            if len(data) < self.count / 32:
                # Not all results retrieved -> task was interrupted, exit
                raise RuntimeError(
                    "Not all data could be obtained. Experiment was probably interrupted. Aborting."
                )
