from collections.abc import Iterable as _Iterable
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf.internal import containers as _containers

DESCRIPTOR: _descriptor.FileDescriptor

class SampleablePulse(_message.Message):
    __slots__ = (
        "amplitude",
        "hold",
        "index",
        "length",
        "phase",
        "shape",
        "shift_phase",
    )
    AMPLITUDE_FIELD_NUMBER: _ClassVar[int]
    INDEX_FIELD_NUMBER: _ClassVar[int]
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    SHAPE_FIELD_NUMBER: _ClassVar[int]
    HOLD_FIELD_NUMBER: _ClassVar[int]
    PHASE_FIELD_NUMBER: _ClassVar[int]
    SHIFT_PHASE_FIELD_NUMBER: _ClassVar[int]
    amplitude: int
    index: int
    length: int
    shape: int
    hold: bool
    phase: int
    shift_phase: bool
    def __init__(
        self,
        amplitude: int | None = ...,
        index: int | None = ...,
        length: int | None = ...,
        shape: int | None = ...,
        hold: bool = ...,
        phase: int | None = ...,
        shift_phase: bool = ...,
    ) -> None: ...

class Code(_message.Message):
    __slots__ = ("assembly", "binary")
    class Binary(_message.Message):
        __slots__ = ("code",)
        CODE_FIELD_NUMBER: _ClassVar[int]
        code: _containers.RepeatedScalarFieldContainer[int]
        def __init__(self, code: _Iterable[int] | None = ...) -> None: ...

    class Assembly(_message.Message):
        __slots__ = ("code",)
        CODE_FIELD_NUMBER: _ClassVar[int]
        code: _containers.RepeatedScalarFieldContainer[str]
        def __init__(self, code: _Iterable[str] | None = ...) -> None: ...

    ASSEMBLY_FIELD_NUMBER: _ClassVar[int]
    BINARY_FIELD_NUMBER: _ClassVar[int]
    assembly: Code.Assembly
    binary: Code.Binary
    def __init__(
        self,
        assembly: Code.Assembly | _Mapping | None = ...,
        binary: Code.Binary | _Mapping | None = ...,
    ) -> None: ...

class CompiledJob(_message.Message):
    __slots__ = ("cells",)
    class Cell(_message.Message):
        __slots__ = (
            "code",
            "id",
            "manipulation_pulses",
            "original_recording_ids",
            "readout_pulses",
        )
        ID_FIELD_NUMBER: _ClassVar[int]
        CODE_FIELD_NUMBER: _ClassVar[int]
        ORIGINAL_RECORDING_IDS_FIELD_NUMBER: _ClassVar[int]
        MANIPULATION_PULSES_FIELD_NUMBER: _ClassVar[int]
        READOUT_PULSES_FIELD_NUMBER: _ClassVar[int]
        id: int
        code: Code
        original_recording_ids: _containers.RepeatedScalarFieldContainer[int]
        manipulation_pulses: _containers.RepeatedCompositeFieldContainer[
            SampleablePulse
        ]
        readout_pulses: _containers.RepeatedCompositeFieldContainer[SampleablePulse]
        def __init__(
            self,
            id: int | None = ...,
            code: Code | _Mapping | None = ...,
            original_recording_ids: _Iterable[int] | None = ...,
            manipulation_pulses: _Iterable[SampleablePulse | _Mapping] | None = ...,
            readout_pulses: _Iterable[SampleablePulse | _Mapping] | None = ...,
        ) -> None: ...

    CELLS_FIELD_NUMBER: _ClassVar[int]
    cells: _containers.RepeatedCompositeFieldContainer[CompiledJob.Cell]
    def __init__(
        self, cells: _Iterable[CompiledJob.Cell | _Mapping] | None = ...
    ) -> None: ...
