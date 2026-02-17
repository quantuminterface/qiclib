from __future__ import annotations

from abc import ABC, abstractmethod
from functools import wraps

from google.protobuf.internal.containers import RepeatedCompositeFieldContainer

from qicode._callsite import capture_callsite
from qicode.proto.commands_pb2 import (
    AsmCommand,
    AssignCommand,
    CallSite,
    Command,
    DigitalTriggerCommand,
    ElseCommand,
    ForRangeCommand,
    GateCommand,
    IfCommand,
    ParallelCommand,
    PlayCommand,
    PlayFluxCommand,
    PlayReadoutCommand,
    RecordingCommand,
    RotateFrameCommand,
    StoreCommand,
    SyncCommand,
    WaitCommand,
    WhileCommand,
)
from qicode.qi_cell import QiCell, QiCoupler
from qicode.qi_expression import ExpressionLike, QiExpression, VariableRef
from qicode.qi_job import QiJob
from qicode.qi_pulse import QiPulse


def Sync(*cells: QiCell):
    """
    Synchronize cells.
    """
    QiJob._current()._add_command(
        syncCommand=SyncCommand(cells=(cell._proto() for cell in cells)),
        sourceInfo=capture_callsite(),
    )


def Play(cell: QiCell, pulse: QiPulse):
    """Add Manipulation command and pulse to cell

    :param cell:
        The cell that plays the pulse
    :param pulse:
        The pulse to play
    """
    QiJob._current()._add_command(
        playCommand=PlayCommand(cell=cell._proto(), pulse=pulse._proto()),
        sourceInfo=capture_callsite(),
    )


def PlayReadout(cell: QiCell, pulse: QiPulse):
    """Add Readout command and pulse to cell

    :param cell:
        The cell that plays the readout
    :param pulse:
        The readout pulse to play
    """
    QiJob._current()._add_command(
        playReadoutCommand=PlayReadoutCommand(cell=cell._proto(), pulse=pulse._proto()),
        sourceInfo=capture_callsite(),
    )


def PlayFlux(coupler: QiCoupler, pulse: QiPulse):
    """
    Add Flux Pulse command to cell

    :param coupler:
        The coupler that plays the pulse
    :param pulse:
        The pulse to play
    """
    QiJob._current()._add_command(
        playFluxCommand=PlayFluxCommand(coupler=coupler._proto(), pulse=pulse._proto()),
        sourceInfo=capture_callsite(),
    )


def RotateFrame(cell: QiCell, angle: ExpressionLike):
    """
    Rotates the reference frame of the manipulation pulses played with :ref:`Play()`.
    This corresponds to an instantaneous, virtual Z rotation on the Bloch sphere.

    :param cell:
        The cell for the rotation
    :param angle:
        The angle of the rotation
    """
    QiJob._current()._add_command(
        rotateFrameCommand=RotateFrameCommand(
            cell=cell._proto(), angle=QiExpression.from_any(angle)._proto()
        ),
        sourceInfo=capture_callsite(),
    )


def Recording(
    cell: QiCell,
    duration: ExpressionLike = 0,
    offset: ExpressionLike = 0,
    save_to: str | None = None,
    state_to: VariableRef | None = None,
    toggle_continuous: bool | None = None,
):
    """Add Recording command to cell

    :param cell:
        The QiCell for the recording
    :param duration:
        The duration of the recording window in seconds
    :param offset:
        The offset of the recording window in seconds
    :param save_to:
        The name of the QiResult where to save the result data
    :param state_to:
        The variable in which the obtained qubit state should be stored
    :param toggleContinuous:
        Whether the recording should be repeated continously and seemlessly.
        Value True will start the recording, False will stop it (None is for normal mode)
    """
    if toggle_continuous is None:
        mode = RecordingCommand.Mode.Normal
    elif toggle_continuous is True:
        mode = RecordingCommand.Mode.ContinuousOn
    elif toggle_continuous is False:
        mode = RecordingCommand.Mode.ContinuousOff
    QiJob._current()._add_command(
        recordingCommand=RecordingCommand(
            cell=cell._proto(),
            duration=QiExpression.from_any(duration)._proto(),
            offset=QiExpression.from_any(offset)._proto(),
            save_to=save_to,
            state_to=state_to._proto() if state_to is not None else None,
            mode=mode,
        ),
        sourceInfo=capture_callsite(),
    )


def DigitalTrigger(cell: QiCell, length: ExpressionLike, outputs: list[int]):
    """
    Adds a digital trigger command to the cell.

    Digital triggers are visible at auxiliary outputs and can be used, for example, to trigger external electronics
    simultaneously to outputting a pulse.
    The time resolution of digital triggers is 4 ns.

    =======
    Example
    =======

    The following QiJob Generates a 12 ns long pulse at digital outputs 3 and 6:

    .. code-block:: python

        with QiJob() as job:
            q = QiCells(1)
            DigitalTrigger(q[0], length=12e-9, outputs=(3, 6))

    ===================================================
    Combining the output of multiple Digital Unit Cells
    ===================================================

    Each Digital Unit Cell can trigger each output.
    To combine multiple outputs to multiple inputs, all digital outputs are combined using a logical OR operation.

    ================
    Delaying outputs
    ================

    A static delay can be added to each output using
    :python:`QiController.digital_trigger.set_delay(output_number, delay_in_seconds)`.
    To add a variable amount of time, use :python:`Wait(cell, duration)` before calling :python:`DigitalTrigger`

    :param cell: The cell that is responsible for the outputting the digital trigger
    :param length: The duration of the pulse in seconds. Should be a multiple of four ns
    :param outputs: The outputs to trigger. This can also be an expression like :python:`range(0, 8)`
        to trigger all outputs.
    """
    QiJob._current()._add_command(
        digitalTriggerCommand=DigitalTriggerCommand(
            cell=cell._proto(),
            length=QiExpression.from_any(length)._proto(),
            outputs=outputs,
        ),
        sourceInfo=capture_callsite(),
    )


def Wait(cell: QiCell, delay: ExpressionLike):
    """Add Wait command to cell. delay can be int or QiVariable

    :param cell: the QiCell that should wait
    :param delay: the time to wait in seconds
    """
    QiJob._current()._add_command(
        waitCommand=WaitCommand(
            cell=cell._proto(), length=QiExpression.from_any(delay)._proto()
        ),
        sourceInfo=capture_callsite(),
    )


def Store(cell: QiCell, variable: VariableRef, save_to: str):
    """Not implemented yet. Add Store command to cell."""
    QiJob._current()._add_command(
        storeCommand=StoreCommand(
            cell=cell._proto(), var=variable._proto(), saveTo=save_to
        )
    )


def Assign(dst: VariableRef, value: ExpressionLike):
    """
    Assigns a calculated value to a destination

    :param dst:
        The destination
    :param calc:
        The calculation to perform
    """
    QiJob._current()._add_command(
        assignCommand=AssignCommand(
            destination=dst._proto(), value=QiExpression.from_any(value)._proto()
        ),
        sourceInfo=capture_callsite(),
    )


def ASM(cell: QiCell, instruction: str):
    """Insert assembly instruction"""
    QiJob._current()._add_command(
        asmCommand=AsmCommand(cell=cell._proto(), instruction=instruction),
        sourceInfo=capture_callsite(),
    )


class _Block(ABC):
    def __init__(self) -> None:
        self._callsite: CallSite | None = None

    def __enter__(self):
        container = self._add_command(
            QiJob._current()._insertion_block(), capture_callsite()
        )
        QiJob._current()._add_new_context(container)
        return self

    def __exit__(self, exc_type, exc, tb):
        QiJob._current()._close_context()
        # Propagate exceptions (dont suppress)
        return False

    @abstractmethod
    def _add_command(
        self,
        container: RepeatedCompositeFieldContainer[Command],
        callsite: CallSite | None,
    ) -> RepeatedCompositeFieldContainer[Command]:
        pass


class While(_Block):
    """
    Adds While loop to program.
    If multiple cells are used inside body, a synchronisation between the cells is done before the While as well as after the end of the body.
    The condition is evaluated before each iteration of the loop.

    :param condition: The boolean condition to evaluate for continuing the loop

    Example
    -------

    .. code-block:: python

        with QiJob() as job:
            q = QiCells(1)
            state = QiVariable()

            # Read out initial state
            ql.jobs.Readout(q[0], state_to=state)
            with While(state != 1):
                ql.jobs.Readout(q[0], state_to=state)
    """

    def __init__(self, condition: ExpressionLike) -> None:
        self._condition = QiExpression.from_any(condition)

    def _add_command(
        self,
        container: RepeatedCompositeFieldContainer[Command],
        callsite: CallSite | None,
    ) -> RepeatedCompositeFieldContainer[Command]:
        return container.add(
            whileCommand=WhileCommand(condition=self._condition._proto()),
            sourceInfo=callsite,
        ).whileCommand.body


class If(_Block):
    """
    Add conditional logic to the program.
    If multiple cells are used inside the body, a synchronization between the cells takes place before the If.

    :param condition: The condition to check

    Example
    -------

    .. code-block:: python

        with QiJob() as job:
            q = QiCells(1)
            x = QiIntVariable(1)
            with If(x > 1):
                ...  # won't be executed

    The If statement is most commonly used to react to qubit states in real-time:

    .. code-block:: python

        from qiclib import jobs

        with QiJob() as job:
            q = QiCells(1)
            state = QiStateVariable()
            jobs.Readout(q[0], state_to=state)
            with If(state=0):
                ...  # Apply some conditional logic based on the qubit state
    """

    def __init__(self, condition: QiExpression) -> None:
        self._condition = condition

    def _add_command(
        self,
        container: RepeatedCompositeFieldContainer[Command],
        callsite: CallSite | None,
    ) -> RepeatedCompositeFieldContainer[Command]:
        return container.add(
            ifCommand=IfCommand(condition=self._condition._proto()),
            sourceInfo=callsite,
        ).ifCommand.body


class Else(_Block):
    """
    Adds Conditional logic if the preceding :class:`If` command evaluates to false.

    :raises RuntimeError: When the preceeding command is not an :python:`If` command

    Example
    -------
    .. code-block:: python

        from qiclib import jobs

        with QiJob() as job:
            q = QiCells(1)
            state = QiStateVariable()
            jobs.Readout(q[0], state_to=state)
            with If(state=0):
                ...  # Apply some conditional logic based on the qubit state
            with Else():
                ...  # State is 1

    """

    def _add_command(
        self,
        container: RepeatedCompositeFieldContainer[Command],
        callsite: CallSite | None,
    ) -> RepeatedCompositeFieldContainer[Command]:
        return container.add(
            elseCommand=ElseCommand(),
            sourceInfo=callsite,
        ).elseCommand.body


class Parallel(_Block):
    """Pulses defined in body are united in one trigger command."""

    def _add_command(
        self,
        container: RepeatedCompositeFieldContainer[Command],
        callsite: CallSite | None,
    ) -> RepeatedCompositeFieldContainer[Command]:
        return container.add(
            parallelCommand=ParallelCommand(),
            sourceInfo=callsite,
        ).parallelCommand.body


class ForRange(_Block):
    """
    Adds ForRange to program.
    If multiple cells are used inside body, a synchronisation between the cells is done before the ForRange as well as after the end of the body.
    If QiTimeVariable is used as var, loops starting at 0 are unrolled, to skip pulses/waits inside body using var as length.
    Raises exception if start, end and step are not set up properly.
    """

    def __init__(
        self,
        var: VariableRef,
        start: ExpressionLike,
        end: ExpressionLike,
        step: ExpressionLike = 1,
    ) -> None:
        self._var = var
        self._start = start
        self._end = end
        self._step = step

    def _add_command(
        self,
        container: RepeatedCompositeFieldContainer[Command],
        callsite: CallSite | None,
    ) -> RepeatedCompositeFieldContainer[Command]:
        return container.add(
            forRangeCommand=ForRangeCommand(
                var=self._var._proto(),
                start=QiExpression.from_any(self._start)._proto(),
                end=QiExpression.from_any(self._end)._proto(),
                step=QiExpression.from_any(self._step)._proto(),
            ),
            sourceInfo=callsite,
        ).forRangeCommand.body


def QiGate(func):
    """
    decorator for using a function in a QiJob
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        job = QiJob._current()
        container = job._add_command(
            gateCommand=GateCommand(),
            sourceInfo=capture_callsite(),
        ).gateCommand.body
        job._add_new_context(container)

        func(*args, **kwargs)

        job._close_context()

    return wrapper
