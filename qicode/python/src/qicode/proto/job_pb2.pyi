from collections.abc import Iterable as _Iterable
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf.internal import containers as _containers

from qicode.proto import cell_pb2 as _cell_pb2
from qicode.proto import commands_pb2 as _commands_pb2

DESCRIPTOR: _descriptor.FileDescriptor

class Job(_message.Message):
    __slots__ = ("cells", "commands", "couplers", "ncoSyncLength", "skipNcoSync")
    COMMANDS_FIELD_NUMBER: _ClassVar[int]
    CELLS_FIELD_NUMBER: _ClassVar[int]
    COUPLERS_FIELD_NUMBER: _ClassVar[int]
    SKIPNCOSYNC_FIELD_NUMBER: _ClassVar[int]
    NCOSYNCLENGTH_FIELD_NUMBER: _ClassVar[int]
    commands: _containers.RepeatedCompositeFieldContainer[_commands_pb2.Command]
    cells: _containers.RepeatedCompositeFieldContainer[_cell_pb2.Cell]
    couplers: _containers.RepeatedCompositeFieldContainer[_cell_pb2.Coupler]
    skipNcoSync: bool
    ncoSyncLength: int
    def __init__(
        self,
        commands: _Iterable[_commands_pb2.Command | _Mapping] | None = ...,
        cells: _Iterable[_cell_pb2.Cell | _Mapping] | None = ...,
        couplers: _Iterable[_cell_pb2.Coupler | _Mapping] | None = ...,
        skipNcoSync: bool = ...,
        ncoSyncLength: int | None = ...,
    ) -> None: ...
