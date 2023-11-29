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
"""This script is the central place to store constants used in other scripts."""

import numpy as np

CONTROLLER_FREQUENCY_IN_HZ = 250e6  # Hz
CONTROLLER_CYCLE_TIME = 1.0 / CONTROLLER_FREQUENCY_IN_HZ  # s

CONTROLLER_SAMPLES_PER_CYCLE = 4

CONTROLLER_NCO_PHASE_VALUE_PER_PHASE = 2**16 / (2 * np.pi)
CONTROLLER_NCO_PHASE_INCREMENT_PER_HZ = 2**30 / CONTROLLER_FREQUENCY_IN_HZ

CONTROLLER_SAMPLE_FREQUENCY_IN_HZ = (
    CONTROLLER_FREQUENCY_IN_HZ * CONTROLLER_SAMPLES_PER_CYCLE
)

CONTROLLER_AMPLITUDE_MAX_VALUE = (1 << 16) - 1

# 0x1000 Memory size, 2 bytes per value and 2 values (I/Q) per sample
RECORDING_MAX_RAW_SAMPLES = int(0x1000 / (2 * 2))
