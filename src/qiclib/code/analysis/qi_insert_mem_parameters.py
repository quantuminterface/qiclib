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
This module contains the algorithm to insert MemStoreCommand instructions into a QiJob,
to ensure that the QiCellCommand parameters are correctly set in the recording module.

We define the term 'memory parameter' to mean a parameter of a QiCellCommand that is not
part of the corresponding trigger (or wait) assembly instruction, instead it needs to
be stored in the recording module via a store instruction.
The challenge lies in figuring out where to insert these store instructions, without
increasing performance overhead unnecessarily.

The following is a description of the used algorithm, specialized for the recording offset
memory parameter part of the RecordingCommand command, but generalizes to the other memory parameters.

The entry point of the algorithm is in `insert_recording_offset_store_commands`.
It performs roughly the following steps:

1. For every program point (_CFGNode), determine the next offset needed by a Recording
   instruction, represented by a FlatLatticeValue for each cell.
   (see AnticipatedMemoryParameterAnalysis)

2. For every program point, determine the currently stored offset in the recording module
   for every cell.
   Here we assume, that as soon as a distinct offset is anticipated this value stored.
   (see AvailableMemoryParameterAnalysis)

3. On every edge in the CFG where a distinct offset is anticipated but not available we
   insert a MemStoreCommand instruction in the corresponding place in the QiJob.commands.

(This algorithm is a customized Partial Redundancy Elimination (PRE). The idea is we insert a store
instruction before every Recording instruction and then use PRE to eliminate as many as we can.)

Notes:
    Before we start the main algorithm we insert so called 'pseudo store instructions'.
    These are MemStoreCommand commands inserted into the CFG (but NOT into the QiJob) and simulate
    the unrolling of loops for one iteration.
    Otherwise our analysis thinks that loops might never enter the body once which will lead to
    our algorithm, not placing the store instruction before the loop in the following code:

    .. code-block:: python

        ForRange(i, 0, 100):
            MemStoreCommand(addr, 12e-9)                    <- Instruction would be placed here
            Recording(cells[0], length, offset=12e-9)

    In the event, that the loop never executes the body there would be a unecessary
    store instruction.
    Therefore we unroll the relevant part for our analysis for every loop where its possible
    (If a loop only uses a single invariant offset value.)


    In order to support arbitrary expressions as recording offsets (notably variables) the
    AnticipatedMemoryParameterAnalysis incorporates a typical gen-kill schema to invalidate
    expressions that are modified in the CFG.
    More specifically, gen-kill refers to the fact that whenever a variable (or more general an expression)
    changes, any memory parameter which make use of that variable needs to be reloaded with a store instruction.
    Therefore, on any change of a variable we need to invalidate (kill) the cells which, previously have stored
    this expression using the variable.


    Some commands, like Play/PlayReadout frequency allow for a missing memory parameter.
    In such cases the desired semantics are to keep the last memory parameter.
    This somewhat complicates the algorithm because we generally try to place the store as early as possible,
    possibly, before the command with no frequency.

    .. code-block:: python

        Play(cells[0], QiPulse(..., frequency=20-e9))
        MemStoreCommand(addr, 40e-9)                  <- Instruction would be placed here.
        Play(cells[0], QiPulse(...))
        Play(cells[0], QiPulse(..., frequency=40-e9))

    This would be wrong, because we want the second Play Command to have the same frequency as the first.
    To solve this problem we invalidate the abstract value of the AnticipatedMemoryParameterAnalysis if
    the memory parameter is None.
    This will cause step three in the above sketch of the algorithm to insert the store command after the second play command.
"""

from __future__ import annotations

from copy import copy

from qiclib.code.qi_command import (
    AssignCommand,
    DeclareCommand,
    ForRangeCommand,
    MemStoreCommand,
    ParallelCommand,
    PlayCommand,
    PlayReadoutCommand,
    RecordingCommand,
)
from qiclib.code.qi_dataflow import (
    _CFG,
    CellValues,
    DataflowVisitor,
    FlatLatticeValue,
    _CFGNode,
    forward_dataflow,
    reverse_dataflow,
)
from qiclib.code.qi_jobs import (
    QiCell,
    QiCommand,
    QiJob,
)
from qiclib.code.qi_types import QiType
from qiclib.code.qi_var_definitions import QiCellProperty, QiExpression, _QiConstValue
from qiclib.code.qi_visitor import QiCommandVisitor, QiExpressionVisitor


class Multiple:
    pass


def _collect_memory_param_in_parallel_block(
    parallel: ParallelCommand, config: InsertMemoryParameterConfiguration
) -> dict[QiCell, QiExpression | None]:
    """Collects uses of a memory parameter in a parallel block for every cell.
    If there are multiple different uses, we store `Multiple` in the returned dict.
    """
    mem_param = {}
    for par_block in parallel.entries:
        for command in par_block:
            offset = config.get_memory_param(command)
            if offset is not IrrelevantCommand:
                for cell in command._relevant_cells:
                    if cell not in mem_param:
                        mem_param[cell] = offset
                    elif (
                        offset is None or mem_param[cell] is None
                    ) and offset != mem_param[cell]:
                        mem_param[cell] = Multiple
                    elif (
                        offset is not None
                        and mem_param[cell] is not None
                        and not mem_param[cell]._equal_syntax(offset)
                    ):
                        mem_param[cell] = Multiple
    return mem_param


class AnticipatedMemoryParameterAnalysis(DataflowVisitor):
    def __init__(self, config: InsertMemoryParameterConfiguration):
        super().__init__()
        self.config = config

    def visit_cell_command(self, cell_cmd, cell_values: CellValues, node):
        mem_param = self.config.get_memory_param(cell_cmd)
        if mem_param is not IrrelevantCommand:
            out = copy(cell_values)

            for cell in cell_cmd._relevant_cells:
                if mem_param is None:
                    # Missing memory parameter => invalidate value so stores for subsequent
                    # memory parameters are not placed before this command.
                    out.set_cell_value(cell, FlatLatticeValue.no_const())
                elif FlatLatticeValue.value(mem_param) != cell_values.get_cell_value(
                    cell
                ):
                    assert isinstance(mem_param, QiExpression)
                    out.set_cell_value(cell, FlatLatticeValue.value(mem_param))

            return out
        else:
            return cell_values

    def visit_parallel(self, parallel_cm, cell_values: CellValues, node):
        assert isinstance(parallel_cm, ParallelCommand)
        # Check if parallel command contains multiple recording commands with different offsets.

        mem_param = _collect_memory_param_in_parallel_block(parallel_cm, self.config)

        for v in mem_param.values():
            if v is Multiple:
                raise RuntimeError(
                    "Parallel Blocks with multiple Recording instructions with different offsets are not supported."
                )

        out = copy(cell_values)
        for cell, mem_param in mem_param.items():
            if mem_param is None:
                out.set_cell_value(cell, FlatLatticeValue.no_const())
            else:
                out.set_cell_value(cell, FlatLatticeValue.value(mem_param))

        return out

    def visit_for_range(
        self, for_range_cm: ForRangeCommand, cell_values: CellValues, node
    ):
        var = for_range_cm.var

        # Kill variables that use the loop variable, because it will change in the next iteration
        return cell_values.invalidate_values_containing(var)

    def visit_assign_command(
        self, assign_cmd: AssignCommand, cell_values: CellValues, node
    ):
        var = assign_cmd.var

        # Kill variables that use the assigned variable
        return cell_values.invalidate_values_containing(var)

    def visit_declare_command(
        self, declare_cmd: DeclareCommand, cell_values: CellValues, node
    ):
        var = declare_cmd.var

        # There shouldn't be any expressions which use this variable, but lets be on the safe side
        # and invalidate regardless.
        return cell_values.invalidate_values_containing(var)

    # Needed to handle inserted store commands in cfg by _add_pseudo_store_instructions
    def visit_mem_store_command(self, store_cmd: MemStoreCommand, cell_values, node):
        if store_cmd.addr == self.config.recording_module_address:
            out = copy(cell_values)

            for cell in store_cmd._relevant_cells:
                if store_cmd.value is None:
                    out.set_cell_value(cell, FlatLatticeValue.no_const())
                else:
                    out.set_cell_value(cell, FlatLatticeValue.value(store_cmd.value))

            return out
        else:
            return cell_values


class AvailableMemoryParameterAnalysis(DataflowVisitor):
    "Requires that AnticipatedMemoryParameterAnalysis was run on the CFG beforehand."

    def __init__(self, anticipated_analysis: str):
        self.anticipated_analysis = anticipated_analysis

    def propagate(self, cell_values, node):
        """
        Propagates data flow information for this node, based on the incoming data
        and the anticipated memory param analysis.
        """
        antic = node.value_map[self.anticipated_analysis]

        out = copy(cell_values)

        # Values that are anticipated are assigned immediately.
        for cell, value in antic.values.items():
            if value.type == FlatLatticeValue.Type.VALUE:
                out[cell] = value

        return out

    def visit_cell_command(self, cell_cmd, cell_values, node):
        return self.propagate(cell_values, node)

    def visit_context_manager(self, context_manager, cell_values, node):
        return self.propagate(cell_values, node)

    def visit_if(self, if_cm, cell_values, node):
        return self.propagate(cell_values, node)

    def visit_parallel(self, parallel_cm, cell_values, node):
        return self.propagate(cell_values, node)

    def visit_for_range(self, for_range_cm, cell_values, node):
        out = self.propagate(cell_values, node)
        var = for_range_cm.var
        return out.invalidate_values_containing(var)

    def visit_variable_command(self, variable_cmd, cell_values, node):
        return self.propagate(cell_values, node)

    def visit_assign_command(self, assign_cmd, cell_values, node):
        out = self.propagate(cell_values, node)
        var = assign_cmd.var
        return out.invalidate_values_containing(var)

    def visit_declare_command(self, declare_cmd, cell_values, node):
        out = self.propagate(cell_values, node)
        var = declare_cmd.var
        return out.invalidate_values_containing(var)

    def visit_sync_command(self, sync_cmd, cell_values, node):
        return self.propagate(cell_values, node)

    def visit_asm_command(self, asm_command, cell_values, node):
        return self.propagate(cell_values, node)

    def visit_mem_store_command(self, store_command, cell_values, node):
        return self.propagate(cell_values, node)


def _in_job_insert_command_here(
    node: _CFGNode, pred: _CFGNode.Neighbor
) -> tuple[list[QiCommand], int]:
    pred_node = pred.node

    if node.instruction_index == 0:
        return node.instruction_list, 0
    else:
        if pred.src_edge_type == _CFGNode.SrcEdgeType.IF_FALSE:
            return pred.node.command._else_body, 0
        elif pred.src_edge_type == _CFGNode.SrcEdgeType.IF_TRUE:
            return pred.node.command.body, 0
        else:
            return pred_node.instruction_list, pred_node.instruction_index + 1


class MemoryParameterVisitor(QiCommandVisitor):
    """Checks if visited instructions contain a certain memory parameter."""

    def __init__(self, config: InsertMemoryParameterConfiguration):
        """
        `compare_eq_memory_param` compares to possible values of a memory parameter.
        Usually this just compares two QiExpressions, but it might also include None.
        For example, Play(Readout) frequency can be None.
        """
        # If self.mem_param_values contains Multiple, then there were multiple different offsets for this cell found.
        self.mem_param_values: dict[QiCell, QiExpression | Multiple] = {}
        self.config = config

    def visit_context_manager(self, context_manager, *args, **kwargs):
        for cmd in context_manager.body:
            cmd.accept(self)

    def visit_if(self, if_cm, *args, **kwargs):
        for cmd in if_cm.body:
            cmd.accept(self)

        for cmd in if_cm._else_body:
            cmd.accept(self)

    def visit_cell_command(self, cell_cmd, *args, **kwargs):
        mem_param = self.config.get_memory_param(cell_cmd)
        if mem_param is not IrrelevantCommand:
            for cell in cell_cmd._relevant_cells:
                if cell not in self.mem_param_values:
                    self.mem_param_values[cell] = mem_param

                elif self.mem_param_values[cell] is not Multiple:
                    stored_param_value = self.mem_param_values[cell]

                    if not self.config.compare_eq_memory_param(
                        mem_param, stored_param_value
                    ):
                        self.mem_param_values[cell] = Multiple

    def visit_parallel(self, parallel_cm, *args, **kwargs):
        offsets = _collect_memory_param_in_parallel_block(parallel_cm, self.config)

        for cell, mem_param in offsets.items():
            if mem_param is Multiple:
                self.mem_param_values[cell] = Multiple

            elif cell not in self.mem_param_values:
                self.mem_param_values[cell] = mem_param

            elif not self.config.compare_eq_memory_param(
                self.mem_param_values[cell], mem_param
            ):
                self.mem_param_values[cell] = Multiple


class _MemoryParameterConstantVisitor(QiCommandVisitor):
    """Checks if a given memory parameter is constant."""

    def __init__(self, cell: QiCell, configuration: InsertMemoryParameterConfiguration):
        self.cell = cell
        self.found_memory_param = None
        self.result = True  # Is a constant memory parameter used
        self.config = configuration

    def visit_context_manager(self, context_manager, *args, **kwargs):
        for item in context_manager.body:
            item.accept(self)

    def visit_if(self, if_cm, *args, **kwargs):
        for command in if_cm.body:
            command.accept(self)

        for command in if_cm._else_body:
            command.accept(self)

    def visit_cell_command(self, cell_cmd, *args, **kwargs):
        if cell_cmd.cell is not self.cell:
            return

        mem_param = self.config.get_memory_param(cell_cmd)
        if mem_param is IrrelevantCommand:
            return

        if isinstance(mem_param, (_QiConstValue, QiCellProperty)):
            if self.found_memory_param is None:
                self.found_memory_param = mem_param
            else:
                self.result = self.result and self.config.compare_eq_memory_param(
                    self.found_memory_param, mem_param
                )
        elif mem_param is None:
            # If a memory param is None is should use the previously used value, so it doesn't count as a changed value.
            pass
        else:
            self.result = False


def _has_cell_constant_recording_offset(
    job: QiJob, cell: QiCell, configuration: InsertMemoryParameterConfiguration
):
    visitor = _MemoryParameterConstantVisitor(cell, configuration)

    for cmd in job.commands:
        cmd.accept(visitor)

    return visitor.result


class ExpressionInvariantVisitor(QiCommandVisitor):
    """Checks if an expression in not invalidated (changed) in the visited commands."""

    def __init__(self, expr: QiExpression):
        self.expr = expr
        self.result = True

    def visit_context_manager(self, context_manager, *args, **kwargs):
        for cmd in context_manager.body:
            cmd.accept(self)

    def visit_if(self, if_cm, *args, **kwargs):
        for cmd in if_cm.body:
            cmd.accept(self)

        for cmd in if_cm._else_body:
            cmd.accept(self)

    def visit_assign_command(self, assign_cmd, *args, **kwargs):
        self.result = self.result and (
            self.expr is None or assign_cmd.var not in self.expr.contained_variables
        )

    def visit_declare_command(self, declare_cmd, *args, **kwargs):
        self.result = self.result and (
            self.expr is None or declare_cmd.var not in self.expr.contained_variables
        )

    def visit_for_range(self, for_range_cm, *args, **kwargs):
        self.result = self.result and (
            self.expr is None or for_range_cm.var not in self.expr.contained_variables
        )
        self.visit_context_manager(for_range_cm)


def _insert_pseudo_command_before_for_loop(
    cfg: _CFG, for_loop: _CFGNode, pseudo_command: QiCommand
):
    assert isinstance(for_loop.command, ForRangeCommand)

    new_loop_preds = set()
    command_preds = set()

    for pred in for_loop.predecessors:
        if pred.dest_edge_type == _CFGNode.DestEdgeType.FOR_ENTRY:
            # Remove for_loop from entry predecessor node,
            # it will point to the pseudo command instead.
            pred.node.successors = set(
                filter(lambda x: x.node is not for_loop, pred.node.successors)
            )

            p = copy(pred)
            p.dest_edge_type = _CFGNode.DestEdgeType.NORMAL
            command_preds.add(p)
        else:
            assert pred.dest_edge_type == _CFGNode.DestEdgeType.FOR_BODY_RETURN
            new_loop_preds.add(pred)

    # Since this node doesn't have a corresponding command in QiJob we give
    # it the same position as the for loop. We should never want to insert a
    # (offset store) command between this command and the for loop.
    pseudo_command_node = _CFGNode(
        pseudo_command,
        for_loop.instruction_index,
        for_loop.instruction_index,
        *command_preds,
    )

    cfg.nodes.add(pseudo_command_node)

    for_loop.predecessors = new_loop_preds
    for_loop.connect_predecessors(
        _CFGNode.Neighbor(
            pseudo_command_node,
            _CFGNode.SrcEdgeType.NORMAL,
            _CFGNode.DestEdgeType.FOR_ENTRY,
        )
    )


def _add_pseudo_store_instructions(
    cfg: _CFG,
    configuration: InsertMemoryParameterConfiguration,
):
    # For each cell
    # Check the body of every for loop
    # For different memory parameter values
    # If theres only a single value
    # make sure it's value doesn't use any variables that
    # are changed in the for loop body.
    # If so place such a store command before the for loop

    for_loops = [
        x
        for x in cfg.nodes
        if x.type == _CFGNode.Type.COMMAND and isinstance(x.command, ForRangeCommand)
    ]

    for for_loop in for_loops:
        collected_offsets = MemoryParameterVisitor(configuration)
        for_loop.command.accept(collected_offsets)

        for cell, mem_param in collected_offsets.mem_param_values.items():
            # Multiple different offsets for cell => Don't insert pseudo store command.
            if mem_param is Multiple:
                continue

            expression_invariant = ExpressionInvariantVisitor(mem_param)

            for_loop.command.accept(expression_invariant)

            if expression_invariant.result:
                # Insert pseudo command
                pseudo_command = MemStoreCommand(
                    cell, configuration.recording_module_address, mem_param
                )

                _insert_pseudo_command_before_for_loop(cfg, for_loop, pseudo_command)


class InsertMemoryParameterConfiguration:
    """Contains configuration to insert memory parameters for a certain QiCommand."""

    def __init__(
        self,
        recording_module_address: int,
        get_memory_param,
        if_memory_param_is_constant,
        anticipated_analysis=AnticipatedMemoryParameterAnalysis,
        available_analysis=AvailableMemoryParameterAnalysis,
    ):
        # The memory address to store a value of the memory parameter in the recording module.
        self.recording_module_address = recording_module_address

        # `get_memory_param` is a function which is given a QiCommand and determines if it uses the memory parameter.
        # If it doesn't IrrelevantCommand is returned.
        self.get_memory_param = get_memory_param

        # `if_memory_param_is_constant` is a function which is called when a memory parameter is only ever used with a constant value.
        # i.e. QiConstValue or QiCellProperty. In such cases we usually want to just initialize this value in the recording module
        # and don't insert any store instructions.
        self.if_memory_param_is_constant = if_memory_param_is_constant

        # The anticipated and available analysis can be modified if special behaviour is needed in certain cases.
        self.anticipated_analysis = anticipated_analysis
        self.available_analysis = available_analysis

    def compare_eq_memory_param(
        self, x: QiExpression | None, y: QiExpression | None
    ) -> bool:
        if isinstance(x, QiExpression) and isinstance(y, QiExpression):
            return x._equal_syntax(y)
        else:
            return x is None and y is None


def _insert_memory_parameter_store_commands(
    job: QiJob, configuration: InsertMemoryParameterConfiguration
):
    """
    Inserts MemStoreCommand commands into the QiJob needed for a memory parameter.

    'get_memory_param' is a function which extracts a memory parameter from a QiCellCommand, if it exists.
    (see '_get_recording_offset' for an example)

    'if_memory_param_is_constant' is called if the memory parameter of a cell is constant.
    This can be used to ellide store instructions altogether and simply initialize the value correctly.
    """

    cfg = _CFG(job)

    _add_pseudo_store_instructions(cfg, configuration)

    # Figures out what memory parameter values are anticipated before every node.
    reverse_dataflow(
        cfg,
        "anticipated",
        configuration.anticipated_analysis(configuration),
        CellValues(),
    )

    cfg.start.value_map["available"] = CellValues.default(
        job.cells, FlatLatticeValue.no_const()
    )

    # Figures out what memory parameters values are available after every node under the assumption that
    # anticipated values are loaded as early as possible.
    forward_dataflow(
        cfg,
        "available",
        configuration.available_analysis("anticipated"),
        CellValues(),
    )

    # Find locations in job.commands where to insert which MemStoreCommand commands.
    command_insertions: dict[int, tuple[list, list]] = {}

    for cell in job.cells:
        if _has_cell_constant_recording_offset(job, cell, configuration):
            # Anticipated value is the only (constant) value used for this memory parameter for this cell.
            mem_param = (
                cfg.start.value_map["anticipated"][cell] or FlatLatticeValue.undefined()
            )
            if mem_param.type == FlatLatticeValue.Type.VALUE:
                mem_param = mem_param.value
                assert isinstance(
                    mem_param, (_QiConstValue, QiCellProperty)
                ), f"mem_param is {mem_param}, but should be constant."
                configuration.if_memory_param_is_constant(cell, mem_param)
            else:
                # Mem param is never used
                pass
            continue

        for node in cfg.node_iterator():
            if cell not in node.value_map["anticipated"].values:
                continue

            antic_value = node.value_map["anticipated"][cell]

            for pred in node.predecessors:
                avail_value = pred.node.value_map["available"][cell]

                # Is a specific value anticipated and not currently available
                #   => load value to make it available
                if (
                    antic_value.type == FlatLatticeValue.Type.VALUE
                    and antic_value != avail_value
                ):
                    instruction_list, idx = _in_job_insert_command_here(node, pred)

                    command = MemStoreCommand(
                        cell, configuration.recording_module_address, antic_value.value
                    )
                    lists = command_insertions.get(
                        id(instruction_list), ([], instruction_list)
                    )
                    lists[0].append((idx, command))
                    command_insertions[id(instruction_list)] = lists

    # Insert collected MemStoreCommand commands in the descending index order.
    # Otherwise, we would invalidate higher indices.
    for _, data in command_insertions.items():
        insertions, instruction_list = data

        sorted_insertions = sorted(insertions, key=lambda x: x[0], reverse=True)

        for idx, command in sorted_insertions:
            instruction_list.insert(idx, command)


class _IrrelevantCommand(QiExpression):
    def accept(self, _visitor: QiExpressionVisitor):
        pass


IrrelevantCommand = _IrrelevantCommand()


RECORDING_OFFSET_ADDRESS = 0x8010 // 4
MANIPULATION_PULSE_FREQUENCY_ADDRESS = 0x18014 // 4
READOUT_PULSE_FREQUENCY_ADDRESS = 0x38100 // 4
MANIPULATION_PULSE_PHASE_ADDRESS = 0x18030 // 4
READOUT_PULSE_PHASE_ADDRESS = 0x38030 // 4
MANIPULATION_PULSE_AMPLITUDE_ADDRESS = 0x18010 // 4
READOUT_PULSE_AMPLITUDE_ADDRESS = 0x38010 // 4


class AnticipatedPulseVisitor(AnticipatedMemoryParameterAnalysis):
    def __init__(self, config, pulse_command, property):
        """pulse_command is either the type PlayCommand or PlayReadoutCommand."""
        super().__init__(config)

        self.pulse_command = pulse_command
        self.property = property

    def visit_cell_command(self, cell_cmd, cell_values: CellValues, node):
        if (
            isinstance(cell_cmd, self.pulse_command)
            and self.property(cell_cmd.pulse) is None
        ):
            # If a Play command has no frequency specified it should keep using the frequency that was previously set.
            # Therefore, we need to prevent store instructions for following commands to be placed before this instructions.
            # We do this, by setting the anticipated value to no_const, because we look for FlatLatticeValue.value of
            # the anticipated analysis when inserting store instructions.  (see _insert_memory_parameter_store_commands)
            out = copy(cell_values)
            out.set_cell_value(cell_cmd.cell, FlatLatticeValue.no_const())
            return out
        else:
            return super().visit_cell_command(cell_cmd, cell_values, node)


def _initialize_constant_manipulation_pulse_frequency(
    cell: QiCell, frequency: _QiConstValue | QiCellProperty
):
    assert frequency.type == QiType.FREQUENCY
    cell._initial_manip_freq = frequency.float_value


def _initialize_constant_readout_pulse_frequency(
    cell: QiCell, frequency: _QiConstValue | QiCellProperty
):
    assert frequency.type == QiType.FREQUENCY
    cell._initial_readout_freq = frequency.float_value


def _initialize_constant_manipulation_pulse_phase(
    cell: QiCell, phase: _QiConstValue | QiCellProperty
):
    assert phase.type == QiType.PHASE
    cell._initial_phase = phase.float_value


def _initialize_constant_readout_pulse_phase(
    cell: QiCell, phase: _QiConstValue | QiCellProperty
):
    assert phase.type == QiType.PHASE
    cell._initial_phase = phase.float_value


def _initialize_constant_manipulation_pulse_amplitude(
    cell: QiCell, amplitude: _QiConstValue | QiCellProperty
):
    assert amplitude.type == QiType.AMPLITUDE
    cell._initial_amplitude = amplitude.float_value


def _initialize_constant_readout_pulse_amplitude(
    cell: QiCell, amplitude: _QiConstValue | QiCellProperty
):
    assert amplitude.type == QiType.AMPLITUDE
    cell._initial_amplitude = amplitude.float_value


def _initialize_constant_recording_offset(cell, offset: _QiConstValue | QiCellProperty):
    assert offset.type == QiType.TIME
    cell._initial_rec_offset = offset.float_value


def _get_recording_offset(cmd) -> QiExpression | None:
    if isinstance(cmd, RecordingCommand):
        return cmd._offset
    elif isinstance(cmd, PlayReadoutCommand) and cmd.recording is not None:
        return cmd.recording._offset
    else:
        return IrrelevantCommand


def _get_manip_pulse_amplitude(cmd: QiCommand):
    if isinstance(cmd, PlayCommand) and isinstance(cmd.pulse.amplitude, QiExpression):
        return cmd.pulse.amplitude | (cmd.pulse.amplitude << 16)
    else:
        return IrrelevantCommand


def _get_readout_pulse_amplitude(cmd: QiCommand):
    if isinstance(cmd, PlayReadoutCommand) and isinstance(
        cmd.pulse.amplitude, QiExpression
    ):
        return cmd.pulse.amplitude | (cmd.pulse.amplitude << 16)
    else:
        return IrrelevantCommand


def _get_manip_pulse_property(cmd: QiCommand, property, transform=lambda x: x):
    if isinstance(cmd, PlayCommand) and isinstance(property(cmd.pulse), QiExpression):
        return transform(property(cmd.pulse))
    else:
        return IrrelevantCommand


def _get_readout_pulse_property(cmd: QiCommand, property, transform=lambda x: x):
    if isinstance(cmd, PlayReadoutCommand) and isinstance(
        property(cmd.pulse), QiExpression
    ):
        return transform(property(cmd.pulse))
    else:
        return IrrelevantCommand


def replace_variable_assignment_with_store_commands(job: QiJob):
    configs = (
        InsertMemoryParameterConfiguration(
            RECORDING_OFFSET_ADDRESS,
            _get_recording_offset,
            _initialize_constant_recording_offset,
        ),
        InsertMemoryParameterConfiguration(
            MANIPULATION_PULSE_FREQUENCY_ADDRESS,
            lambda cmd: _get_manip_pulse_property(cmd, lambda x: x.frequency),
            _initialize_constant_manipulation_pulse_frequency,
            anticipated_analysis=lambda config: AnticipatedPulseVisitor(
                config, PlayCommand, lambda pulse: pulse.frequency
            ),
        ),
        InsertMemoryParameterConfiguration(
            READOUT_PULSE_FREQUENCY_ADDRESS,
            lambda cmd: _get_readout_pulse_property(cmd, lambda x: x.frequency),
            _initialize_constant_readout_pulse_frequency,
            anticipated_analysis=lambda config: AnticipatedPulseVisitor(
                config, PlayReadoutCommand, lambda pulse: pulse.frequency
            ),
        ),
        InsertMemoryParameterConfiguration(
            MANIPULATION_PULSE_PHASE_ADDRESS,
            lambda cmd: _get_manip_pulse_property(cmd, lambda x: x.phase),
            _initialize_constant_manipulation_pulse_phase,
            anticipated_analysis=lambda config: AnticipatedPulseVisitor(
                config, PlayCommand, lambda pulse: pulse.phase
            ),
        ),
        InsertMemoryParameterConfiguration(
            READOUT_PULSE_PHASE_ADDRESS,
            lambda cmd: _get_readout_pulse_property(cmd, lambda x: x.phase),
            _initialize_constant_readout_pulse_phase,
            anticipated_analysis=lambda config: AnticipatedPulseVisitor(
                config, PlayReadoutCommand, lambda pulse: pulse.phase
            ),
        ),
        InsertMemoryParameterConfiguration(
            MANIPULATION_PULSE_AMPLITUDE_ADDRESS,
            _get_manip_pulse_amplitude,
            _initialize_constant_manipulation_pulse_amplitude,
            anticipated_analysis=lambda config: AnticipatedPulseVisitor(
                config, PlayCommand, lambda pulse: pulse.amplitude
            ),
        ),
        InsertMemoryParameterConfiguration(
            READOUT_PULSE_AMPLITUDE_ADDRESS,
            _get_readout_pulse_amplitude,
            _initialize_constant_readout_pulse_amplitude,
            anticipated_analysis=lambda config: AnticipatedPulseVisitor(
                config, PlayReadoutCommand, lambda pulse: pulse.amplitude
            ),
        ),
    )
    for config in configs:
        _insert_memory_parameter_store_commands(
            job,
            config,
        )
