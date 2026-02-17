from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper

DESCRIPTOR: _descriptor.FileDescriptor

class Type(_message.Message):
    __slots__ = ("array", "scalar", "unknown")
    class Scalar(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        Time: _ClassVar[Type.Scalar]
        State: _ClassVar[Type.Scalar]
        Normal: _ClassVar[Type.Scalar]
        Frequency: _ClassVar[Type.Scalar]
        Phase: _ClassVar[Type.Scalar]
        Amplitude: _ClassVar[Type.Scalar]

    Time: Type.Scalar
    State: Type.Scalar
    Normal: Type.Scalar
    Frequency: Type.Scalar
    Phase: Type.Scalar
    Amplitude: Type.Scalar
    class Unknown(_message.Message):
        __slots__ = ()
        def __init__(self) -> None: ...

    class Array(_message.Message):
        __slots__ = ("length", "type")
        TYPE_FIELD_NUMBER: _ClassVar[int]
        LENGTH_FIELD_NUMBER: _ClassVar[int]
        type: Type
        length: int
        def __init__(
            self, type: Type | _Mapping | None = ..., length: int | None = ...
        ) -> None: ...

    SCALAR_FIELD_NUMBER: _ClassVar[int]
    UNKNOWN_FIELD_NUMBER: _ClassVar[int]
    ARRAY_FIELD_NUMBER: _ClassVar[int]
    scalar: Type.Scalar
    unknown: Type.Unknown
    array: Type.Array
    def __init__(
        self,
        scalar: Type.Scalar | str | None = ...,
        unknown: Type.Unknown | _Mapping | None = ...,
        array: Type.Array | _Mapping | None = ...,
    ) -> None: ...
