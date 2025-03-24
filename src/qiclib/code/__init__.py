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
"""
This package provides everything related to coding with `QiCode`.
From this package, everything required to write QiCode can be imported.
For convenience, one usually star-imports everything from this module, i.e.

.. code-block:: python

    from qiclib.code import *

to have access to all QiCode Commands.

Additionally, this package also contains the compiler that transforms `QiCode` into binary code
that is fed to the QiController.
"""

from . import qi_seq_instructions
from .qi_jobs import (
    Assign,
    DigitalTrigger,
    Else,
    ForRange,
    If,
    Parallel,
    Play,
    PlayFlux,
    PlayReadout,
    QiAmplitudeVariable,
    QiCell,
    QiCells,
    QiCoupler,
    QiCouplers,
    QiFrequencyVariable,
    QiGate,
    QiIntVariable,
    QiJob,
    QiPhaseVariable,
    QiStateVariable,
    QiTimeVariable,
    QiVariable,
    Recording,
    RotateFrame,
    Sync,
    Wait,
)
from .qi_pulse import QiPulse, ShapeLib
from .qi_result import QiResult
from .qi_sample import QiSample

__all__ = [
    "Assign",
    "DigitalTrigger",
    "Else",
    "ForRange",
    "If",
    "Parallel",
    "Play",
    "PlayFlux",
    "PlayReadout",
    "QiAmplitudeVariable",
    "QiCell",
    "QiCells",
    "QiCoupler",
    "QiCouplers",
    "QiFrequencyVariable",
    "QiGate",
    "QiIntVariable",
    "QiJob",
    "QiPhaseVariable",
    "QiPulse",
    "QiResult",
    "QiSample",
    "QiStateVariable",
    "QiTimeVariable",
    "QiVariable",
    "Recording",
    "RotateFrame",
    "ShapeLib",
    "Sync",
    "Wait",
    "qi_seq_instructions",
]
