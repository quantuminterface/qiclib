from collections.abc import Iterable as _Iterable
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper

from qicode.proto import cell_pb2 as _cell_pb2
from qicode.proto import expression_pb2 as _expression_pb2
from qicode.proto import pulse_pb2 as _pulse_pb2
from qicode.proto import types_pb2 as _types_pb2
from qicode.proto import variables_pb2 as _variables_pb2

DESCRIPTOR: _descriptor.FileDescriptor

class DigitalTriggerCommand(_message.Message):
    __slots__ = ("cell", "length", "outputs")
    CELL_FIELD_NUMBER: _ClassVar[int]
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    OUTPUTS_FIELD_NUMBER: _ClassVar[int]
    cell: _cell_pb2.Cell
    length: _expression_pb2.Expression
    outputs: _containers.RepeatedScalarFieldContainer[int]
    def __init__(
        self,
        cell: _cell_pb2.Cell | _Mapping | None = ...,
        length: _expression_pb2.Expression | _Mapping | None = ...,
        outputs: _Iterable[int] | None = ...,
    ) -> None: ...

class WaitCommand(_message.Message):
    __slots__ = ("cell", "length")
    CELL_FIELD_NUMBER: _ClassVar[int]
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    cell: _cell_pb2.Cell
    length: _expression_pb2.Expression
    def __init__(
        self,
        cell: _cell_pb2.Cell | _Mapping | None = ...,
        length: _expression_pb2.Expression | _Mapping | None = ...,
    ) -> None: ...

class RecordingCommand(_message.Message):
    __slots__ = ("cell", "duration", "mode", "offset", "save_to", "state_to")
    class Mode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        Normal: _ClassVar[RecordingCommand.Mode]
        ContinuousOn: _ClassVar[RecordingCommand.Mode]
        ContinuousOff: _ClassVar[RecordingCommand.Mode]

    Normal: RecordingCommand.Mode
    ContinuousOn: RecordingCommand.Mode
    ContinuousOff: RecordingCommand.Mode
    CELL_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    SAVE_TO_FIELD_NUMBER: _ClassVar[int]
    STATE_TO_FIELD_NUMBER: _ClassVar[int]
    DURATION_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    cell: _cell_pb2.Cell
    offset: _expression_pb2.Expression
    save_to: str
    state_to: _variables_pb2.Variable
    duration: _expression_pb2.Expression
    mode: RecordingCommand.Mode
    def __init__(
        self,
        cell: _cell_pb2.Cell | _Mapping | None = ...,
        offset: _expression_pb2.Expression | _Mapping | None = ...,
        save_to: str | None = ...,
        state_to: _variables_pb2.Variable | _Mapping | None = ...,
        duration: _expression_pb2.Expression | _Mapping | None = ...,
        mode: RecordingCommand.Mode | str | None = ...,
    ) -> None: ...

class PlayCommand(_message.Message):
    __slots__ = ("cell", "pulse")
    CELL_FIELD_NUMBER: _ClassVar[int]
    PULSE_FIELD_NUMBER: _ClassVar[int]
    cell: _cell_pb2.Cell
    pulse: _pulse_pb2.Pulse
    def __init__(
        self,
        cell: _cell_pb2.Cell | _Mapping | None = ...,
        pulse: _pulse_pb2.Pulse | _Mapping | None = ...,
    ) -> None: ...

class PlayFluxCommand(_message.Message):
    __slots__ = ("coupler", "pulse")
    COUPLER_FIELD_NUMBER: _ClassVar[int]
    PULSE_FIELD_NUMBER: _ClassVar[int]
    coupler: _cell_pb2.Coupler
    pulse: _pulse_pb2.Pulse
    def __init__(
        self,
        coupler: _cell_pb2.Coupler | _Mapping | None = ...,
        pulse: _pulse_pb2.Pulse | _Mapping | None = ...,
    ) -> None: ...

class PlayReadoutCommand(_message.Message):
    __slots__ = ("cell", "pulse")
    CELL_FIELD_NUMBER: _ClassVar[int]
    PULSE_FIELD_NUMBER: _ClassVar[int]
    cell: _cell_pb2.Cell
    pulse: _pulse_pb2.Pulse
    def __init__(
        self,
        cell: _cell_pb2.Cell | _Mapping | None = ...,
        pulse: _pulse_pb2.Pulse | _Mapping | None = ...,
    ) -> None: ...

class RotateFrameCommand(_message.Message):
    __slots__ = ("angle", "cell")
    CELL_FIELD_NUMBER: _ClassVar[int]
    ANGLE_FIELD_NUMBER: _ClassVar[int]
    cell: _cell_pb2.Cell
    angle: _expression_pb2.Expression
    def __init__(
        self,
        cell: _cell_pb2.Cell | _Mapping | None = ...,
        angle: _expression_pb2.Expression | _Mapping | None = ...,
    ) -> None: ...

class SyncCommand(_message.Message):
    __slots__ = ("cells",)
    CELLS_FIELD_NUMBER: _ClassVar[int]
    cells: _containers.RepeatedCompositeFieldContainer[_cell_pb2.Cell]
    def __init__(
        self, cells: _Iterable[_cell_pb2.Cell | _Mapping] | None = ...
    ) -> None: ...

class StoreCommand(_message.Message):
    __slots__ = ("cell", "saveTo", "var")
    CELL_FIELD_NUMBER: _ClassVar[int]
    VAR_FIELD_NUMBER: _ClassVar[int]
    SAVETO_FIELD_NUMBER: _ClassVar[int]
    cell: _cell_pb2.Cell
    var: _variables_pb2.Variable
    saveTo: str
    def __init__(
        self,
        cell: _cell_pb2.Cell | _Mapping | None = ...,
        var: _variables_pb2.Variable | _Mapping | None = ...,
        saveTo: str | None = ...,
    ) -> None: ...

class AssignCommand(_message.Message):
    __slots__ = ("destination", "value")
    DESTINATION_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    destination: _variables_pb2.Variable
    value: _expression_pb2.Expression
    def __init__(
        self,
        destination: _variables_pb2.Variable | _Mapping | None = ...,
        value: _expression_pb2.Expression | _Mapping | None = ...,
    ) -> None: ...

class DeclareCommand(_message.Message):
    __slots__ = ("initialValue", "name", "static", "type", "var")
    VAR_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    STATIC_FIELD_NUMBER: _ClassVar[int]
    INITIALVALUE_FIELD_NUMBER: _ClassVar[int]
    var: _variables_pb2.Variable
    name: str
    type: _types_pb2.Type
    static: bool
    initialValue: _expression_pb2.Expression
    def __init__(
        self,
        var: _variables_pb2.Variable | _Mapping | None = ...,
        name: str | None = ...,
        type: _types_pb2.Type | _Mapping | None = ...,
        static: bool = ...,
        initialValue: _expression_pb2.Expression | _Mapping | None = ...,
    ) -> None: ...

class AsmCommand(_message.Message):
    __slots__ = ("cell", "instruction")
    CELL_FIELD_NUMBER: _ClassVar[int]
    INSTRUCTION_FIELD_NUMBER: _ClassVar[int]
    cell: _cell_pb2.Cell
    instruction: str
    def __init__(
        self,
        cell: _cell_pb2.Cell | _Mapping | None = ...,
        instruction: str | None = ...,
    ) -> None: ...

class IfCommand(_message.Message):
    __slots__ = ("body", "condition")
    CONDITION_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    condition: _expression_pb2.Expression
    body: _containers.RepeatedCompositeFieldContainer[Command]
    def __init__(
        self,
        condition: _expression_pb2.Expression | _Mapping | None = ...,
        body: _Iterable[Command | _Mapping] | None = ...,
    ) -> None: ...

class ElseCommand(_message.Message):
    __slots__ = ("body",)
    BODY_FIELD_NUMBER: _ClassVar[int]
    body: _containers.RepeatedCompositeFieldContainer[Command]
    def __init__(self, body: _Iterable[Command | _Mapping] | None = ...) -> None: ...

class ForRangeCommand(_message.Message):
    __slots__ = ("body", "end", "start", "step", "var")
    VAR_FIELD_NUMBER: _ClassVar[int]
    START_FIELD_NUMBER: _ClassVar[int]
    END_FIELD_NUMBER: _ClassVar[int]
    STEP_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    var: _variables_pb2.Variable
    start: _expression_pb2.Expression
    end: _expression_pb2.Expression
    step: _expression_pb2.Expression
    body: _containers.RepeatedCompositeFieldContainer[Command]
    def __init__(
        self,
        var: _variables_pb2.Variable | _Mapping | None = ...,
        start: _expression_pb2.Expression | _Mapping | None = ...,
        end: _expression_pb2.Expression | _Mapping | None = ...,
        step: _expression_pb2.Expression | _Mapping | None = ...,
        body: _Iterable[Command | _Mapping] | None = ...,
    ) -> None: ...

class WhileCommand(_message.Message):
    __slots__ = ("body", "condition")
    CONDITION_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    condition: _expression_pb2.Expression
    body: _containers.RepeatedCompositeFieldContainer[Command]
    def __init__(
        self,
        condition: _expression_pb2.Expression | _Mapping | None = ...,
        body: _Iterable[Command | _Mapping] | None = ...,
    ) -> None: ...

class ParallelCommand(_message.Message):
    __slots__ = ("body",)
    BODY_FIELD_NUMBER: _ClassVar[int]
    body: _containers.RepeatedCompositeFieldContainer[Command]
    def __init__(self, body: _Iterable[Command | _Mapping] | None = ...) -> None: ...

class CallSite(_message.Message):
    __slots__ = ("code", "file", "line")
    FILE_FIELD_NUMBER: _ClassVar[int]
    LINE_FIELD_NUMBER: _ClassVar[int]
    CODE_FIELD_NUMBER: _ClassVar[int]
    file: str
    line: int
    code: str
    def __init__(
        self, file: str | None = ..., line: int | None = ..., code: str | None = ...
    ) -> None: ...

class GateCommand(_message.Message):
    __slots__ = ("body",)
    BODY_FIELD_NUMBER: _ClassVar[int]
    body: _containers.RepeatedCompositeFieldContainer[Command]
    def __init__(self, body: _Iterable[Command | _Mapping] | None = ...) -> None: ...

class Command(_message.Message):
    __slots__ = (
        "asmCommand",
        "assignCommand",
        "declareCommand",
        "digitalTriggerCommand",
        "elseCommand",
        "forRangeCommand",
        "gateCommand",
        "ifCommand",
        "parallelCommand",
        "playCommand",
        "playFluxCommand",
        "playReadoutCommand",
        "recordingCommand",
        "rotateFrameCommand",
        "sourceInfo",
        "storeCommand",
        "syncCommand",
        "waitCommand",
        "whileCommand",
    )
    SOURCEINFO_FIELD_NUMBER: _ClassVar[int]
    DIGITALTRIGGERCOMMAND_FIELD_NUMBER: _ClassVar[int]
    WAITCOMMAND_FIELD_NUMBER: _ClassVar[int]
    RECORDINGCOMMAND_FIELD_NUMBER: _ClassVar[int]
    PLAYCOMMAND_FIELD_NUMBER: _ClassVar[int]
    PLAYFLUXCOMMAND_FIELD_NUMBER: _ClassVar[int]
    PLAYREADOUTCOMMAND_FIELD_NUMBER: _ClassVar[int]
    ROTATEFRAMECOMMAND_FIELD_NUMBER: _ClassVar[int]
    SYNCCOMMAND_FIELD_NUMBER: _ClassVar[int]
    STORECOMMAND_FIELD_NUMBER: _ClassVar[int]
    ASSIGNCOMMAND_FIELD_NUMBER: _ClassVar[int]
    DECLARECOMMAND_FIELD_NUMBER: _ClassVar[int]
    ASMCOMMAND_FIELD_NUMBER: _ClassVar[int]
    IFCOMMAND_FIELD_NUMBER: _ClassVar[int]
    ELSECOMMAND_FIELD_NUMBER: _ClassVar[int]
    FORRANGECOMMAND_FIELD_NUMBER: _ClassVar[int]
    WHILECOMMAND_FIELD_NUMBER: _ClassVar[int]
    PARALLELCOMMAND_FIELD_NUMBER: _ClassVar[int]
    GATECOMMAND_FIELD_NUMBER: _ClassVar[int]
    sourceInfo: CallSite
    digitalTriggerCommand: DigitalTriggerCommand
    waitCommand: WaitCommand
    recordingCommand: RecordingCommand
    playCommand: PlayCommand
    playFluxCommand: PlayFluxCommand
    playReadoutCommand: PlayReadoutCommand
    rotateFrameCommand: RotateFrameCommand
    syncCommand: SyncCommand
    storeCommand: StoreCommand
    assignCommand: AssignCommand
    declareCommand: DeclareCommand
    asmCommand: AsmCommand
    ifCommand: IfCommand
    elseCommand: ElseCommand
    forRangeCommand: ForRangeCommand
    whileCommand: WhileCommand
    parallelCommand: ParallelCommand
    gateCommand: GateCommand
    def __init__(
        self,
        sourceInfo: CallSite | _Mapping | None = ...,
        digitalTriggerCommand: DigitalTriggerCommand | _Mapping | None = ...,
        waitCommand: WaitCommand | _Mapping | None = ...,
        recordingCommand: RecordingCommand | _Mapping | None = ...,
        playCommand: PlayCommand | _Mapping | None = ...,
        playFluxCommand: PlayFluxCommand | _Mapping | None = ...,
        playReadoutCommand: PlayReadoutCommand | _Mapping | None = ...,
        rotateFrameCommand: RotateFrameCommand | _Mapping | None = ...,
        syncCommand: SyncCommand | _Mapping | None = ...,
        storeCommand: StoreCommand | _Mapping | None = ...,
        assignCommand: AssignCommand | _Mapping | None = ...,
        declareCommand: DeclareCommand | _Mapping | None = ...,
        asmCommand: AsmCommand | _Mapping | None = ...,
        ifCommand: IfCommand | _Mapping | None = ...,
        elseCommand: ElseCommand | _Mapping | None = ...,
        forRangeCommand: ForRangeCommand | _Mapping | None = ...,
        whileCommand: WhileCommand | _Mapping | None = ...,
        parallelCommand: ParallelCommand | _Mapping | None = ...,
        gateCommand: GateCommand | _Mapping | None = ...,
    ) -> None: ...
