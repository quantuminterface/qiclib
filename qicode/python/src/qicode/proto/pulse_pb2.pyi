from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message

from qicode.proto import expression_pb2 as _expression_pb2

DESCRIPTOR: _descriptor.FileDescriptor

class DiscretePulse(_message.Message):
    __slots__ = (
        "amplitude",
        "frequency",
        "hold",
        "length",
        "phase",
        "shape",
        "shiftPhase",
    )
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    AMPLITUDE_FIELD_NUMBER: _ClassVar[int]
    PHASE_FIELD_NUMBER: _ClassVar[int]
    FREQUENCY_FIELD_NUMBER: _ClassVar[int]
    SHAPE_FIELD_NUMBER: _ClassVar[int]
    HOLD_FIELD_NUMBER: _ClassVar[int]
    SHIFTPHASE_FIELD_NUMBER: _ClassVar[int]
    length: _expression_pb2.Expression
    amplitude: _expression_pb2.Expression
    phase: _expression_pb2.Expression
    frequency: _expression_pb2.Expression
    shape: Shape
    hold: bool
    shiftPhase: bool
    def __init__(
        self,
        length: _expression_pb2.Expression | _Mapping | None = ...,
        amplitude: _expression_pb2.Expression | _Mapping | None = ...,
        phase: _expression_pb2.Expression | _Mapping | None = ...,
        frequency: _expression_pb2.Expression | _Mapping | None = ...,
        shape: Shape | _Mapping | None = ...,
        hold: bool = ...,
        shiftPhase: bool = ...,
    ) -> None: ...

class ContinuousPulse(_message.Message):
    __slots__ = ("amplitude", "frequency", "phase", "shape")
    AMPLITUDE_FIELD_NUMBER: _ClassVar[int]
    PHASE_FIELD_NUMBER: _ClassVar[int]
    FREQUENCY_FIELD_NUMBER: _ClassVar[int]
    SHAPE_FIELD_NUMBER: _ClassVar[int]
    amplitude: _expression_pb2.Expression
    phase: _expression_pb2.Expression
    frequency: _expression_pb2.Expression
    shape: Shape
    def __init__(
        self,
        amplitude: _expression_pb2.Expression | _Mapping | None = ...,
        phase: _expression_pb2.Expression | _Mapping | None = ...,
        frequency: _expression_pb2.Expression | _Mapping | None = ...,
        shape: Shape | _Mapping | None = ...,
    ) -> None: ...

class OffPulse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Pulse(_message.Message):
    __slots__ = ("continuous", "discrete", "off")
    DISCRETE_FIELD_NUMBER: _ClassVar[int]
    CONTINUOUS_FIELD_NUMBER: _ClassVar[int]
    OFF_FIELD_NUMBER: _ClassVar[int]
    discrete: DiscretePulse
    continuous: ContinuousPulse
    off: OffPulse
    def __init__(
        self,
        discrete: DiscretePulse | _Mapping | None = ...,
        continuous: ContinuousPulse | _Mapping | None = ...,
        off: OffPulse | _Mapping | None = ...,
    ) -> None: ...

class Shape(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    def __init__(self, id: int | None = ...) -> None: ...
