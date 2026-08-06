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
This is the main module of QiCode.
Here, all important commands write QiPrograms are defined.
"""

from __future__ import annotations

import dataclasses
import warnings
from collections.abc import Callable, Iterable
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal

import numpy as np
import numpy.typing as npt

import qiclib
import qicode
import qicode.proto
from qiclib.code.compiler.qicode_compiler import (
    Compilation,
    QiCodeCompiler,
)
from qiclib.code.qi_command import (
    AsmCommand,
    AssignCommand,
    DeclareCommand,
    DigitalTriggerCommand,
    ForRangeCommand,
    IfCommand,
    ParallelCommand,
    PlayCommand,
    PlayReadoutCommand,
    QiCommand,
    RecordingCommand,
    RotateFrameCommand,
    StoreCommand,
    SyncCommand,
    WaitCommand,
    WhileCommand,
)
from qiclib.code.qi_prog_builder import build_program, get_all_variables
from qiclib.code.qi_pulse import Shape, ShapeLib, _QiPulse
from qiclib.code.qi_result import QiResult
from qiclib.code.qi_sample import QiSample
from qiclib.code.qi_seq_instructions import SequencerInstruction
from qiclib.code.qi_types import (
    QiPostTypecheckVisitor,
    QiType,
    QiTypeFallbackVisitor,
    _TypeDefiningUse,
)
from qiclib.code.qi_var_definitions import (
    QiCellProperty,
    QiCondition,
    QiExpression,
    QiIndexed,
    QiOpCond,
    _QiConstValue,
    _QiStaticVariable,
    _QiVariableBase,
)
from qiclib.code.qi_visitor import (
    QiCMContainedCellVisitor,
    QiResultCollector,
)
from qiclib.experiment.qicode.data_handler import DataHandler
from qiclib.experiment.qicode.data_provider import DataProvider
from qiclib.hardware import digital_trigger
from qiclib.hardware.taskrunner import TaskRunner
from qiclib.hardware.unitcell import DataCollection
from qiclib.packages.grpc.qic_unitcell_pb2 import JobStatus

if TYPE_CHECKING:
    from qiclib.experiment.qicode.base import QiCodeExperiment


def _resolve_property(value: QiCellProperty | Any):
    """Helper to resolve QiCellProperty values to their actual values."""
    return value() if isinstance(value, QiCellProperty) else value


class QiCell(qicode.QiCell):
    """A QiCell is an abstract representation of the qubit/cell the program is run on.
    Usually, a single :python:`QiCell` is not instantiated, but instead a :class:`QiCells` object.
    For a single :python:`QiCell`, use instead :python:`QiCells(1)`

    A :python:`QiCell` must be instantiated inside within a :class:`QiJob` context.

    The :python:`QiCell` object can be used to get properties that are defined on :class:`QiSamples <QiSample>`.
    For this, index the :python:`QiCell` object using the name of the property:

    .. code-block:: python

        q: QiCell = ...
        t1_time = q["t1"]

    The actual value for the accessed property (in the example above, the T1 time) is filled in when executing a
    :class:`QiJob` and providing the actual sample.

    **Tasks of the QiCell**:

    - Saves the pulses needed for program execution.
    - Provides a dictionary functionality to define commonly used durations/properties.
    - Implements a Sequencer object, which contains the assembler program after compilation.

    :param cell_id: A unique ID
    :raises RuntimeError: When the :python:`QiCell` is instantiated outside a `QiJob`
    """

    def __init__(self, cell_id: int, job: QiJob | None = None):
        super().__init__(cell_id)
        self.manipulation_pulses: list[_QiPulse] = []
        self.digital_trigger_sets: list[digital_trigger.TriggerSet] = []
        self.flux_pulses: list[_QiPulse] = []
        self.readout_pulses: list[_QiPulse] = []
        self._result_container: dict[str, QiResult] = {}
        # The order in which recorded values are assigned to which result container
        self._result_recording_order: list[QiResult] = []
        self._unresolved_property: set[str] = set()
        if job is None:
            self._job_ref = QiJob._current()
        else:
            self._job_ref = job
        self._relevant_vars: set[_QiVariableBase] = set()

        # These attributes are determined by dataflow analyses
        self._initial_manip_freq: float | None = None
        self._initial_readout_freq: float | None = None
        self._initial_rec_offset: float | None = None
        self._initial_phase: float | None = None
        self._initial_amplitude: float | None = None

        self._rec_length: int | float | QiCellProperty | None = None

        self._properties: dict[str | QiCellProperty, Any] = {}

    @property
    def cell_id(self) -> int:
        return self._proto().index

    def add_pulse(self, pulse: _QiPulse):
        if pulse not in self.manipulation_pulses:
            self.manipulation_pulses.append(pulse)

        if len(self.manipulation_pulses) > 13:
            raise RuntimeError("Too many pulses in use")

        return self.manipulation_pulses.index(pulse) + 1  # index 0 and 15 are reserved

    def add_digital_trigger(self, trig_set: digital_trigger.TriggerSet):
        if trig_set not in self.digital_trigger_sets:
            self.digital_trigger_sets.append(trig_set)

        if len(self.digital_trigger_sets) > 3:
            raise RuntimeError(
                "Too many digital trigger sets in use (Only three sets are available)"
            )

        return self.digital_trigger_sets.index(trig_set) + 1  # index 0 is reserved

    @property
    def initial_manipulation_frequency(self):
        if self._initial_manip_freq is None:
            if len(self.manipulation_pulses) > 0:
                warnings.warn(
                    "Manipulation pulses without frequency given, using 90 MHz."
                )
            return 90e6  # Default frequency
        return _resolve_property(self._initial_manip_freq)

    @property
    def initial_phase(self):
        if self._initial_phase is None:
            if len(self.manipulation_pulses) > 0:
                warnings.warn("Manipulation pulses without phase given, using 0.")
            return 0  # Default phase
        return _resolve_property(self._initial_phase)

    @property
    def initial_amplitude(self):
        if self._initial_amplitude is None:
            if len(self.manipulation_pulses) > 0:
                warnings.warn("Manipulation pulses without amplitude given, using 1.")
            return 1  # Default amplitude
        return _resolve_property(self._initial_amplitude)

    def add_recording_length(self, length):
        if self._rec_length is None:
            self._rec_length = length
        elif (
            not self._rec_length._equal_syntax(length)
            if isinstance(self._rec_length, QiExpression)
            else self._rec_length != length
        ):
            raise RuntimeError(
                f"Cell {self.cell_id}: Multiple definitions of recording length used."
            )

    def add_readout_pulse(self, pulse: _QiPulse):
        if pulse not in self.readout_pulses:
            self.readout_pulses.append(pulse)

        if len(self.readout_pulses) > 13:
            raise RuntimeError("Too many pulses in use")

        return self.readout_pulses.index(pulse) + 1  # index 0 and 15 are reserved

    @property
    def initial_readout_frequency(self):
        if self._initial_readout_freq is None:
            if len(self.readout_pulses) > 0 and not self._has_variable_frequency():
                warnings.warn("Readout pulses without frequency given, using 30 MHz.")
            return 30e6  # Default frequency
        return _resolve_property(self._initial_readout_freq)

    def _has_variable_frequency(self) -> bool:
        """Check if any readout pulse has a variable frequency."""
        return any(
            pulse.frequency is not None
            and isinstance(pulse.frequency, QiExpression)
            and pulse.frequency.contains_variables()
            for pulse in self.readout_pulses
        )

    @property
    def recording_length(self):
        """the length of the recording pulse"""
        if self._rec_length is None:
            return 0
        return _resolve_property(self._rec_length)

    @property
    def initial_recording_offset(self):
        """the recording offset in seconds"""
        if self._initial_rec_offset is None:
            return 0
        return _resolve_property(self._initial_rec_offset)

    def get_result_container(self, result: str) -> QiResult:
        if result not in self._result_container:
            box = QiResult(result)
            box._cell = self
            self._result_container[result] = box
        return self._result_container[result]

    def add_variable(self, var: _QiVariableBase):
        self._relevant_vars.add(var)

    def get_number_of_recordings(self):
        return len(self._result_recording_order)

    def reset(self):
        for container in self._result_container.values():
            container.data = []

    def data(self, name: str | None = None) -> dict[str, np.ndarray] | np.ndarray:
        """
        Returns the data after running an experiment.

        When calling this function without a name, i.e., calling :python:`cell.data()`,
        returns a dictionary containing the results as numpy arrays.

        When calling this function with a name, i.e., calling :python:`cell.data("result_name")`,
        returns the result referenced by :python:`name`

        :param name: The name of the data
        :return: A single result, or a dictionary of result names mapped to results.
        """
        if name is not None:
            return self._result_container[name].get()
        return {
            key: container.get() for key, container in self._result_container.items()
        }

    def _resolve_properties(self, len_dict: dict[str, Any]):
        missing_keys = self._unresolved_property.difference(len_dict.keys())
        if missing_keys:
            raise RuntimeError(
                f"Cell {self.cell_id}: Not all properties for job could be resolved. "
                f"Missing properties: {missing_keys}"
            )

        for key in self._unresolved_property:
            self._properties[key] = len_dict[key]

    @property
    def has_unresolved_properties(self):
        return len(self._unresolved_property) > 0

    def _get_unresolved_properties(self):
        return [key for key in self._unresolved_property if key not in self._properties]

    def __str__(self) -> str:
        return f"QiCell({self.cell_id})"


class QiCells(qicode.QiCells):
    """
    QiCells encapsulates multiple :class`QiCell` objects.
    It is a list-like object where the individual cells can be accessed using the
    index operator, i.e.

    .. code-block:: python

        cells = QiCells(5)
        cell0: QiCell = cells[0]
        cell3: QiCell = cells[3]


    :param num: The number of cells to create
    :param job: The QiJob to use when not inside a QiJob context
    :raises RuntimeError: When the :python:`QiCells` object is instantiated outside a :python:`QiJob`
    """

    def __init__(self, num: int, job: QiJob | None = None) -> None:
        super().__init__(num)
        self.cells = [QiCell(x) for x in range(num)]
        job_ref = job if job is not None else QiJob._current()
        job_ref._register_cells(self.cells)


class QiCoupler(qicode.QiCoupler):
    def __init__(self, associated_unit_cell: QiCell, coupling_index: int):
        self.associated_unit_cell = associated_unit_cell
        self.coupling_index = coupling_index
        self.coupling_pulses: list[_QiPulse] = []

    def add_pulse(self, pulse: _QiPulse):
        self.coupling_pulses.append(pulse)
        return len(self.coupling_pulses)


class QiCouplers(qicode.QiCouplers):
    """
    Declares :py:`count` couplers.

    Couplers are capable of playing flux pulses.
    In the context of QiCode, flux Pulses are longer but do not have Digital Up-Conversion.

    You can instantiate up to twice the amount of digital Unit Cells.

    .. warning::
        You must first instantiate Digital Unit Cells before you can instantiate Couplers.

    .. code-block:: python

        with QiJob() as job:
            q = QiCells(6)
            c = QiCouplers(12)
    """

    def __init__(self, count: int):
        super().__init__(count)
        if len(QiJob._current().cells) == 0:
            raise RuntimeError(
                "No cells in the QiJob found."
                "Note that couplers must be instantiated after cells."
            )

        self._couplers = [
            QiCoupler(QiJob._current().cells[i // 2], i % 2) for i in range(count)
        ]
        QiJob._current()._register_couplers(self._couplers)


If = qicode.If
Else = qicode.Else
Parallel = qicode.Parallel
ForRange = qicode.ForRange
While = qicode.While
QiVariable = qicode.QiVariable
Recording = qicode.Recording
RotateFrame = qicode.RotateFrame
DigitalTrigger = qicode.DigitalTrigger
Wait = qicode.Wait
Store = qicode.Store
Assign = qicode.Assign
ASM = qicode.ASM
QiTimeVariable = qicode.QiTimeVariable
QiFrequencyVariable = qicode.QiFrequencyVariable
QiStateVariable = qicode.QiStateVariable
QiIntVariable = qicode.QiIntVariable
QiPhaseVariable = qicode.QiPhaseVariable
QiAmplitudeVariable = qicode.QiAmplitudeVariable
Sync = qicode.Sync
Play = qicode.Play
PlayReadout = qicode.PlayReadout
PlayFlux = qicode.PlayFlux
QiGate = qicode.QiGate


class SubmittedJobStatus(Enum):
    ENQUEUED = 1
    """
    The job is enqueud and will run when available
    """
    RUNNING = 2
    """
    The job is currently running
    """
    FINISHED = 3
    """
    The job has finished was not fetched
    """
    EXPIRED = 4
    """
    The job has finished but was never fetched and thus expired
    """
    FETCHED = 5
    """
    The job was fetched
    """
    CANCELED = 6
    """
    The job was canceled on the server side.
    """


class SubmittedJob:
    """
    A handle to a job running on the platform.

    This handle can be used to query results using :meth:`results` and
    query the current status using :meth:`status`.
    """

    def __init__(
        self,
        job_id: int,
        qic,
        data_handler_factory: DataHandler.Factory,
        cell_list: list[QiCell],
        averages: int,
        use_taskrunner: bool = False,
    ):
        self._qic = qic
        self.job_id = job_id
        self._data_handler_factory = data_handler_factory
        self._cell_list = cell_list
        self._use_taskrunner = use_taskrunner
        self._averages = averages
        self._results = None

    @classmethod
    def from_experiment(
        cls,
        job_id: int,
        exp: QiCodeExperiment,
    ):
        return SubmittedJob(
            job_id,
            exp.qic,
            data_handler_factory=exp._data_handler_factory,
            cell_list=exp.cell_list,
            averages=exp.averages,
            use_taskrunner=exp.use_taskrunner,
        )

    def status(self) -> SubmittedJobStatus:
        if self._results is None:
            grpc_status = self._qic.cell.cell.status(self.job_id)
            status_map = {
                JobStatus.ENQUEUED: SubmittedJobStatus.ENQUEUED,
                JobStatus.RUNNING: SubmittedJobStatus.RUNNING,
                JobStatus.FINISHED: SubmittedJobStatus.FINISHED,
                JobStatus.NOT_PRESENT: SubmittedJobStatus.EXPIRED,
            }
            if grpc_status not in status_map:
                raise AssertionError(f"Unknown grpc job status {grpc_status}")
            return status_map[grpc_status]
        # we have results -> the job was fetched
        return SubmittedJobStatus.FETCHED

    def _process_results(self, result):
        # Check if some errors have been missed but do not raise an exception
        self._qic.check_errors(raise_exceptions=False)

        data_provider = DataProvider.create(result, self._use_taskrunner)
        data_handler: DataHandler = self._data_handler_factory(
            data_provider, self._cell_list, self._averages
        )
        data_handler.process_results()

    def results(self):
        if self._results is None:
            self._results = self._qic.cell.stream_results(self.job_id)
            self._process_results(self._results)
        return self._results

    def __str__(self):
        return f"SubmittedJob(id={self.job_id})"


_LiteralType = int | float | list["_LiteralType"]


def _generate_proto_from_binary_compilation(
    binary: Compilation,
) -> qiclib.packages.grpc.qic_unitcell_pb2.Job:
    import qiclib.packages.grpc.datatypes_pb2 as dt
    import qiclib.packages.grpc.pulsegen_pb2 as pulsegen_proto
    import qiclib.packages.grpc.qic_unitcell_pb2 as unitcell_proto
    import qiclib.packages.grpc.sequencer_pb2 as sequencer_proto

    def _convert_pulse(pulse: qicode.proto.SampleablePulse):
        assert pulse.shape in {1, 0}, (
            f"Only rectangular pulses or off supported currently, got shape {pulse.shape}"
        )

        envelope_i = pulse.amplitude / (2**15 - 1) * np.ones(pulse.length)
        envelope_q = np.zeros(pulse.length)

        # Zero-pad arrays to align to size of 4
        pad_size = (4 - len(envelope_i) % 4) % 4
        envelope_i = np.pad(envelope_i, (0, pad_size), mode="constant")
        envelope_q = np.pad(envelope_q, (0, pad_size), mode="constant")
        # TODO: This samples, then re-samples the pulse.
        # Use more efficient method in the pulsegen_proto to directly transmit samplabe pulse.
        return pulsegen_proto.Pulse(
            index=pulsegen_proto.IndexSet(
                cindex=dt.EndpointIndex(value=0),
                tindex=pulsegen_proto.TriggerSetIndex(value=pulse.index),
            ),
            i=envelope_i,
            q=envelope_q,
            phase=pulse.phase,
            hold=pulse.hold,
            shift_phase=pulse.shift_phase,
        )

    job = unitcell_proto.Job()
    compilation_proto = binary.proto()
    for cell in compilation_proto.cells:
        if len(cell.readout_pulses) > 13:
            raise RuntimeError(
                "Number of readouts exceeded 13. Your program uses too many different pulses."
            )
        cell_config = unitcell_proto.CellConfig(index=dt.EndpointIndex(value=cell.id))
        readout_config = cell_config.readout_config
        for pulse in cell.readout_pulses:
            readout_config.pulses.append(_convert_pulse(pulse))

        warnings.warn(
            "[Readout] Initial readout frequency, recording frequency, recording duration and recording offset not implemented (using some default)"
        )
        readout_config.readout_frequency = 10e6
        readout_config.recording_frequency = 10e6
        readout_config.recording_duration = 510e-9
        readout_config.recording_offset = 0

        drive_config = cell_config.drive_config
        if len(cell.manipulation_pulses) > 13:
            raise RuntimeError(
                "Number of pulses exceeded 13. Your program uses too many different pulses."
            )
        warnings.warn(
            "[Manipulation] Initial frequency not implemented (using some default)"
        )
        for pulse in cell.manipulation_pulses:
            drive_config.pulses.append(_convert_pulse(pulse))

        # TODO: Digital trigger.
        # No warning because this will already raise in the compiler
        sequencer_config = unitcell_proto.SequencerConfig(
            program=sequencer_proto.Program(
                index=dt.EndpointIndex(value=0),
                description="No Description",
                program_data=cell.code.binary.code,
            )
        )
        cell_config.sequencer_config.CopyFrom(sequencer_config)
        # TODO: couplers
        # Also no warning because this will already raise in the compiler
        job.cell_configs.append(cell_config)
    return job


@dataclasses.dataclass
class ExecutionInfo:
    results: npt.NDArray
    """
    The results obtained from an experiment
    """
    timestamp: int
    """
    Relative timestamp when the experiment started
    """


class QiJob(qicode.QiJob):
    """
    Container holding program, cells and qi_result containers for execution of program.
    Builds the job with its properties

    :param skip_nco_sync: if the NCO synchronization at the beginning should be skipped
    :param nco_sync_length: how long to wait after the nco synchronization
    """

    def __init__(
        self,
        skip_nco_sync: bool = False,
        nco_sync_length: int = 0,
    ) -> None:
        super().__init__(skip_nco_sync, nco_sync_length)
        self.qi_results: list[QiResult] = []
        self.cells: list[QiCell] = []
        self.couplers: list[QiCoupler] = []
        self._variables: dict[int, _QiVariableBase] = {}

        self._commands: list[QiCommand] = []

        # Build
        self._performed_analyses = False
        self._build_done = False
        self._arranged_cells: list[QiCell | None] = []
        self._var_reg_map: dict[_QiVariableBase, dict[QiCell, int]] = {}

        # Run
        self._custom_processing = None
        self._custom_data_handler = None

    def get_var(self, variable: qicode.VariableRef) -> _QiVariableBase:
        return self._variables[variable._proto().id]

    @property
    def skip_nco_sync(self) -> bool:
        return self.proto().skipNcoSync

    @property
    def nco_sync_length(self) -> int:
        return self.proto().ncoSyncLength

    def __exit__(self, exception_type, exception_value, traceback):
        super().__exit__(exception_type, exception_value, traceback)
        self._qi_commands = self._map_commands(self.proto().commands)
        for cmd in self.commands:
            cmd.accept(QiTypeFallbackVisitor())

        for cmd in self.commands:
            cmd.accept(QiPostTypecheckVisitor())

        _QiVariableBase.reset_str_id()

    def _map_cell(self, cell: qicode.proto.Cell) -> QiCell:
        return self.cells[cell.index]

    def _map_literal(self, expr: qicode.proto.Expression.Literal) -> _LiteralType:
        if expr.HasField("intLiteral"):
            return expr.intLiteral
        elif expr.HasField("floatLiteral"):
            return expr.floatLiteral
        else:
            assert expr.HasField("arrayLiteral")
            return list(map(self._map_literal, expr.arrayLiteral.values))

    def _map_expression(
        self, expr: qicode.proto.Expression
    ) -> QiExpression | _LiteralType:
        if expr.HasField("literal"):
            return self._map_literal(expr.literal)
        if expr.HasField("variable"):
            return self._variables[expr.variable.id]
        if expr.HasField("binary"):
            val1 = QiExpression._from(self._map_expression(expr.binary.lhs))
            cls = type(val1)
            op_calc = {
                qicode.proto.Expression.Binary.Operator.Plus: cls.__add__,
                qicode.proto.Expression.Binary.Operator.Minus: cls.__sub__,
                qicode.proto.Expression.Binary.Operator.Mult: cls.__mul__,
                qicode.proto.Expression.Binary.Operator.Lsh: cls.__lshift__,
                qicode.proto.Expression.Binary.Operator.Rsh: cls.__rshift__,
                qicode.proto.Expression.Binary.Operator.And: cls.__and__,
                qicode.proto.Expression.Binary.Operator.Or: cls.__or__,
                qicode.proto.Expression.Binary.Operator.Xor: cls.__xor__,
                qicode.proto.Expression.Binary.Operator.Div: cls.__truediv__,
            }.get(expr.binary.op)
            assert op_calc is not None, (
                f"Cannot form condition with operator {expr.binary.op}"
            )
            return op_calc(
                val1, QiExpression._from(self._map_expression(expr.binary.rhs))
            )
        if expr.HasField("property"):
            cell = self._map_cell(expr.property.cell)
            prop = QiCellProperty(cell, name=expr.property.name)
            cell._unresolved_property.add(expr.property.name)
            return prop
        if expr.HasField("typeCast"):
            value = self._map_expression(expr.typeCast.expr)
            if not isinstance(value, int | float | _QiConstValue):
                raise NotImplementedError(
                    f"Type cast for non-constant value {value.__class__.__name__}"
                )
            const = value if isinstance(value, _QiConstValue) else _QiConstValue(value)
            typ = self._map_type(expr.typeCast.targetType)
            const._type_info.set_type(typ, _TypeDefiningUse.VALUE_DEFINITION)
            return const
        if expr.HasField("indexed"):
            base = self._map_expression(expr.indexed.base)
            assert isinstance(base, _QiVariableBase)
            index = self._map_expression(expr.indexed.value)
            return QiIndexed(base, QiExpression._from(index))
        else:
            assert expr.HasField("unary"), f"Unknown expression {expr}"
            op = {
                qicode.proto.Expression.Unary.Operator.Minus: QiExpression.__invert__,
            }.get(expr.unary.op)
            if op is None:
                raise NotImplementedError(f"Unary operator {expr.unary.op}")
            val1 = self._map_expression(expr.unary.expr)
            return op(QiExpression._from(val1))

    def _map_type(self, typ: qicode.proto.Type) -> QiType:
        return QiType(typ)

    def _map_recording_command(
        self, cmd: qicode.proto.RecordingCommand, commands: list[QiCommand]
    ) -> RecordingCommand:
        def opt_field(field_name, mapper=lambda x: x):
            if cmd.HasField(field_name):
                return mapper(getattr(cmd, field_name))
            else:
                return None

        save_to = opt_field("save_to")
        state_to = opt_field("state_to", lambda state_to: self._variables[state_to.id])
        duration = opt_field("duration", self._map_expression)
        offset = opt_field("offset", self._map_expression)
        if cmd.mode == qicode.proto.RecordingCommand.Mode.ContinuousOn:
            toggle_continuous = True
        elif cmd.mode == qicode.proto.RecordingCommand.Mode.ContinuousOff:
            toggle_continuous = False
        else:
            toggle_continuous = None
        recording_cmd = RecordingCommand(
            self._map_cell(cmd.cell),
            save_to,
            state_to,
            duration,
            offset,
            toggle_continuous,
        )
        try:
            last_command = commands[-1]
            if (
                isinstance(last_command, PlayReadoutCommand)
                and last_command.cell == recording_cmd.cell
            ):
                recording_cmd.follows_readout = True
                last_command.recording = recording_cmd
                last_command._associated_variable_set.update(
                    recording_cmd._associated_variable_set
                )
        except IndexError:
            pass

        return recording_cmd

    def _map_pulse(self, pulse: qicode.proto.Pulse) -> _QiPulse:
        if pulse.HasField("off"):
            return _QiPulse.off()
        elif pulse.HasField("continuous"):
            if pulse.continuous.HasField("frequency"):
                frequency_expr = self._map_expression(pulse.continuous.frequency)
            else:
                frequency_expr = None
            return _QiPulse.cw(
                self._map_expression(pulse.continuous.amplitude),
                self._map_expression(pulse.continuous.phase),
                frequency_expr,
            )
        elif pulse.HasField("discrete"):
            if pulse.discrete.HasField("shape"):
                shape = Shape.REGISTRY.get(pulse.discrete.shape.id)
                if shape is None:
                    raise RuntimeError(
                        f"Shape with ID {pulse.discrete.shape.id} is not registered"
                    )
            else:
                shape = ShapeLib.rect
            if pulse.discrete.HasField("frequency"):
                frequency_expr = self._map_expression(pulse.discrete.frequency)
            else:
                frequency_expr = None
            return _QiPulse(
                self._map_expression(pulse.discrete.length),
                shape,
                self._map_expression(pulse.discrete.amplitude),
                self._map_expression(pulse.discrete.phase),
                frequency_expr,
                pulse.discrete.hold,
            )
        else:
            raise AssertionError(f"Unknown pulse type {pulse}")

    def _map_condition(self, expr: qicode.proto.Expression) -> QiCondition:
        if expr.HasField("binary"):
            op_calc = {
                qicode.proto.Expression.Binary.Operator.Lt: QiOpCond.LT,
                qicode.proto.Expression.Binary.Operator.Le: QiOpCond.LE,
                qicode.proto.Expression.Binary.Operator.Eq: QiOpCond.EQ,
                qicode.proto.Expression.Binary.Operator.Gt: QiOpCond.GT,
                qicode.proto.Expression.Binary.Operator.Ge: QiOpCond.GE,
                qicode.proto.Expression.Binary.Operator.Ne: QiOpCond.NE,
            }.get(expr.binary.op)
            assert op_calc is not None, (
                f"Cannot form condition with operator {expr.binary.op}"
            )
            return QiCondition(
                val1=QiExpression._from(self._map_expression(expr.binary.lhs)),
                op=op_calc,
                val2=QiExpression._from(self._map_expression(expr.binary.rhs)),
            )
        else:
            raise ValueError("Expression must be a binary condition")

    def _map_command(
        self, command: qicode.proto.Command, commands: list[QiCommand]
    ) -> None:
        if command.HasField("digitalTriggerCommand"):
            qi_expr = self._map_expression(command.digitalTriggerCommand.length)
            assert isinstance(qi_expr, int | float), (
                "digital trigger length must be a constant"
            )
            commands.append(
                DigitalTriggerCommand(
                    self._map_cell(command.digitalTriggerCommand.cell),
                    list(command.digitalTriggerCommand.outputs),
                    qi_expr,
                )
            )
        elif command.HasField("waitCommand"):
            commands.append(
                WaitCommand(
                    self._map_cell(command.waitCommand.cell),
                    self._map_expression(command.waitCommand.length),
                )
            )
        elif command.HasField("recordingCommand"):
            rec = self._map_recording_command(command.recordingCommand, commands)
            # When True, RecordingCommand is added to the readout command
            if not rec.follows_readout:
                commands.append(rec)
        elif command.HasField("playCommand"):
            commands.append(
                PlayCommand(
                    self._map_cell(command.playCommand.cell),
                    self._map_pulse(command.playCommand.pulse),
                )
            )
        elif command.HasField("playReadoutCommand"):
            commands.append(
                PlayReadoutCommand(
                    self._map_cell(command.playReadoutCommand.cell),
                    self._map_pulse(command.playReadoutCommand.pulse),
                )
            )
        elif command.HasField("playFluxCommand"):
            raise NotImplementedError("PlayFluxCommand")
        elif command.HasField("rotateFrameCommand"):
            expr = self._map_expression(command.rotateFrameCommand.angle)
            assert isinstance(expr, float | int), (
                "Rotate Frame command must be constant"
            )
            commands.append(
                RotateFrameCommand(
                    self._map_cell(command.rotateFrameCommand.cell), angle=expr
                )
            )
        elif command.HasField("syncCommand"):
            commands.append(
                SyncCommand(
                    [self._map_cell(cell) for cell in command.syncCommand.cells]
                )
            )
        elif command.HasField("storeCommand"):
            result = QiResult(command.storeCommand.saveTo)
            commands.append(
                StoreCommand(
                    self._map_cell(command.storeCommand.cell),
                    store_var=self._variables[command.storeCommand.var.id],
                    save_to=result,
                )
            )
        elif command.HasField("assignCommand"):
            commands.append(
                AssignCommand(
                    self._variables[command.assignCommand.destination.id],
                    self._map_expression(command.assignCommand.value),
                )
            )
        elif command.HasField("declareCommand"):
            qi_type = self._map_type(command.declareCommand.type)
            if command.declareCommand.HasField("initialValue"):
                value = self._map_expression(command.declareCommand.initialValue)
                assert isinstance(value, int | float | list)
            else:
                value = None

            if qi_type == QiType.UNKNOWN and isinstance(value, list):
                qi_type = QiType.ARRAY(element_type=QiType.UNKNOWN, length=len(value))

            if command.declareCommand.HasField("name"):
                name = command.declareCommand.name
            else:
                name = None

            static = command.declareCommand.static

            if static:
                var = _QiStaticVariable(qi_type, value, name)
            else:
                var = _QiVariableBase(qi_type, value, name)

            self._variables[command.declareCommand.var.id] = var
            commands.append(DeclareCommand(var))
            if value is not None and not static and not qi_type.is_array():
                val = _QiConstValue(value)
                val._type_info.set_type(qi_type, _TypeDefiningUse.VARIABLE_DEFINITION)
                commands.append(AssignCommand(var, val))
        elif command.HasField("whileCommand"):
            while_cm = command.whileCommand
            commands.append(
                WhileCommand(
                    self._map_condition(while_cm.condition),
                    self._map_commands(while_cm.body),
                )
            )
        elif command.HasField("ifCommand"):
            if_cm = command.ifCommand
            commands.append(
                IfCommand(
                    self._map_condition(if_cm.condition), self._map_commands(if_cm.body)
                )
            )
        elif command.HasField("elseCommand"):
            else_cm = command.elseCommand
            if len(commands) == 0:
                raise RuntimeError("Else is not preceded by If")
            if_cmd = commands[-1]
            if not isinstance(if_cmd, IfCommand):
                raise RuntimeError("Else is not preceded by If")
            if_cmd.add_else_body(self._map_commands(else_cm.body))
        elif command.HasField("parallelCommand"):
            parallel_cm = ParallelCommand()
            body = self._map_commands(command.parallelCommand.body)
            parallel_cm.body += (
                body  # So visitors also find commands in Parallel blocks.
            )
            parallel_cm.append_entry(body)

            # If previous command is also parallel, combine by adding another parallel entry at previous command
            try:
                cmd = commands[-1]
                if isinstance(cmd, ParallelCommand) and len(cmd.entries) < 2:
                    cmd.entries.append(body)
                    cmd._associated_variable_set.update(
                        parallel_cm._associated_variable_set
                    )
                else:
                    commands.append(parallel_cm)
            except IndexError:
                commands.append(parallel_cm)
        elif command.HasField("asmCommand"):
            seq_instr = SequencerInstruction.from_str(command.asmCommand.instruction)
            # TODO: correct length in cycles (should be from ASM command)
            commands.append(
                AsmCommand(
                    self._map_cell(command.asmCommand.cell),
                    seq_instr,
                    1,
                )
            )
        elif command.HasField("forRangeCommand"):
            var = self._variables[command.forRangeCommand.var.id]
            commands.append(
                ForRangeCommand(
                    var,
                    self._map_expression(command.forRangeCommand.start),
                    self._map_expression(command.forRangeCommand.end),
                    self._map_expression(command.forRangeCommand.step),
                    self._map_commands(command.forRangeCommand.body),
                )
            )
        elif command.HasField("gateCommand"):
            new_commands = self._map_commands(command.gateCommand.body)
            find_cells = QiCMContainedCellVisitor()

            for cmd in new_commands:
                cmd.accept(find_cells)

                if isinstance(cmd, AssignCommand):
                    raise RuntimeError(
                        "Assign inside QiGate might result in unwanted side effects."
                    )

            if len(find_cells.contained_cells) > 1:
                commands.append(SyncCommand(list(find_cells.contained_cells)))

            commands.extend(new_commands)
        else:
            raise NotImplementedError(f"Command {command}")

    def _map_commands(
        self, commands: Iterable[qicode.proto.Command]
    ) -> list[QiCommand]:
        ret_commands: list[QiCommand] = []
        for command in commands:
            self._map_command(command, ret_commands)
        return ret_commands

    @property
    def commands(self):
        """returns the commands of the job"""
        return self._qi_commands

    def _register_cells(self, cells: list[QiCell]):
        if len(self.cells) > 0:
            raise RuntimeError("Can only register one set of cells at a QiJob.")

        self.cells = cells

    def _register_couplers(self, couplers: list[QiCoupler]):
        if len(self.couplers) > 0:
            raise RuntimeError("Can only register one set of couplers at a QiJob.")

        self.couplers = couplers

    def _run_analyses(self):
        """
        Executes needed (dataflow) analyses.
        These mutate the commands in QiJob by inserting additional instructions, therefore
        they should only run once, in order to avoid duplicate instructions.
        """
        from .analysis.qi_insert_mem_parameters import (
            replace_variable_assignment_with_store_commands,
        )

        if not self._performed_analyses:
            replace_variable_assignment_with_store_commands(self)

        self._performed_analyses = True

    def _simulate_recordings(self) -> dict[Any, list[RecordingCommand]]:
        """
        Simulates the order RecordingCommand executions.
        The result of this simulation is used to disentangle the recordings buffer
        and reassociate the individual recording results with their corresponding Recording commands.
        It might return more elements than are recorded during the real execution.
        """

        # We first check if there are Recording commands at positions which we can not simulate.
        # i.e. If-Else, ForRanges with start or end that are neither constant nor other loop variables.
        # If this is the case we cannot simulate the order.
        visitor = QiResultCollector()
        for cmd in self.commands:
            cmd.accept(visitor)

        if len(visitor.found_qi_results) == 0:
            return {cell: [] for cell in self.cells}
        elif visitor.recording_in_if:
            raise RuntimeError("Recording command within If-Else statement.")

        # Next we simulate all loops and collect the respective Recording commands inside.
        from .qi_simulate import Simulator

        simulator = Simulator(self.cells)
        simulator._simulate(self.commands)

        return simulator.cell_recordings

    def _build_program(
        self, sample: QiSample | None = None, cell_map: list[int] | None = None
    ):
        if sample is not None and cell_map is not None:
            sample = sample._arrange_for_controller()
            sample = [sample[m] if m < len(sample) else None for m in cell_map]

        if cell_map is None:
            cell_map = list(range(len(self.cells)))

        # TODO Check that this works with None and right order now
        self._resolve_properties(sample)

        for cell in self.cells:
            if len(cell._get_unresolved_properties()) > 0:
                raise RuntimeError(
                    f"Unresolved properties {cell._get_unresolved_properties()} at cell {cell}"
                )

        self._run_analyses()

        sim_result = self._simulate_recordings()
        for cell in self.cells:
            cell._result_recording_order = [
                x.result_box
                for x in filter(lambda x: x.result_box is not None, sim_result[cell])
            ]

        self.cell_seq_dict = build_program(
            self.cells,
            cell_map,
            self.commands,
            self.skip_nco_sync,
            self.nco_sync_length,
        )

        self._var_reg_map = get_all_variables(self.cell_seq_dict)
        self._build_done = True

    def _get_sequencer_codes(self):
        return [self.cell_seq_dict[cell].executable() for cell in self.cells]

    def _get_initial_memory(self):
        return [self.cell_seq_dict[cell].static_region for cell in self.cells]

    def create_experiment(
        self,
        controller,
        sample: QiSample | None = None,
        averages: int = 1,
        cell_map: list[int] | None = None,
        coupling_map: list[int] | None = None,
        data_collection=None,
        use_taskrunner=False,
    ) -> QiCodeExperiment:
        from ..experiment.qicode.base import QiCodeExperiment

        exp = QiCodeExperiment(
            controller,
            *self._prepare_experiment_params(
                sample,
                averages,
                cell_map,
                coupling_map,
                data_collection,
                use_taskrunner,
            ),
        )

        if data_collection is None:
            if self._custom_processing is not None:
                exp._taskrunner.update(self._custom_processing)
            if self._custom_data_handler is not None:
                exp._data_handler_factory = DataHandler.get_custom_wrapper_factory(
                    self._custom_data_handler
                )

        # Provide a human-readable description of the execution
        cell_map = cell_map or list(range(len(self.cells)))
        str_map = ", ".join(f"q[{i}] -> sample[{m}]" for i, m in enumerate(cell_map))
        exp._job_representation = f"{self}\n\nmapped as {str_map} to\n\n{sample}"

        return exp

    def _prepare_experiment_params(
        self,
        sample: QiSample | None = None,
        averages: int = 1,
        cell_map: list[int] | None = None,
        coupling_map: list[int] | None = None,
        data_collection=None,
        use_taskrunner=False,
    ):
        data_collection = data_collection or (
            "custom" if self._custom_processing else "average"
        )

        # If float, convert averages to int
        averages = int(averages)

        if sample is None:
            sample = QiSample(len(self.cells))
        elif len(sample) < len(self.cells):
            raise ValueError(
                "Need to submit a QiSample with at least as many cells as the job "
                f"has ({len(self.cells)}), but only {len(sample)} provided."
            )

        if cell_map is None:
            # Use the first cells of the sample
            cell_map = list(range(len(self.cells)))
        else:
            if len(cell_map) != len(self.cells):
                raise ValueError(
                    "cell_map needs to have as many entries as the job has cells, but "
                    f"{len(cell_map)} entries given and {len(self.cells)} required!"
                )
            if len(set(cell_map)) != len(cell_map):
                raise ValueError("Duplicate values not allowed in cell_map!")
            if any(m < 0 or m >= len(sample) for m in cell_map):
                raise IndexError(
                    "cell_map values can only point to valid indices within the passed"
                    f" QiSample object, i.e. values between 0 and {len(sample) - 1}."
                )

        if coupling_map is None:
            coupling_map = list(range(len(self.couplers)))

        # Translate cell_map from sample cells ("cells") to QiController cells
        cell_map = [sample.cell_map[c] for c in cell_map]

        self._build_program(sample, cell_map)

        for_range_list = [
            self.cell_seq_dict[cell]._for_range_list for cell in self.cells
        ]

        return (
            self.cells,
            self.couplers,
            self._get_sequencer_codes(),
            self._get_initial_memory(),
            averages,
            for_range_list,
            cell_map,
            coupling_map,
            self._var_reg_map,
            data_collection,
            use_taskrunner,
        )

    def run(
        self,
        controller,
        sample: QiSample | None = None,
        averages: int = 1,
        cell_map: list[int] | None = None,
        coupling_map: list[int] | None = None,
        data_collection: DataCollection | None = None,
        use_taskrunner: bool = False,
    ) -> ExecutionInfo:
        """executes the job and returns execution information

        :param controller: the QiController on which the job should be executed
        :param sample: the QiSample object used for execution of pulses and extracts parameters for the experiment
        :param averages: the number of executions that should be averaged, by default 1
        :param cell_map: A list containing the indices of the cells
        :param coupling_map: A list containing the indices of the couplers
        :param data_collection: the data_collection mode for the result, by default "average"
        :param use_taskrunner: if the execution should be handled by the Taskrunner
            Some advanced schemes and data_collection modes are currently only supported
            by the Taskrunner and not yet by a native control flow.
        """
        exp = self.create_experiment(
            controller,
            sample,
            averages,
            cell_map,
            coupling_map,
            data_collection,
            use_taskrunner,
        )
        results = exp.run()
        return ExecutionInfo(results, exp.time_tag())

    def compile(
        self,
        use_qicode_compiler: bool = True,
        compiler_binary: str | None = None,
        output_mode: Literal["assembly", "binary"] = "binary",
    ) -> Compilation:
        assert use_qicode_compiler, (
            "Compilation is currently only supported using the QiCode compiler"
        )
        return QiCodeCompiler(compiler_binary).compile(self, output_mode=output_mode)

    def _new_compiler_submit(
        self,
        qic: qiclib.QiController,
        averages: int,
        binary: str | None = None,
        data_collection: DataCollection = "average",
    ):
        warnings.warn(
            "This function is experimental and should never be used in production unless you know what you do",
            UserWarning,
        )
        compilation = self.compile(
            use_qicode_compiler=True, compiler_binary=binary, output_mode="binary"
        )
        proto_job = _generate_proto_from_binary_compilation(compilation)
        for i, cell in enumerate(self.cells):
            result_cell = compilation.cell(i)
            cell._result_recording_order = [
                cell.get_result_container(name) for name in result_cell.recordings()
            ]
        job_id = qic.cell.submit(
            proto_job,
            averages,
            list(range(len(self.cells))),
            recordings=[len(cell.recordings()) for cell in compilation.cells()],
            data_collection=data_collection,
        )
        return SubmittedJob(
            job_id,
            qic,
            data_handler_factory=DataHandler.get_factory_by_name(data_collection),
            cell_list=self.cells,
            averages=averages,
            use_taskrunner=False,
        )

    def submit(
        self,
        controller,
        sample: QiSample | None = None,
        averages: int = 1,
        cell_map: list[int] | None = None,
        coupling_map: list[int] | None = None,
        data_collection=None,
        use_taskrunner=False,
    ) -> SubmittedJob:
        """Submits the job to the QiController

        This method is comparabe to :meth:`run`, but doesn't execute instantaneouly.
        Instead, the pulse is pushed onto an internal queue and executed when no other job is running.
        This enables multi-user access to the QiController and queuing jobs when network latency becomes
        a noticeable overhead.

        .. warning::
            This method is highly experimental and can lead to deadlocks and hanging of the QiController if
            used incorrectly. It is recommended to use the :meth:`run` method while this is in an experimental state.

        :param controller: the QiController on which the job should be executed
        :param sample: the QiSample object used for execution of pulses and extracts parameters for the experiment
        :param averages: the number of executions that should be averaged, by default 1
        :param cell_map: A list containing the indices of the cells
        :param cell_map: A list containing the indices of the couplers
        :param data_collection: the data_collection mode for the result, by default "average"
        :param use_taskrunner: if the execution should be handled by the Taskrunner
            Some advanced schemes and data_collection modes are currently only supported
            by the Taskrunner and not yet by a native control flow.
        :return: a `SubmittedJob` that can be used to query the results.
        """
        exp = self.create_experiment(
            controller,
            sample,
            averages,
            cell_map,
            coupling_map,
            data_collection,
            use_taskrunner,
        )
        job_id = exp.submit()
        return SubmittedJob.from_experiment(job_id, exp)

    def run_with_data_callback(self, on_new_data: Callable[[dict], None]):
        pass

    def run_streamed(self):
        pass

    def set_custom_data_processing(
        self,
        file: str,
        params: list | None = None,
        converter: Callable[[list], list] | None = None,
        mode: TaskRunner.DataMode | str = TaskRunner.DataMode.INT32,
        data_handler: Callable[[list[QiCell], DataProvider], None] | None = None,
    ):
        from qiclib.experiment.qicode.base import _TaskrunnerSettings

        if isinstance(mode, str):
            mode = TaskRunner.DataMode[mode.upper()]

        self._custom_processing = _TaskrunnerSettings(
            file, "QiCode[Custom]", params, mode, converter
        )
        self._custom_data_handler = data_handler

    def get_assembly(
        self,
        cells: QiCells | None = None,
        cell_index=0,
        cell_map: list[int] | None = None,
    ):
        self._build_program(cells, cell_map)

        cell = self.cells[cell_index]

        return list(map(str, self.cell_seq_dict[cell].instruction_list))

    def print_assembler(
        self,
        cells: QiCells | None = None,
        cell_index=0,
        cell_map: list[int] | None = None,
        use_qicode_compiler: bool = False,
        compiler_binary: str | None = None,
    ):
        """
        Prints the commands as assembler code

        :param cells: the QiCells object for execution of pulses and saving result
        :param cell_index: the index of the cell in QiCells
        """
        print(f"Print program for cell index {cell_index}")
        if use_qicode_compiler:
            result = self.compile(
                compiler_binary=compiler_binary, output_mode="assembly"
            )
            code = result.assembly()[cell_index]
            for el in code:
                print(el)
        else:
            self._build_program(cells, cell_map)

            cell = self.cells[cell_index]

            self.cell_seq_dict[cell].print_assembler()

    def _resolve_properties(self, sample: QiSample):
        # Check if any job cell has unresolved properties -> if not, return
        if not any(cell.has_unresolved_properties for cell in self.cells):
            return

        if sample is None:
            raise ValueError("QiSample needs to be passed to resolve job properties!")

        for i, cell in enumerate(self.cells):
            if cell.has_unresolved_properties:
                if i < len(sample) and sample[i] is not None:
                    cell._resolve_properties(sample[i]._properties)
                else:
                    raise ValueError(
                        f"Cell {i} of the job has unresolved properties but no QiSample "
                        "cell is specified for it! Check your cell_map."
                    )

    def __str__(self) -> str:
        from .qi_visitor import QiStringifyJob

        stringify_job = QiStringifyJob()
        return stringify_job.stringify(self)
