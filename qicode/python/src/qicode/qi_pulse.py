from __future__ import annotations

from typing import Literal, Protocol, runtime_checkable

from qicode.proto.pulse_pb2 import (
    ContinuousPulse,
    DiscretePulse,
    OffPulse,
    Pulse,
    Shape,
)
from qicode.qi_expression import ExpressionLike, QiExpression


@runtime_checkable
class QiShape(Protocol):
    def id(self) -> int: ...


SHAPE_ID_ZERO: int = 0
"""
Reserved ID for the zero shape (i.e., shape that is zero everywhere)
"""
SHAPE_ID_RECT: int = 1
"""
Reserved ID for the rectangular shape.
"""
SHAPE_ID_RESERVED_START: int = 2
SHAPE_ID_RESERVED_END: int = 0x7FFF


class QiPulse:
    def __init__(
        self,
        length: ExpressionLike | Literal["cw"] | Literal["off"],
        frequency: ExpressionLike | None = None,
        amplitude: ExpressionLike = 1.0,
        phase: ExpressionLike = 0.0,
        shape: QiShape | None = None,
        hold: bool = False,
    ) -> None:
        if shape is not None:
            assert isinstance(shape, QiShape), (
                "Shapes must conform to the QiShape protocol"
            )
        if isinstance(length, str) and length.lower() == "cw":
            self._pulse = Pulse(
                continuous=ContinuousPulse(
                    frequency=QiExpression.from_any(frequency)._proto()
                    if frequency is not None
                    else None,
                    amplitude=QiExpression.from_any(amplitude)._proto(),
                    phase=QiExpression.from_any(phase)._proto(),
                )
            )
        elif isinstance(length, str) and length.lower() == "off":
            self._pulse = Pulse(off=OffPulse())
        else:
            if shape is None:
                _shape = Shape(id=SHAPE_ID_RECT)
            else:
                _shape = Shape(id=shape.id())
            self._pulse = Pulse(
                discrete=DiscretePulse(
                    length=QiExpression.from_any(length)._proto(),
                    frequency=QiExpression.from_any(frequency)._proto()
                    if frequency is not None
                    else None,
                    amplitude=QiExpression.from_any(amplitude)._proto(),
                    phase=QiExpression.from_any(phase)._proto(),
                    hold=hold,
                    shape=_shape,
                )
            )

    @classmethod
    def off(cls):
        return QiPulse("off")

    @classmethod
    def cw(
        cls,
        frequency: QiExpression | int | float,
        amplitude: QiExpression | int | float = 1,
        phase: QiExpression | int | float = 0,
    ):
        return QiPulse("cw", frequency, amplitude, phase)

    def _proto(self) -> Pulse:
        return self._pulse

    def __str__(self) -> str:
        if self._pulse.HasField("continuous"):
            return f"QiPulse(cw, frequency={self._pulse.continuous.frequency}, amplitude={self._pulse.continuous.amplitude}, phase={self._pulse.continuous.phase})"
        elif self._pulse.HasField("off"):
            return "QiPulse(off)"
        else:  # discrete
            return f"QiPulse(length={self._pulse.discrete.length}, frequency={self._pulse.discrete.frequency}, amplitude={self._pulse.discrete.amplitude}, phase={self._pulse.discrete.phase}, hold={self._pulse.discrete.hold})"
