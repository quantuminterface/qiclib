"""
This package provides everything related to coding with `QiCode`.
From this package, everything required to write QiCode can be imported.
For convenience, one usually star-imports everything from this module, i.e.

.. code-block:: python

    from qicode import *

to have access to all QiCode Commands.
"""

from qicode.compiled_job import CompiledJob
from qicode.qi_cell import QiCell, QiCells, QiCoupler, QiCouplers
from qicode.qi_command import (
    ASM,
    Assign,
    DigitalTrigger,
    Else,
    ForRange,
    If,
    Parallel,
    Play,
    PlayFlux,
    PlayReadout,
    QiGate,
    Recording,
    RotateFrame,
    Store,
    Sync,
    Wait,
    While,
)
from qicode.qi_expression import (
    ExpressionLike,
    QiAmplitudeValue,
    QiAmplitudeVariable,
    QiCellProperty,
    QiConst,
    QiExpression,
    QiFrequencyValue,
    QiFrequencyVariable,
    QiIntVariable,
    QiNormalValue,
    QiPhaseValue,
    QiPhaseVariable,
    QiStateValue,
    QiStateVariable,
    QiTimeValue,
    QiTimeVariable,
    QiVariable,
    VariableRef,
)
from qicode.qi_job import QiJob
from qicode.qi_pulse import QiPulse, QiShape
from qicode.qi_type import QiType

__all__ = [
    "ASM",
    "Assign",
    "CompiledJob",
    "DigitalTrigger",
    "Else",
    "ExpressionLike",
    "ForRange",
    "If",
    "Parallel",
    "Play",
    "PlayFlux",
    "PlayReadout",
    "QiAmplitudeValue",
    "QiAmplitudeVariable",
    "QiCell",
    "QiCellProperty",
    "QiCells",
    "QiConst",
    "QiCoupler",
    "QiCouplers",
    "QiExpression",
    "QiFrequencyValue",
    "QiFrequencyVariable",
    "QiGate",
    "QiIntVariable",
    "QiJob",
    "QiNormalValue",
    "QiPhaseValue",
    "QiPhaseVariable",
    "QiPulse",
    "QiShape",
    "QiStateValue",
    "QiStateVariable",
    "QiTimeValue",
    "QiTimeVariable",
    "QiType",
    "QiVariable",
    "Recording",
    "RotateFrame",
    "Store",
    "Sync",
    "VariableRef",
    "Wait",
    "While",
]
