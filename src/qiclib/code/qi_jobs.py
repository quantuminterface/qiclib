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

import functools
import warnings
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any, Callable, Generic, TypeVar

import numpy as np

from qiclib.code.qi_command import (
    AsmCommand,
    AssignCommand,
    DeclareCommand,
    DigitalTriggerCommand,
    ForRangeCommand,
    IfCommand,
    ParallelCommand,
    PlayCommand,
    PlayFluxCommand,
    PlayReadoutCommand,
    QiCellCommand,
    QiCommand,
    RecordingCommand,
    RotateFrameCommand,
    StoreCommand,
    SyncCommand,
    WaitCommand,
)
from qiclib.code.qi_prog_builder import build_program, get_all_variables
from qiclib.code.qi_pulse import QiPulse
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
    _QiConstValue,
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


class QiCell:
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
        self.cell_id = cell_id
        self.manipulation_pulses: list[QiPulse] = []
        self.digital_trigger_sets: list[digital_trigger.TriggerSet] = []
        self.flux_pulses: list[QiPulse] = []
        self.readout_pulses: list[QiPulse] = []
        self._result_container: dict[str, QiResult] = {}
        # The order in which recorded values are assigned to which result container
        self._result_recording_order: list[QiResult] = []
        self._unresolved_property: set[QiCellProperty] = set()
        if job is None:
            self._job_ref = QiJob.current()
        else:
            self._job_ref = job
        self._relevant_vars: set[_QiVariableBase] = set()

        # These attributes are determined by dataflow analyses
        self._initial_manip_freq: float = None
        self._initial_readout_freq: float = None
        self._initial_rec_offset: float = None
        self._initial_phase: float = None
        self._initial_amplitude: float = None

        self._rec_length: int | float | QiCellProperty = None

        self._properties: dict[str | QiCellProperty, Any] = {}

    def __getitem__(self, key):
        if QiJob.current() != self._job_ref:
            raise RuntimeError(
                "Tried getting values for cells registered to other QiJob"
            )

        prop = self._properties.get(key, QiCellProperty(self, key))

        if isinstance(prop, QiCellProperty):
            self._unresolved_property.add(key)
        return prop

    def __setitem__(self, key, value):
        if QiJob.current() != self._job_ref:
            raise RuntimeError(
                "Tried setting values for cells registered to other QiJob"
            )
        self._properties[key] = value

    def __call__(self, qic):
        return qic.cell[self.qic_cell]

    def get_properties(self):
        return self._properties.copy()

    def add_pulse(self, pulse: QiPulse):
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
        freq = self._initial_manip_freq
        return freq() if isinstance(freq, QiCellProperty) else freq

    @property
    def initial_phase(self):
        if self._initial_phase is None:
            if len(self.manipulation_pulses) > 0:
                warnings.warn("Manipulation pulses without phase given, using 0.")
            return 0  # Default phase
        phase = self._initial_phase
        return phase() if isinstance(phase, QiCellProperty) else phase

    @property
    def initial_amplitude(self):
        if self._initial_amplitude is None:
            if len(self.manipulation_pulses) > 0:
                warnings.warn("Manipulation pulses without amplitude given, using 1.")
            return 1  # Default amplitude
        amplitude = self._initial_amplitude
        return amplitude() if isinstance(amplitude, QiCellProperty) else amplitude

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

    def add_readout_pulse(self, pulse: QiPulse):
        if pulse not in self.readout_pulses:
            self.readout_pulses.append(pulse)

        if len(self.readout_pulses) > 13:
            raise RuntimeError("Too many pulses in use")

        return self.readout_pulses.index(pulse) + 1  # index 0 and 15 are reserved

    @property
    def initial_readout_frequency(self):
        if self._initial_readout_freq is None:
            if len(self.readout_pulses) > 0:
                warnings.warn("Readout pulses without frequency given, using 30 MHz.")
            return 30e6  # Default frequency
        freq = self._initial_readout_freq
        return freq() if isinstance(freq, QiCellProperty) else freq

    @property
    def recording_length(self):
        """the length of the recording pulse"""
        if self._rec_length is not None:
            return (
                self._rec_length()
                if isinstance(self._rec_length, QiCellProperty)
                else self._rec_length
            )

        return 0

    @property
    def initial_recording_offset(self):
        """the recording offset in seconds"""
        if self._initial_rec_offset is not None:
            return (
                self._initial_rec_offset()
                if isinstance(self._initial_rec_offset, QiCellProperty)
                else self._initial_rec_offset
            )

        return 0

    def get_result_container(self, result: str) -> QiResult:
        if result in self._result_container:
            return self._result_container[result]  # was already added
        else:
            box = QiResult(result)
            box._cell = self
            self._result_container[result] = box
            return box

    def add_variable(self, var: _QiVariableBase):
        self._relevant_vars.add(var)

    def get_number_of_recordings(self):
        return len(self._result_recording_order)

    def set_default_readout(self, pulse):
        pass

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
        if name is None:
            result_dict = {}
            for key, container in self._result_container.items():
                result_dict.update({key: container.get()})
            return result_dict

        else:
            return self._result_container[name].get()

    def _resolve_properties(self, len_dict: dict[QiCellProperty, Any]):
        keys = list(self._unresolved_property)

        missing_keys = self._unresolved_property.difference(len_dict.keys())
        if missing_keys:
            raise RuntimeError(
                f"Cell {self.cell_id}: Not all properties for job could be resolved. "
                f"Missing properties: {missing_keys}"
            )

        for key in keys:
            self._properties[key] = len_dict[key]

    @property
    def has_unresolved_properties(self):
        return len(self._unresolved_property) > 0

    def _get_unresolved_properties(self):
        return [
            key
            for key in list(self._unresolved_property)
            if self._properties.get(key) is None
        ]

    def __str__(self) -> str:
        return f"QiCell({self.cell_id})"


class QiCells:
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

    def __init__(self, num: int, job: QiJob = None) -> None:
        self.cells = [QiCell(x) for x in range(num)]
        if job is None:
            QiJob.current()._register_cells(self.cells)
        else:
            job._register_cells(self.cells)

    def __getitem__(self, key):
        return self.cells[key]

    def __len__(self):
        return len(self.cells)


class QiCoupler:
    def __init__(self, associated_unit_cell: QiCell, coupling_index: int):
        self.associated_unit_cell = associated_unit_cell
        self.coupling_index = coupling_index
        self.coupling_pulses: list[QiPulse] = []

    def add_pulse(self, pulse: QiPulse):
        self.coupling_pulses.append(pulse)
        return len(self.coupling_pulses)


class QiCouplers:
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
        if len(QiJob.current().cells) == 0:
            raise RuntimeError(
                "No cells in the QiJob found."
                "Note that couplers must be instantiated after cells."
            )

        self._couplers = [
            QiCoupler(QiJob.current().cells[i // 2], i % 2) for i in range(count)
        ]
        QiJob.current()._register_couplers(self._couplers)

    def __getitem__(self, key):
        return self._couplers[key]

    def __len__(self):
        return len(self._couplers)


class _JobDescription:
    """Saves experiment descriptions and handles storage of commands"""

    def __init__(self) -> None:
        self._commands: list[QiCommand] = []
        self._ContextStack: list[list[QiCommand]] = []

    def __getitem__(self, key):
        return self._commands[key]

    def __len__(self):
        return len(self._commands)

    def add_command(self, command):
        """Checks current command for used cells and raises error, if cells are not defined for current QiJob"""
        if isinstance(command, QiCellCommand):
            if QiJob().current() != command.cell._job_ref:
                raise RuntimeError("Cell not defined for current job")

        self._commands.append(command)

    def open_new_context(self):
        """Saves current commands in a stack and clears command list"""
        self._ContextStack.append(self._commands.copy())
        self._commands = []

    def close_context(self) -> list[QiCommand]:
        """returns the current command list, and loads the commands from top of stack"""
        current_commands = self._commands.copy()
        self._commands = self._ContextStack.pop()

        return current_commands

    def reset(self):
        self._commands = []
        self._ContextStack = []


_T = TypeVar("_T")


class _QiContextManager(ABC, Generic[_T]):
    """Base Class for If, Else, ForRange and Parallel.
    Defines functions for storing commands."""

    def __init__(self, command: _T | None) -> None:
        super().__init__()
        self._command = command

    def __enter__(self):
        QiJob.current()._open_new_context()
        return self._command if self._command is not None else self

    def __exit__(self, exception_type, exception_value, traceback):
        self._update_body(QiJob.current()._close_context())

    @abstractmethod
    def _update_body(self, body: list[QiCommand]):
        pass


class If(_QiContextManager[QiCondition]):
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

    def __init__(self, condition: QiCondition):
        super().__init__(IfCommand(condition))

    def _update_body(self, body: list[QiCommand]):
        self._command.body = body
        QiJob.current()._add_command(self._command)


class Else(_QiContextManager[None]):
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

    def __init__(self):
        super().__init__(None)

    def __enter__(self):
        self.if_cmd = QiJob.current().commands[-1]

        if not isinstance(self.if_cmd, IfCommand):
            raise RuntimeError("Else is not preceded by If")

        QiJob.current()._open_new_context()
        return self

    def _update_body(self, body: list[QiCommand]):
        self.if_cmd.add_else_body(body)


class Parallel(_QiContextManager[ParallelCommand]):
    """Pulses defined in body are united in one trigger command."""

    def __init__(self):
        super().__init__(ParallelCommand())

    def _update_body(self, body: list[QiCommand]):
        self._command.body += body  # So visitors also find commands in Parallel blocks.
        self._command.append_entry(body)

        # If previous command is also parallel, combine by adding another parallel entry at previous command
        try:
            cmd = QiJob.current().commands[-1]
            if isinstance(cmd, ParallelCommand) and len(cmd.entries) < 2:
                cmd.entries.append(body)
                cmd._associated_variable_set.update(
                    self._command._associated_variable_set
                )
            else:
                QiJob.current()._add_command(self._command)
        except IndexError:
            QiJob.current()._add_command(self._command)


class ForRange(_QiContextManager[ForRangeCommand]):
    """Adds ForRange to program.
    If multiple cells are used inside body, a synchronisation between the cells is done before the ForRange as well as after the end of the body.
    If QiTimeVariable is used as var, loops starting at 0 are unrolled, to skip pulses/waits inside body using var as length.
    Raises exception if start, end and step are not set up properly."""

    def __init__(
        self,
        var: _QiVariableBase,
        start: _QiVariableBase | int | float,
        end: _QiVariableBase | int | float,
        step: int | float = 1,
    ):
        from .qi_types import (
            _add_equal_constraints,
            _IllegalTypeReason,
            _TypeConstraintReasonQiCommand,
        )

        if not isinstance(var, _QiVariableBase):
            raise RuntimeError(
                "Can only use QiVariables as control variable in ForRanges."
            )

        start_expr = QiExpression._from(start)
        end_expr = QiExpression._from(end)
        step_expr = QiExpression._from(step)

        var._type_info.add_illegal_type(QiType.STATE, _IllegalTypeReason.FOR_RANGE)
        start_expr._type_info.add_illegal_type(
            QiType.STATE, _IllegalTypeReason.FOR_RANGE
        )
        end_expr._type_info.add_illegal_type(QiType.STATE, _IllegalTypeReason.FOR_RANGE)
        step_expr._type_info.add_illegal_type(
            QiType.STATE, _IllegalTypeReason.FOR_RANGE
        )

        _add_equal_constraints(
            QiType.TIME,
            _TypeConstraintReasonQiCommand(ForRangeCommand),
            var,
            start_expr,
            end_expr,
            step_expr,
        )
        _add_equal_constraints(
            QiType.FREQUENCY,
            _TypeConstraintReasonQiCommand(ForRangeCommand),
            var,
            start_expr,
            end_expr,
            step_expr,
        )
        _add_equal_constraints(
            QiType.PHASE,
            _TypeConstraintReasonQiCommand(ForRange),
            var,
            start_expr,
            end_expr,
            step_expr,
        )
        _add_equal_constraints(
            QiType.AMPLITUDE,
            _TypeConstraintReasonQiCommand(ForRange),
            var,
            start_expr,
            end_expr,
            step_expr,
        )
        _add_equal_constraints(
            QiType.NORMAL,
            _TypeConstraintReasonQiCommand(ForRangeCommand),
            var,
            start_expr,
            end_expr,
            step_expr,
        )

        if not isinstance(start, _QiVariableBase) and not isinstance(
            end, _QiVariableBase
        ):
            if start > end and step >= 0:
                raise ValueError(
                    f"Definition of ForRange faulty: start ({start}) is greater than end ({end}) and the step is positive"
                )
            elif start < end and step <= 0:
                raise ValueError(
                    f"Definition of ForRange faulty: start ({start}) is less than end ({end}) and the step is negative"
                )

        super().__init__(ForRangeCommand(var, start_expr, end_expr, step_expr, body=[]))

    def _update_body(self, body: list[QiCommand]):
        self._command.body = body
        QiJob.current()._add_command(self._command)


class QiVariable(_QiVariableBase):
    """Used as variables for use in program.
    If no type is provided as an argument, it will infer its type.
    """

    def __init__(
        self,
        type: QiType | type[int] | type[float] = QiType.UNKNOWN,
        value=None,
        name=None,
    ) -> None:
        if type is int:
            type = QiType.NORMAL
        elif type is float:
            type = QiType.TIME

        super().__init__(type, value, name=name)
        QiJob.current()._add_command(DeclareCommand(self))
        if self.value is not None:
            val = _QiConstValue(value)
            val._type_info.set_type(type, _TypeDefiningUse.VARIABLE_DEFINITION)
            QiJob.current()._add_command(AssignCommand(self, val))


class QiJob:
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
        self.qi_results: list[QiResult] = []
        self.cells: list[QiCell] = []
        self.couplers: list[QiCoupler] = []
        self.skip_nco_sync = skip_nco_sync
        self.nco_sync_length = nco_sync_length

        self._description = _JobDescription()

        # Build
        self._performed_analyses = False
        self._build_done = False
        self._arranged_cells: list[QiCell | None] = []
        self._var_reg_map: dict[_QiVariableBase, dict[QiCell, int]] = {}

        # Run
        self._custom_processing = None
        self._custom_data_handler = None

    _current_job: QiJob | None = None

    @staticmethod
    def current() -> QiJob:
        """
        Get the current job reference, when this job is used to build a program.
        """
        if QiJob._current_job is None:
            raise RuntimeError("Can not use command outside QiJob context manager.")
        return QiJob._current_job

    def __enter__(self):
        QiJob._current_job = self
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        for cmd in self.commands:
            cmd.accept(QiTypeFallbackVisitor())

        for cmd in self.commands:
            cmd.accept(QiPostTypecheckVisitor())

        _QiVariableBase.reset_str_id()

        QiJob._current_job = None

    def _open_new_context(self):
        self._description.open_new_context()

    def _close_context(self):
        return self._description.close_context()

    def _add_command(self, command):
        self._description.add_command(command)

    @property
    def commands(self):
        """returns the commands of the job"""
        return self._description._commands

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
            self._description._commands.copy(),
            self.skip_nco_sync,
            self.nco_sync_length,
        )

        self._var_reg_map = get_all_variables(self.cell_seq_dict)
        self._build_done = True

    def _get_sequencer_codes(self):
        return [
            [
                instr.get_riscv_instruction()
                for instr in self.cell_seq_dict[cell].instruction_list
            ]
            for cell in self.cells
        ]

    def create_experiment(
        self,
        controller,
        sample: QiSample | None = None,
        averages: int = 1,
        cell_map: list[int] | None = None,
        coupling_map: list[int] | None = None,
        data_collection=None,
        use_taskrunner=False,
    ):
        from ..experiment.qicode.base import QiCodeExperiment

        exp = QiCodeExperiment(
            *self._prepare_experiment_params(
                controller,
                sample,
                averages,
                cell_map,
                coupling_map,
                data_collection,
                use_taskrunner,
            )
        )

        if data_collection is None:
            if self._custom_processing is not None:
                exp._taskrunner.update(self._custom_processing)
            if self._custom_data_handler is not None:
                exp._data_handler_factory = DataHandler.get_custom_wrapper_factory(
                    self._custom_data_handler
                )

        # Provide a human-readable description of the execution
        if cell_map is None:
            cell_map = list(range(len(self.cells)))
        str_map = ", ".join([f"q[{i}] -> sample[{m}]" for i, m in enumerate(cell_map)])
        exp._job_representation = f"{self}\n\nmapped as {str_map} to\n\n{sample}"

        return exp

    def _prepare_experiment_params(
        self,
        controller,
        sample: QiSample | None = None,
        averages: int = 1,
        cell_map: list[int] | None = None,
        coupling_map: list[int] | None = None,
        data_collection=None,
        use_taskrunner=False,
    ):
        if len(self.cells) > len(controller.cell):
            raise IndexError(
                f"This job requires {len(self.cells)} cells but only "
                f"{len(controller.cell)} are available in the QiController."
            )

        if data_collection is None:
            if self._custom_processing is None:
                data_collection = "average"
            else:
                data_collection = "custom"

        # If float, convert averages to int
        averages = int(averages)

        if sample is None:
            sample = QiSample(len(controller.cell))
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

        if any(c < 0 or c >= len(controller.cell) for c in cell_map):
            raise ValueError(
                "The QiSample cell_map can only reference available QiController "
                f"cells, i.e. between 0 and {len(controller.cell) - 1}."
            )

        self._build_program(sample, cell_map)

        for_range_list = []

        for cell in self.cells:
            for_range_list.append(self.cell_seq_dict[cell]._for_range_list)

        return (
            controller,
            self.cells,
            self.couplers,
            self._get_sequencer_codes(),
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
        data_collection=None,
        use_taskrunner=False,
    ):
        """executes the job and returns the results

        :param controller: the QiController on which the job should be executed
        :param sample: the QiSample object used for execution of pulses and extracts parameters for the experiment
        :param averages: the number of executions that should be averaged, by default 1
        :param cell_map: A list containing the indices of the cells
        :param cell_map: A list containing the indices of the couplers
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
        exp.run()

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
    ):
        """
        Prints the commands as assembler code

        :param cells: the QiCells object for execution of pulses and saving result
        :param cell_index: the index of the cell in QiCells
        """
        print(f"Print program for cell index {cell_index}")
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


def Sync(*cells: QiCell):
    """Synchronize cells. Currently implemented by comparing cycle times and adding wait commands. Cannot Sync after If/Else, or load/store to time variables"""
    QiJob.current()._add_command(SyncCommand(list(cells)))


def Play(cell: QiCell, pulse: QiPulse):
    """Add Manipulation command and pulse to cell

    :param cell: the cell that plays the pulse
    :param pulse: the pulse to play
    """
    QiJob.current()._add_command(PlayCommand(cell, pulse))


def PlayReadout(cell: QiCell, pulse: QiPulse):
    """Add Readout command and pulse to cell

    :param cell: the cell that plays the readout
    :param pulse: the readout to play
    """
    QiJob.current()._add_command(PlayReadoutCommand(cell, pulse))


def PlayFlux(coupler: QiCoupler, pulse: QiPulse):
    """
    Add Flux Pulse command to cell

    :param coupler: The coupler that plays the pulse
    :param pulse: The pulse to play
    """
    QiJob.current()._add_command(PlayFluxCommand(coupler, pulse))


def RotateFrame(cell: QiCell, angle: float):
    """Rotates the reference frame of the manipulation pulses played with :python:`Play()`.
    This corresponds to an instantaneous, virtual Z rotation on the Bloch sphere.

    :param cell: the cell for the rotation
    :param angle: the angle of the rotation
    """
    QiJob.current()._add_command(RotateFrameCommand(cell, angle))


def Recording(
    cell: QiCell,
    duration: int | float | QiCellProperty,
    offset: int | float | QiCellProperty | QiExpression = 0,
    save_to: str | None = None,
    state_to: _QiVariableBase | None = None,
    toggleContinuous: bool | None = None,
):
    """Add Recording command to cell

    :param cell: the QiCell for the recording
    :param duration: the duration of the recording window in seconds
    :param offset: the offset of the recording window in seconds
    :param save_to: the name of the QiResult where to save the result data
    :param state_to: the variable in which the obtained qubit state should be stored
    :param toggleContinuous: whether the recording should be repeated continously and seemlessly
        Value True will start the recording, False will stop it (None is for normal mode)
    """
    rec = RecordingCommand(
        cell,
        save_to,
        state_to,
        length=duration,
        offset=offset,
        toggle_continuous=toggleContinuous,
    )
    # When True, RecordingCommand is added to the readout command
    if not rec.follows_readout:
        QiJob.current()._add_command(rec)


def DigitalTrigger(
    cell: QiCell,
    length: float,
    outputs: Iterable[int],
):
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
    QiJob.current()._add_command(DigitalTriggerCommand(cell, list(outputs), length))


def Wait(cell: QiCell, delay: int | float | _QiVariableBase | QiCellProperty):
    """Add Wait command to cell. delay can be int or QiVariable

    :param cell: the QiCell that should wait
    :param delay: the time to wait in seconds
    """
    QiJob.current()._add_command(WaitCommand(cell, delay))


def Store(cell: QiCell, variable: _QiVariableBase, save_to: QiResult):
    """Not implemented yet. Add Store command to cell."""
    QiJob.current()._add_command(StoreCommand(cell, variable, save_to))


def Assign(dst: _QiVariableBase, calc: QiExpression | float | int):
    """Assigns a calculated value to a destination

    :param dst: the destination
    :param calc: the calculation to perform
    """
    QiJob.current()._add_command(AssignCommand(dst, calc))


def ASM(cell: QiCell, instr: SequencerInstruction, cycles=1):
    """Insert assembly instruction"""
    QiJob.current()._add_command(AsmCommand(cell, instr, cycles))


def QiGate(func):
    """decorator for using a function in a QiJob

    :raises RuntimeError: if QiGate inside QiGate
    """

    @functools.wraps(func)
    def wrapper_QiGate(*args, **kwargs):
        start = len(QiJob.current().commands)

        func(*args, **kwargs)

        end = len(QiJob.current().commands)

        find_cells = QiCMContainedCellVisitor()

        for cmd in QiJob.current().commands[start:end]:
            cmd.accept(find_cells)

            if isinstance(cmd, AssignCommand):
                raise RuntimeError(
                    "Assign inside QiGate might result in unwanted side effects."
                )

        if len(find_cells.contained_cells) > 1:
            QiJob.current().commands.insert(
                start, SyncCommand(list(find_cells.contained_cells))
            )

    return wrapper_QiGate


class QiTimeVariable(QiVariable):
    def __init__(self, value=None, name=None):
        super().__init__(type=QiType.TIME, value=value, name=name)


class QiFrequencyVariable(QiVariable):
    def __init__(self, value=None, name=None):
        super().__init__(type=QiType.FREQUENCY, value=value, name=name)


class QiStateVariable(QiVariable):
    def __init__(self, name=None):
        super().__init__(type=QiType.STATE, name=name)


class QiIntVariable(QiVariable):
    def __init__(self, value=None, name=None):
        super().__init__(type=QiType.NORMAL, value=value, name=name)


class QiPhaseVariable(QiVariable):
    def __init__(self, value=None, name=None):
        super().__init__(type=QiType.PHASE, value=value, name=name)


class QiAmplitudeVariable(QiVariable):
    def __init__(self, value=None, name=None):
        super().__init__(type=QiType.AMPLITUDE, value=value, name=name)
