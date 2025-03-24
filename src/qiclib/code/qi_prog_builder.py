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
This module contains the higher level parts of the code generation logic.
The entry point is in `build_program` which uses the `ProgramBuilderVisitor`.
`ProgramBuilderVisitor` recursively visits every `QiJob` command and generates its corresponding
RISC-V assembly sequentially.
"""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any

import qiclib.packages.utility as util
from qiclib.code.qi_command import (
    DigitalTriggerCommand,
    ForRangeCommand,
    PlayCommand,
    PlayFluxCommand,
    PlayReadoutCommand,
    RecordingCommand,
    RotateFrameCommand,
    WaitCommand,
)
from qiclib.code.qi_seq_instructions import SeqCellSync
from qiclib.code.qi_var_definitions import (
    QiCellProperty,
    QiExpression,
    QiType,
    _QiConstValue,
    _QiVariableBase,
)

from .qi_sequencer import Sequencer
from .qi_util import _get_for_range_end_value, _get_for_range_iterations
from .qi_visitor import (
    QiCMContainedCellVisitor,
    QiCmdVariableInspection,
    QiCommandVisitor,
    QiFindVarCmds,
)

if TYPE_CHECKING:
    from qiclib.code.qi_jobs import QiCell, QiCommand


class QiCmdExcludeVar(QiCommandVisitor):
    """Generates command list excluding cell- and variable-commands which implement variables from ignore_list.
    Generates new context managers with updated bodies"""

    def __init__(self, ignore_list: list[_QiVariableBase]) -> None:
        self.ignore_list = ignore_list
        self.commands: list[QiCommand] = []

    def visit_cell_command(self, cell_cmd):
        from .qi_command import AnyPlayCommand, PlayReadoutCommand, WaitCommand
        from .qi_var_definitions import _QiVariableBase

        for variable in self.ignore_list:
            if isinstance(cell_cmd, AnyPlayCommand) and cell_cmd.is_variable_relevant(
                variable
            ):
                if (
                    isinstance(cell_cmd, PlayReadoutCommand)
                    and cell_cmd.recording is not None
                ):
                    self.commands.append(cell_cmd.recording)
                return
            elif (
                isinstance(cell_cmd, WaitCommand)
                and isinstance(cell_cmd.length, _QiVariableBase)
                and cell_cmd.length.id == variable.id
            ):
                # If WaitCommand.length is QiCalc, append command
                return

        self.commands.append(cell_cmd)

    def visit_context_manager(self, context_manager):
        exclude_var = QiCmdExcludeVar(self.ignore_list)

        for command in context_manager.body:
            command.accept(exclude_var)

        if len(exclude_var.commands) == 0:
            return

        new_cm = copy.copy(context_manager)
        new_cm._relevant_cells.update(context_manager._relevant_cells)
        new_cm.body = exclude_var.commands
        self.commands.append(new_cm)

    def visit_if(self, if_cm):
        """Searches If/Else for commands containing variables defined in self.ignore_list.
        Creates new bodies and checks their size, so no empty ifs are returned."""
        exclude_if_body = QiCmdExcludeVar(self.ignore_list)

        for command in if_cm.body:
            command.accept(exclude_if_body)

        new_if = copy.copy(if_cm)
        new_if.body = exclude_if_body.commands

        if if_cm.is_followed_by_else():
            exclude_else_body = QiCmdExcludeVar(self.ignore_list)

            for command in if_cm._else_body:
                command.accept(exclude_else_body)

            if len(exclude_else_body.commands) > 0:
                new_if._else_body = exclude_else_body.commands

        if len(new_if.body) != 0 or len(new_if._else_body) != 0:
            self.commands.append(new_if)

    def visit_parallel(self, parallel_cm):
        new_parallel = copy.copy(parallel_cm)
        new_parallel.parallel = []
        for cmd_list in parallel_cm.entries:
            exclude_var = QiCmdExcludeVar(self.ignore_list)

            for cmd in cmd_list:
                cmd.accept(exclude_var)

            if len(exclude_var.commands) > 0:
                new_parallel.parallel.append(exclude_var.commands)

        if len(new_parallel.parallel) > 0:
            self.commands.append(new_parallel)

    def visit_variable_command(self, variable_cmd):
        for variable in self.ignore_list:
            if variable.id == variable_cmd.var.id:
                return

        self.commands.append(variable_cmd)

    def visit_sync_command(self, sync_cmd):
        self.commands.append(sync_cmd)

    def visit_mem_store_command(self, store_cmd):
        self.commands.append(store_cmd)


class QiCmdReplaceTriggerVar(QiCommandVisitor):
    """Generates command list, replacing trigger commands utilizing var with a trigger command of length 1.
    Generates new context managers with updated bodies."""

    def __init__(self, replace_var) -> None:
        self.replace_var = replace_var
        self.commands: list[QiCommand] = []

    def visit_cell_command(self, cell_cmd):
        from .qi_command import AnyPlayCommand, PlayReadoutCommand, RecordingCommand

        if isinstance(cell_cmd, AnyPlayCommand) and cell_cmd.is_variable_relevant(
            self.replace_var
        ):
            new_cmd = copy.copy(cell_cmd)
            new_cmd._relevant_cells.update(cell_cmd._relevant_cells)

            if isinstance(cell_cmd, PlayReadoutCommand) and isinstance(
                cell_cmd.recording, RecordingCommand
            ):
                new_cmd.recording = copy.copy(cell_cmd.recording)

            new_cmd.length = util.conv_cycles_to_time(
                1
            )  # set length to 1 for possible Parallel sequence generation
            new_cmd._var_single_cycle_trigger = True

            self.commands.append(new_cmd)
            return

        self.commands.append(cell_cmd)

    def visit_context_manager(self, context_manager):
        replace_var = QiCmdReplaceTriggerVar(self.replace_var)

        for command in context_manager.body:
            command.accept(replace_var)

        new_cm = copy.copy(context_manager)
        new_cm._relevant_cells.update(context_manager._relevant_cells)
        new_cm.body = replace_var.commands
        self.commands.append(new_cm)

    def visit_if(self, if_cm):
        """Searches If/Else for commands containing variable defined in self.replace_var."""
        replace_var_if = QiCmdReplaceTriggerVar(self.replace_var)

        for command in if_cm.body:
            command.accept(replace_var_if)

        new_if = copy.copy(if_cm)
        new_if.body = replace_var_if.commands

        if if_cm.is_followed_by_else():
            replace_var_else = QiCmdReplaceTriggerVar(self.replace_var)

            for command in if_cm._else_body:
                command.accept(replace_var_else)

            new_if._else_body = replace_var_else.commands

        self.commands.append(new_if)

    def visit_parallel(self, parallel_cm):
        new_parallel = copy.copy(parallel_cm)
        new_parallel.parallel = []
        for cmd_list in parallel_cm.parallel:
            replace_var = QiCmdReplaceTriggerVar(self.replace_var)

            for cmd in cmd_list:
                cmd.accept(replace_var)

            new_parallel.parallel.append(replace_var.commands)

        if len(new_parallel.parallel) > 0:
            self.commands.append(new_parallel)

    def visit_variable_command(self, variable_cmd):
        self.commands.append(variable_cmd)

    def visit_sync_command(self, sync_cmd):
        self.commands.append(sync_cmd)

    def visit_mem_store_command(self, store_cmd):
        self.commands.append(store_cmd)


class ProgramBuilderVisitor(QiCommandVisitor):
    def __init__(
        self,
        cell_seq: dict[QiCell, Sequencer],
        job_cell_to_digital_unit_cell_map: list[int],
    ) -> None:
        self.cell_seq = cell_seq
        self.if_depth: int = 0  # Used to check if currently processing commands inside If-Context-Manager
        self.for_range_end_val_list: list[
            tuple[_QiVariableBase, QiExpression | int]
        ] = []
        self.job_cell_to_digital_unit_cell_map = job_cell_to_digital_unit_cell_map

    def get_relevant_cells(self, cmd) -> list[QiCell]:
        """Generates a list of releveant cells from the cells registered to the builder and the command cmd"""
        return [cell for cell in self.cell_seq.keys() if cell in cmd._relevant_cells]

    def end_of_body(self, relevant_cells):
        """End of body --> stop potentially running pulses"""
        for cell in self.cell_seq.keys():
            if cell in relevant_cells:
                self.cell_seq[cell].end_of_command_body()

    def build_element_body(self, body, relevant_cells):
        """Function used to build commands from body.
        end_of_body() is called afterwards to end possibly ongoing pulses"""
        for cmd in body:
            cmd.accept(self)
        self.end_of_body(relevant_cells)

    def force_sync(self, relevant_cells, sync_point):
        """Forces the given cells to synchronize by inserting a SeqCellSync instruction."""

        digital_unit_cell_indices = [
            self.job_cell_to_digital_unit_cell_map[cell.cell_id]
            for cell in relevant_cells
        ]

        for cell in relevant_cells:
            cell_sequencer = self.cell_seq[cell]

            cell_sequencer.add_instruction_to_list(
                SeqCellSync(digital_unit_cell_indices)
            )

            cell_sequencer._prog_cycles.set_synchronized(sync_point)

    def cells_implicitly_synchronizable(self, cells):
        all_valid = all(self.cell_seq[cell].prog_cycles >= 0 for cell in cells)

        def all_share_syncpoint():
            return (
                len(
                    {self.cell_seq[cell]._prog_cycles.last_sync_point for cell in cells}
                )
                == 1
            )

        return all_valid and all_share_syncpoint()

    def sync_cells(self, relevant_cells: list[QiCell], sync_point):
        """
        Synchronizes given cells, implicitly if possible, explicitly otherwise.
        If implicit synch is possible, it evaluates the current programm lengths of sequencers
        of relevant_cells. If valid prog_lengths are found adds Wait commands at sequencers
        with shorter programs.
        """

        if len(relevant_cells) <= 1:
            return

        if not self.cells_implicitly_synchronizable(relevant_cells):
            self.force_sync(relevant_cells, sync_point)

        else:
            longest_prog_len = max(
                self.cell_seq[cell].prog_cycles for cell in relevant_cells
            )

            for cell in relevant_cells:
                if self.cell_seq[cell].prog_cycles < longest_prog_len:
                    self.cell_seq[cell]._wait_cycles(
                        longest_prog_len - self.cell_seq[cell].prog_cycles
                    )

    def _unroll_loop_0(self, for_range: ForRangeCommand, static_unroll=False):
        """Function used for unrolling ForRange with variable value 0.
        A new program body is built from ForRange.body excluding wait and pulse commands using solely ForRange.var.
        The new program body is then added to the sequencer."""
        exclude_var = QiCmdExcludeVar([for_range.var])

        for cmd in for_range.body:
            cmd.accept(exclude_var)

        if len(exclude_var.commands) == 0:
            return

        relevant_cells = self.get_relevant_cells(for_range)

        for cell in relevant_cells:
            if static_unroll:
                # set register value to 0 in case it had different values before --> important for possible use in conditions
                self.cell_seq[cell].set_variable_value(for_range.var, 0)
            # register one cycle of ForRange, actual start/end/step values not relevant
            self.cell_seq[cell].register_for_range(
                for_range.var, 0, for_range.step.value, for_range.step.value
            )

        self.build_element_body(exclude_var.commands, for_range._relevant_cells)

        for cell in relevant_cells:
            self.cell_seq[cell].exit_for_range()

    def _unroll_loop_1(self, for_range):
        """Function used for unrolling ForRange with variable value 1.
        A new program body is built from ForRange.body, replacing pulse commands using ForRange.var with trigger commands with length 1.
        The new program body is then added to the sequencer."""
        replace_var = QiCmdReplaceTriggerVar(for_range.var)

        for cmd in for_range.body:
            cmd.accept(replace_var)

        relevant_cells = self.get_relevant_cells(for_range)

        for cell in relevant_cells:
            self.cell_seq[cell].register_for_range(
                for_range.var, 1, 1 + for_range.step.value, for_range.step.value
            )  # register one cycle of ForRange, actual start/end/step values not relevant

        self.build_element_body(replace_var.commands, for_range._relevant_cells)

        for cell in relevant_cells:
            self.cell_seq[cell].exit_for_range()

    def visit_cell_command(self, cell_cmd: QiCommand):
        relevant_cells = self.get_relevant_cells(cell_cmd)

        for cell in relevant_cells:
            if isinstance(cell_cmd, WaitCommand):
                # Ignore Wait command if it is of length less than a cycle.
                length = cell_cmd.length
                if (
                    isinstance(length, (int, float))
                    and util.conv_time_to_cycles(length) == 0
                ):
                    return

                self.cell_seq[cell].add_wait_cmd(cell_cmd)
            elif isinstance(cell_cmd, (PlayCommand, RotateFrameCommand)):
                self.cell_seq[cell].add_trigger_cmd(
                    manipulation=cell_cmd,
                    var_single_cycle=cell_cmd._var_single_cycle_trigger,
                )
            elif isinstance(cell_cmd, PlayReadoutCommand):
                # cell_cmd.combine_recording is either None or RecordingCommand
                self.cell_seq[cell].add_trigger_cmd(
                    readout=cell_cmd,
                    recording=cell_cmd.recording,
                    var_single_cycle=cell_cmd._var_single_cycle_trigger,
                )
            elif isinstance(cell_cmd, PlayFluxCommand):
                if cell_cmd.coupler.coupling_index == 0:
                    self.cell_seq[cell].add_trigger_cmd(coupling0=cell_cmd)
                elif cell_cmd.coupler.coupling_index == 1:
                    self.cell_seq[cell].add_trigger_cmd(coupling1=cell_cmd)
                else:
                    raise RuntimeError(
                        f"Illegal coupling index {cell_cmd.coupler.coupling_index} (must be 0 or 1)"
                    )
            elif isinstance(cell_cmd, RecordingCommand):
                self.cell_seq[cell].add_trigger_cmd(recording=cell_cmd)
            elif isinstance(cell_cmd, DigitalTriggerCommand):
                self.cell_seq[cell].add_trigger_cmd(digital=cell_cmd)

    def visit_context_manager(self, context_manager):
        """Context managers are evaluated in respective visit"""

    def visit_if(self, if_cm):
        """Visits If command and builds sequencer instructions.
        Tries synchronizing if multiple cells are used."""
        from .qi_sequencer import _ProgramCycles

        jump_over_if = {}
        program_counters = {}

        relevant_cells = self.get_relevant_cells(if_cm)

        self.sync_cells(relevant_cells, _ProgramCycles.SyncPoint(if_cm))

        self.if_depth += 1

        for cell in relevant_cells:
            jump_over_if[cell] = self.cell_seq[cell].add_if_condition(if_cm.condition)

            # conditional branching makes implicit sync by wait impossible
            self.cell_seq[cell]._prog_cycles.valid = False

            program_counters[cell] = self.cell_seq[cell].get_prog_size() - 1

        self.build_element_body(if_cm.body, if_cm._relevant_cells)

        if if_cm.is_followed_by_else():
            jump_over_else = {}
            for cell in relevant_cells:
                # add jump after if-body to jump over else-body
                jump_over_else[cell] = self.cell_seq[cell].add_jump()
                jump_over_if[cell].set_jump_value(
                    self.cell_seq[cell].get_prog_size() - program_counters[cell]
                )

                program_counters[cell] = self.cell_seq[cell].get_prog_size() - 1

            self.build_element_body(if_cm._else_body, if_cm._relevant_cells)

            for cell in relevant_cells:
                jump_over_else[cell].jump_val = (
                    self.cell_seq[cell].get_prog_size() - program_counters[cell]
                )

        else:
            for cell in relevant_cells:
                jump_over_if[cell].set_jump_value(
                    self.cell_seq[cell].get_prog_size() - program_counters[cell]
                )

        self.if_depth -= 1

    def visit_parallel(self, parallel_cm):
        """Visits Parallel command and builds sequencer command.
        Searches for manipulation, readout and recording pulses inside body and summarizes them in one trigger command.
        """
        from .qi_command import (
            PlayCommand,
            PlayReadoutCommand,
            RecordingCommand,
            RotateFrameCommand,
            WaitCommand,
        )
        from .qi_sequencer import Sequencer, _ProgramCycles

        relevant_cells = self.get_relevant_cells(parallel_cm)

        self.sync_cells(relevant_cells, _ProgramCycles.SyncPoint(parallel_cm))

        for cell in relevant_cells:
            time_slots = parallel_cm._generate_command_body(cell, self.cell_seq[cell])

            for time_slot in time_slots:
                if isinstance(time_slot.cmd_tuples[0].cmd, WaitCommand):
                    self.cell_seq[cell].add_wait_cmd(
                        WaitCommand(cell, time_slot.duration)
                    )
                else:
                    manipulation = None
                    readout = None
                    recording = None

                    for cmd_tuple in time_slot.cmd_tuples:
                        trigger_cmd = copy.copy(cmd_tuple.cmd)
                        trigger_cmd.length = time_slot.duration

                        if isinstance(cmd_tuple.cmd, (PlayCommand, RotateFrameCommand)):
                            if cmd_tuple.choke_cmd is True:
                                trigger_cmd.trigger_index = Sequencer.CHOKE_PULSE_INDEX

                            manipulation = trigger_cmd

                        elif isinstance(cmd_tuple.cmd, PlayReadoutCommand):
                            if cmd_tuple.choke_cmd is True:
                                trigger_cmd.trigger_index = Sequencer.CHOKE_PULSE_INDEX
                                trigger_cmd.recording = None

                            readout = trigger_cmd
                            recording = trigger_cmd.recording

                        elif isinstance(cmd_tuple.cmd, RecordingCommand):
                            recording = trigger_cmd

                    self.cell_seq[cell].add_trigger_cmd(
                        manipulation=manipulation,
                        readout=readout,
                        recording=recording,
                        recording_delay=False,
                    )

    def try_sync_for_range(self, for_range, start_val: QiExpression):
        """If multiple cells are used inside a ForRange context manager the program tries to sync cells before restarting the loop.
        If the ForRange does not use its variable for Pulses or waits a normal sync is used.
        """
        from .qi_command import WaitCommand
        from .qi_sequencer import _ProgramCycles
        from .qi_var_definitions import _QiVariableBase

        relevant_cells = self.get_relevant_cells(for_range)

        if len(relevant_cells) == 1:
            return

        find_var_visitor = QiFindVarCmds(for_range.var)
        for cmd in for_range.body:
            cmd.accept(find_var_visitor)

        if len(find_var_visitor.found_cmds) == 0:
            self.sync_cells(
                relevant_cells,
                _ProgramCycles.SyncPoint(
                    for_range, _ProgramCycles.SyncPointType.AFTER_FOR_RANGE_ITERATION
                ),
            )
            return

        if find_var_visitor.calc_in_wait:
            self.force_sync(
                relevant_cells,
                _ProgramCycles.SyncPoint(
                    for_range, _ProgramCycles.SyncPointType.AFTER_FOR_RANGE_ITERATION
                ),
            )
            return

        if isinstance(start_val, _QiVariableBase) or start_val is None:
            self.force_sync(
                relevant_cells,
                _ProgramCycles.SyncPoint(
                    for_range, _ProgramCycles.SyncPointType.AFTER_FOR_RANGE_ITERATION
                ),
            )
            return

        if isinstance(start_val, (_QiConstValue, QiCellProperty)):
            start_val = start_val.value

        prog_lengths: list[int] = []
        wait_cmds = {}
        for cell in relevant_cells:
            wait_cmds[cell] = [
                cmd
                for cmd in find_var_visitor.found_cmds
                if cell in cmd._relevant_cells
            ]
            prog_lengths.append(
                self.cell_seq[cell].prog_cycles - (start_val * len(wait_cmds[cell]))
            )  # subtract already added variable waits

        # negative prog_lengths imply that a self.cell_seq[cell].prog_cycles were invalid.
        if any(x < 0 for x in prog_lengths):
            self.force_sync(
                relevant_cells,
                _ProgramCycles.SyncPoint(
                    for_range, _ProgramCycles.SyncPointType.AFTER_FOR_RANGE_ITERATION
                ),
            )
            return

        longest = max(prog_lengths)

        cycles_without_waits = self.cell_seq[cell].prog_cycles - (
            start_val * len(wait_cmds[cell])
        )

        for cell in relevant_cells:
            if cycles_without_waits < longest:
                # sync non variable cycles
                self.cell_seq[cell]._wait_cycles(longest - cycles_without_waits)

            most_waits = 0
            for cell in relevant_cells:
                most_waits = max(len(wait_cmds[cell]), most_waits)

            waits = len(wait_cmds[cell])
            for _ in range(waits, most_waits):
                self.cell_seq[cell].add_wait_cmd(
                    WaitCommand(None, for_range.var)
                )  # add missing waits, no multiplication to avoid overflows

    def update_cycles_after_for_range(self, for_range, start_val, program_cycles_start):
        """First iteration of loop was already added to sequencer; so every variable wait already used start_val cycles.
        If variable start/end are used, sets _prog_cycles to False."""
        from .qi_command import AnyPlayCommand, WaitCommand
        from .qi_sequencer import _ProgramCycles
        from .qi_var_definitions import _QiVariableBase

        relevant_cells = self.get_relevant_cells(for_range)

        end_val = self.get_for_range_val(for_range.end, relevant_cells)

        if (
            isinstance(for_range.start, _QiVariableBase)
            or isinstance(for_range.end, _QiVariableBase)
            or start_val is None
            or end_val is None
        ):
            for cell in relevant_cells:
                self.cell_seq[cell]._prog_cycles.valid = False
            return

        if isinstance(start_val, (_QiConstValue, QiCellProperty)):
            start_val = start_val.value

        assert isinstance(start_val, (int, _QiVariableBase))

        find_var_visitor = QiFindVarCmds(for_range.var)
        for cmd in for_range.body:
            cmd.accept(find_var_visitor)

        wait_cmds = {}
        play_cmds = {}
        for cell in relevant_cells:
            wait_cmds[cell] = [
                cmd
                for cmd in find_var_visitor.found_cmds
                if cell in cmd._relevant_cells and isinstance(cmd, WaitCommand)
            ]
            play_cmds[cell] = [
                cmd
                for cmd in find_var_visitor.found_cmds
                if cell in cmd._relevant_cells and isinstance(cmd, AnyPlayCommand)
            ]

        for cell in relevant_cells:
            if self.cell_seq[cell].prog_cycles is _ProgramCycles.INVALID:
                continue

            if len(find_var_visitor.found_cmds) == 0:
                self.cell_seq[cell].prog_cycles += (
                    (self.cell_seq[cell].prog_cycles - program_cycles_start[cell])
                    * (
                        _get_for_range_iterations(
                            start_val, end_val, for_range.step.value
                        )
                        - 1
                    )
                    + self.cell_seq[cell].JUMP_EXECUTION_CYCLES
                )  # last execution of branch, jumping over loop body, adds number of Jump Cycles
            elif find_var_visitor.calc_in_wait is False:
                # calculate cycles for not variable cmds
                new_cycles = (
                    self.cell_seq[cell].prog_cycles
                    - (
                        start_val * (len(wait_cmds[cell]) + len(play_cmds[cell]))
                    )  # subtract first wait/play
                    - len(
                        play_cmds[cell]
                    )  # play generates trigger and wait so subtract 1 cycle per trigger
                    - program_cycles_start[cell]
                ) * (
                    _get_for_range_iterations(start_val, end_val, for_range.step) - 1
                ) + self.cell_seq[
                    cell
                ].JUMP_EXECUTION_CYCLES  # cycles for each loop excluding variable waits

                # calculate cycles for ForRange, first loop was already added to sequencer, so skip start_val
                for val in range(
                    start_val + for_range.step.value, end_val, for_range.step.value
                ):
                    new_cycles += val * (
                        len(wait_cmds[cell]) + len(play_cmds[cell])
                    ) + len(
                        play_cmds[cell]
                    )  # adding variable waits times val to cycles

                self.cell_seq[cell].prog_cycles += new_cycles  # update cycles
            else:
                # invalidate cycles, variable is used inside calculation, TODO:evaluate calculation to get the right amount of cycles
                self.cell_seq[cell]._prog_cycles.valid = False

    def get_var_value_on_seq(self, var, cells):
        """Checks variable values at Sequencers of :python:`cells`. If value is the same for each Sequencer, return it, else return None."""
        val = set()
        for cell in cells:
            val.add(self.cell_seq[cell].get_var_value(var))

        if len(val) > 1 or None in val:
            return None
        else:
            return val.pop()

    def get_for_range_val(self, val: QiExpression, cells) -> int | float | None:
        """Returns the value of `val`, depending on the instance and the relevant cells.
        If `val` is _QiVariableBase, it is checked if the value is the same on each cell's sequencer, else None is returned
        """
        from .qi_var_definitions import _QiVariableBase

        if isinstance(val, _QiVariableBase):
            return self.get_var_value_on_seq(val, cells)
        else:
            assert isinstance(val, (_QiConstValue, QiCellProperty))
            return val.value

    def _is_end_val_rising(self, end, end_val):
        """This function is used to determine if any loops are left to implement. It checks if `end` is a QiVariable, if so,
        it is checked if there is an outer ForRange currently being implemented, by trying to get a tuple from self.for_range_end_val_list.
        When a tuple is received, it is checked, if the current end variable is the loop variable
        of the outer loop. If so end val will have a higher value and therefore do not skip after unrolling.
        """
        from .qi_var_definitions import _QiVariableBase

        if isinstance(end, _QiVariableBase):
            for var_end_tuple in self.for_range_end_val_list:
                if var_end_tuple[0].id == end.id or end_val is None:
                    return True
        return False

    def _get_end_value_to_register(self, end):
        from .qi_var_definitions import _QiVariableBase

        if isinstance(end, _QiVariableBase):
            for var_end_tuple in self.for_range_end_val_list:
                if var_end_tuple[0].id == end.id:
                    return var_end_tuple[1]
        return end

    def no_loops_left(
        self, start: int, end: QiExpression, step: QiExpression, cells
    ) -> bool:
        """Checks if there are loops left to implement. If end is a QiVariable it needs to be checked if it is subject to change from an outer loop.
        If so, there will be loops to implement"""
        end_val = self.get_for_range_val(end, cells)

        if self._is_end_val_rising(end, end_val):
            return False

        if start is None or end_val is None:
            return False

        if _get_for_range_iterations(start, end_val, step.value) == 0:
            return True

        return False

    def implement_for_range(
        self,
        for_range,
        start: QiExpression | int,
        end: QiExpression | int,
        relevant_cells,
        var_unroll_last=False,
    ):
        """Implements ForRange. Tries to sync relevant cells, before loop is entered. Sync also is tried after body of loop, before restarting
        loop. Also tries to update program cycles after execution. While building the body self.for_range_end_val_list is added to,
        in order to communicate the used variables to inner ForRanges"""
        from .qi_sequencer import _ProgramCycles
        from .qi_var_definitions import QiOp, _QiVariableBase

        assert isinstance(start, (QiExpression, int))

        branch_instr_loop = {}
        program_counters = {}
        program_cycles = {}
        end_val_reg = {}

        self.sync_cells(
            relevant_cells,
            _ProgramCycles.SyncPoint(
                for_range, _ProgramCycles.SyncPointType.BEFORE_FOR_RANGE
            ),
        )

        for cell in relevant_cells:
            self.cell_seq[cell].register_for_range(
                for_range.var,
                start,
                self._get_end_value_to_register(end),
                for_range.step,
            )

            if isinstance(end, _QiVariableBase):
                end_val_reg[cell] = self.cell_seq[cell].get_var_register(end)
            elif isinstance(end, (_QiConstValue, QiCellProperty)):
                end_val_reg[cell] = self.cell_seq[cell].immediate_to_register(end.value)
            elif isinstance(end, int):
                end_val_reg[cell] = self.cell_seq[cell].immediate_to_register(end)
            else:
                raise AssertionError("Unreacheable")

            if isinstance(start, (_QiConstValue, QiCellProperty)):
                start = start.value

            branch_instr_loop[cell] = self.cell_seq[cell].add_for_range_head(
                for_range.var,
                start,
                end_val_reg[cell],
                for_range.step,
            )  # loads val to reg and adds branch cmd

            program_cycles[cell] = (
                self.cell_seq[cell].prog_cycles - 1
            )  # save cycles before loop; -1 to include branch

            program_counters[cell] = (
                self.cell_seq[cell].get_prog_size() - 1
            )  # prog_size - 1 == current program counter

        # create tuple of (for_range.var, for_range_cm.end); indicator for inner loops that they are inside another loop
        self.for_range_end_val_list.append((for_range.var, end))

        self.build_element_body(for_range.body.copy(), relevant_cells)

        self.for_range_end_val_list.pop()

        self.try_sync_for_range(for_range, start)

        for cell in relevant_cells:
            # add step to variable; TODO: check size of step before entering loop -> if it needs Register then prepare it -> saves one command in loop
            self.cell_seq[cell].add_calculation(
                val1=self.cell_seq[cell].get_var_register(for_range.var),
                operator=QiOp.PLUS,
                val2=for_range.step.value,
                dst_reg=self.cell_seq[cell].get_var_register(for_range.var),
            )

            if var_unroll_last is True:
                # var_unroll_last is True when step <0 and variable times are used; check after loop if var == 1 if so jump out of loop
                # and move into the following unroll
                branch_over_jump = self.cell_seq[cell].add_if_condition(
                    for_range.var == util.conv_cycles_to_time(1)
                )
                branch_over_jump.immediate = 2

            # add jump back to branch_cmd
            self.cell_seq[cell].add_jump(
                program_counters[cell] - self.cell_seq[cell].get_prog_size()
            )

            # set jump value at branch_instr after loop was added to prog list
            branch_instr_loop[cell].immediate = (
                self.cell_seq[cell].get_prog_size() - program_counters[cell]
            )

            # update sequencer cycles and register value of for_range_cm.var at sequencer
            var_reg = self.cell_seq[cell].get_var_register(for_range.var)
            var_reg.value = end_val_reg[cell].value

            if not isinstance(end, _QiVariableBase):
                self.cell_seq[cell].release_register(end_val_reg[cell])

            # cycles were only added for one loop, to generate the real number of cycles, number of loops need to be accounted
            self.update_cycles_after_for_range(for_range, start, program_cycles)

            self.cell_seq[cell].exit_for_range()

    def implement_static_time_for_range(self, for_range, relevant_cells):
        """Is used when using QiTimeVariable and static start values and static end values.
        If necessary, unrolled loops are added sequentially"""
        from .qi_sequencer import _ProgramCycles
        from .qi_var_definitions import _QiVariableBase

        start_val = for_range.start
        end_val = _get_for_range_end_value(
            start_val.value, for_range.end.value, for_range.step.value
        )

        if self.no_loops_left(
            start_val.value, for_range.end, for_range.step, relevant_cells
        ):
            return

        # Unroll loop when TimeVariable == 0, exclude Pulses and Waits with length == element.var

        start_val = start_val.value

        if start_val == 0:
            self.sync_cells(
                relevant_cells,
                _ProgramCycles.SyncPoint(
                    for_range, _ProgramCycles.SyncPointType.LOOP_UNROLL0
                ),
            )
            self._unroll_loop_0(for_range, static_unroll=True)

            start_val += for_range.step.value

            if self.no_loops_left(
                start_val, for_range.end, for_range.step, relevant_cells
            ):
                return

        # Unroll loop when TimeVariable == 1 cycle, only Trigger Pulses with length == 1 and no subsequent wait_reg_command
        if start_val == 1:
            self.sync_cells(
                relevant_cells,
                _ProgramCycles.SyncPoint(
                    for_range, _ProgramCycles.SyncPointType.LOOP_UNROLL1
                ),
            )
            for cell in relevant_cells:
                self.cell_seq[cell].set_variable_value(for_range.var, 1)

            self._unroll_loop_1(for_range)

            start_val += for_range.step.value

            if self.no_loops_left(
                start_val, for_range.end, for_range.step, relevant_cells
            ):
                return

        unroll_last = False

        if for_range.step.value < 0:
            unroll_last = end_val - for_range.step.value == 1

        end_val = end_val - for_range.step.value if unroll_last else end_val

        self.implement_for_range(
            for_range,
            start_val,
            for_range.end if isinstance(for_range.end, _QiVariableBase) else end_val,
            relevant_cells,
        )

        # Unroll last loop when TimeVariable == 1
        if unroll_last:
            self._unroll_loop_1(for_range)

    def implement_variable_time_for_range(self, for_range, relevant_cells):
        """Is used for ForRanges with QiTimeVariable,positive step size and variable start value.
        The variable start value is first loaded to the loop variable. Afterwards conditions are added to check if the
        loop variables value is 0, 1 or >1 and the respective loops are executed and loop var is increased.
        """
        from .qi_sequencer import _ProgramCycles
        from .qi_var_definitions import QiOp

        branch_instr = {}
        program_counters = {}

        self.sync_cells(
            relevant_cells,
            _ProgramCycles.SyncPoint(
                for_range, _ProgramCycles.SyncPointType.LOOP_UNROLL0
            ),
        )

        for cell in relevant_cells:
            self.cell_seq[cell].set_variable_value(for_range.var, for_range.start)

            branch_instr[cell] = self.cell_seq[cell].add_if_condition(
                for_range.var == 0
            )
            # prog_size - 1 == current program counter
            program_counters[cell] = self.cell_seq[cell].get_prog_size() - 1

        self._unroll_loop_0(for_range)

        self.sync_cells(
            relevant_cells,
            _ProgramCycles.SyncPoint(
                for_range, _ProgramCycles.SyncPointType.LOOP_UNROLL1
            ),
        )

        for cell in relevant_cells:
            self.cell_seq[cell].add_calculation(
                val1=self.cell_seq[cell].get_var_register(for_range.var),
                operator=QiOp.PLUS,
                val2=for_range.step.value,
                dst_reg=self.cell_seq[cell].get_var_register(for_range.var),
            )

            # set jump value at branch_instr after loop was added to prog list
            branch_instr[cell].immediate = (
                self.cell_seq[cell].get_prog_size() - program_counters[cell]
            )

            branch_instr[cell] = self.cell_seq[cell].add_if_condition(
                for_range.var == util.conv_cycles_to_time(1)
            )
            # prog_size - 1 == current program counter
            program_counters[cell] = self.cell_seq[cell].get_prog_size() - 1

        self._unroll_loop_1(for_range)

        for cell in relevant_cells:
            self.cell_seq[cell].add_calculation(
                val1=self.cell_seq[cell].get_var_register(for_range.var),
                operator=QiOp.PLUS,
                val2=for_range.step.value,
                dst_reg=self.cell_seq[cell].get_var_register(for_range.var),
            )

            # set jump value at branch_instr after loop was added to prog list
            branch_instr[cell].immediate = (
                self.cell_seq[cell].get_prog_size() - program_counters[cell]
            )

            # add normal loop
            branch_instr[cell] = self.cell_seq[cell].add_if_condition(
                for_range.var > util.conv_cycles_to_time(1)
            )
            # prog_size - 1 == current program counter
            program_counters[cell] = self.cell_seq[cell].get_prog_size() - 1

        self.implement_for_range(
            for_range, for_range.var, for_range.end, relevant_cells
        )

        for cell in relevant_cells:
            # set jump value at branch_instr after loop was added to prog list
            branch_instr[cell].immediate = (
                self.cell_seq[cell].get_prog_size() - program_counters[cell]
            )

    def implement_decr_variable_time_for_range(self, for_range, relevant_cells):
        """Is used for ForRanges with a negative stepsize and variable end/start values.
        Before the Jump instruction which jumps back to the evaluation of the ForRange Parameters,
        a condition is added checking the loop variable if it has value 1, then no jump is executed,
        but the following unrolled loop is executed."""
        from .qi_sequencer import _ProgramCycles

        branch_instr = {}
        program_counters = {}
        branch_instr_2 = {}
        program_counters_2 = {}

        for cell in relevant_cells:
            self.cell_seq[cell].set_variable_value(for_range.var, for_range.start)

        for cell in relevant_cells:
            branch_instr[cell] = self.cell_seq[cell].add_if_condition(
                for_range.var > util.conv_cycles_to_time(1)
            )
            # prog_size - 1 == current program counter
            program_counters[cell] = self.cell_seq[cell].get_prog_size() - 1

        self.implement_for_range(
            for_range, for_range.start, for_range.end, relevant_cells, True
        )

        self.sync_cells(
            relevant_cells,
            _ProgramCycles.SyncPoint(
                for_range, _ProgramCycles.SyncPointType.LOOP_UNROLL1
            ),
        )

        for cell in relevant_cells:
            # set jump value at branch_instr after loop was added to prog list
            branch_instr[cell].immediate = (
                self.cell_seq[cell].get_prog_size() - program_counters[cell]
            )

            # unroll last loop; check if var == 1 and var > end
            branch_instr[cell] = self.cell_seq[cell].add_if_condition(
                for_range.var == util.conv_cycles_to_time(1)
            )
            # prog_size - 1 == current program counter
            program_counters[cell] = self.cell_seq[cell].get_prog_size() - 1

            branch_instr_2[cell] = self.cell_seq[cell].add_if_condition(
                for_range.var > for_range.end
            )

            # prog_size - 1 == current program counter
            program_counters_2[cell] = self.cell_seq[cell].get_prog_size() - 1

        self._unroll_loop_1(for_range)

        for cell in relevant_cells:
            # set jump value at branch_instr after loop was added to prog list
            branch_instr[cell].immediate = (
                self.cell_seq[cell].get_prog_size() - program_counters[cell]
            )

            # set jump value at branch_instr after loop was added to prog list
            branch_instr_2[cell].immediate = (
                self.cell_seq[cell].get_prog_size() - program_counters_2[cell]
            )

    def visit_for_range(self, for_range_cm):
        """Visits ForRange command and builds sequencer commands.
        Separates the ForRange into different cases depending on the input values.
        Simplest case is the use of QiVariables as loop variable;
        When using QiTimeVariables loops need to be unrolled depending on start and end values and if those are variables themselves.
        """
        from qiclib.code.qi_var_definitions import _QiVariableBase

        # Originally, before the switch to a unified QiExpression system, we used pythons dynamic types
        # and passed a variety of types to represent variables, constants, expressions which didn't really
        # relate to one and another.
        # This lead to a bunch of `isinstance` expressions (which is still true, but not as bad) and was
        # generally not that great to read.
        # I'm saying all this because the remnants of this system can still be seen in this code for the
        # code generation of ForRanges, where some function will take _QiConstValue and int values which
        # might lead to confusion. Ideally, we would only accept _QiConstValue but when refactoring the
        # code this wasn't that easy todo.

        relevant_cells = self.get_relevant_cells(for_range_cm)

        if for_range_cm.var.type in {QiType.NORMAL, QiType.PHASE, QiType.AMPLITUDE}:
            self.implement_for_range(
                for_range_cm,
                for_range_cm.start,
                for_range_cm.end,
                relevant_cells,
            )
        elif for_range_cm.var.type in (QiType.TIME, QiType.FREQUENCY):
            if isinstance(for_range_cm.start, _QiVariableBase) and (
                for_range_cm.step.value > 0
            ):
                self.implement_variable_time_for_range(for_range_cm, relevant_cells)
            elif (
                isinstance(for_range_cm.start, _QiVariableBase)
                or isinstance(for_range_cm.end, _QiVariableBase)
            ) and (for_range_cm.step.value < 0):
                self.implement_decr_variable_time_for_range(
                    for_range_cm, relevant_cells
                )
            else:
                self.implement_static_time_for_range(for_range_cm, relevant_cells)
        else:
            # The only other type is QiType.STATE which can not be used in ForRanges.
            raise AssertionError(
                f"Unexpected type {for_range_cm.var.type} used in for loop."
            )

    def visit_variable_command(self, variable_cmd):
        pass

    def visit_assign_command(self, assign_cmd):
        """Evaluates Assign command.
        If Assign.val is _QiConst(Int|Float), immediate command is added to sequencer.
        If Assign.val is _QiCalcBase, QiCalc is evaluated and its final register is used to write to Assign.var; After that the register is released again.
        If Assign.val is _QiVariableBase, the variable's register is used to write to Assign.var
        """
        from .qi_jobs import _QiVariableBase
        from .qi_var_definitions import _QiCalcBase

        relevant_cells = self.get_relevant_cells(assign_cmd)

        for cell in relevant_cells:
            dst_reg = self.cell_seq[cell].get_var_register(assign_cmd.var)

            if isinstance(assign_cmd.value, _QiConstValue):
                self.cell_seq[cell].immediate_to_register(
                    val=assign_cmd.value.value, dst_reg=dst_reg
                )
                dst_reg.valid = self.if_depth == 0
                continue
            elif isinstance(assign_cmd.value, _QiCalcBase):
                register = self.cell_seq[cell].add_qi_calc(assign_cmd.value)
            elif isinstance(assign_cmd.value, _QiVariableBase):
                register = self.cell_seq[cell].get_var_register(assign_cmd.value)
            else:
                raise TypeError(assign_cmd.value)

            self.cell_seq[cell].add_mov_command(dst_reg=dst_reg, src_reg=register)

            dst_reg.valid = register.valid and self.if_depth == 0

            if isinstance(assign_cmd.value, _QiCalcBase):
                self.cell_seq[cell].release_register(register)

    def visit_declare_command(self, declare_cmd):
        """Adds variable to sequencer and reserves register"""
        relevant_cells = self.get_relevant_cells(declare_cmd)
        for cell in relevant_cells:
            self.cell_seq[cell].add_variable(declare_cmd.var)

    def visit_sync_command(self, sync_cmd):
        from .qi_sequencer import _ProgramCycles

        # If sync command contains no cells, it should sync all cells.
        if len(sync_cmd._relevant_cells) == 0:
            sync_cmd._relevant_cells.update(self.cell_seq.keys())

        self.sync_cells(sync_cmd._relevant_cells, _ProgramCycles.SyncPoint(sync_cmd))

    def visit_asm_command(self, asm_cmd):
        relevant_cells = self.get_relevant_cells(asm_cmd)
        for cell in relevant_cells:
            self.cell_seq[cell].add_instruction_to_list(
                asm_cmd.asm_instruction, asm_cmd.cycles
            )

    def visit_mem_store_command(self, store_cmd):
        relevant_cells = self.get_relevant_cells(store_cmd)
        for cell in relevant_cells:
            self.cell_seq[cell].add_store_cmd(
                store_cmd.value, None, offset=store_cmd.addr
            )


def _assign_cell_to_context_manager(commands: list[QiCommand]):
    contained_cells_visitor = QiCMContainedCellVisitor()
    for command in commands:
        command.accept(contained_cells_visitor)


def _assign_variables_to_cell(commands: list[QiCommand]):
    cell_to_variable_visitor = QiCmdVariableInspection()
    for command in reversed(commands):
        command.accept(cell_to_variable_visitor)

    # run again, to ensure all Assignment statements are considered as well
    _assign_cell_to_context_manager(commands)


def build_program(
    cell_list: list[QiCell],
    cell_map: list[int],
    command_list: list[QiCommand],
    skip_nco_sync: bool = False,
    nco_sync_length: float = 0,
) -> dict[QiCell, Sequencer]:
    cell_seq_dict = {}
    result_boxes = []

    for cell, index in zip(cell_list, cell_map):
        cell_seq_dict[cell] = Sequencer(cell_index=index)

        for resultbox in cell._result_container.values():
            result_boxes.append(resultbox)

    for cell, sequencer in cell_seq_dict.items():
        cell.reset()

        if not skip_nco_sync:
            sequencer.add_nco_sync(nco_sync_length)

    _assign_cell_to_context_manager(command_list)
    _assign_variables_to_cell(command_list)

    prog_builder = ProgramBuilderVisitor(cell_seq_dict, cell_map)

    for command in command_list:
        command.accept(prog_builder)

    for sequencer in cell_seq_dict.values():
        sequencer.end_of_program()

    return cell_seq_dict


def get_all_variables(cell_seq_dict) -> dict[Any, dict[Any, int]]:
    vars: dict[Any, dict[Any, int]] = {}
    for cell, seq in cell_seq_dict.items():
        for var in cell._relevant_vars:
            if var not in vars:
                vars[var] = {}
            vars[var][cell] = seq.get_var_register(var).adr
    return vars
