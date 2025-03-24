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
from __future__ import annotations

import abc
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, ClassVar

if TYPE_CHECKING:
    from qiclib.code import QiCell
    from qiclib.code.qi_command import QiCellCommand, QiCommand


class QiCommandVisitor(abc.ABC):
    """
    Generic visitor to traverse the AST generated using a QiJob.
    For tree traversal, one would typically subclass this visitor and overwrite
    relevant methods.
    """

    def visit_cell_command(self, cell_cmd: QiCellCommand, *args, **kwargs):
        """
        Visits any cell command
        """

    def visit_context_manager(self, context_manager, *args, **kwargs):
        pass

    def visit_if(self, if_cm, *args, **kwargs):
        pass

    def visit_parallel(self, parallel_cm, *args, **kwargs):
        self.visit_context_manager(parallel_cm, *args, **kwargs)

    def visit_for_range(self, for_range_cm, *args, **kwargs):
        self.visit_context_manager(for_range_cm, *args, **kwargs)

    def visit_variable_command(self, variable_cmd, *args, **kwargs):
        pass

    def visit_assign_command(self, assign_cmd, *args, **kwargs):
        self.visit_variable_command(assign_cmd, *args, **kwargs)

    def visit_declare_command(self, declare_cmd, *args, **kwargs):
        self.visit_variable_command(declare_cmd, *args, **kwargs)

    def visit_sync_command(self, sync_cmd, *args, **kwargs):
        pass

    def visit_asm_command(self, asm_cmd, *args, **kwargs):
        pass

    def visit_mem_store_command(self, store_cmd, *args, **kwargs):
        pass


class QiCMContainedCellVisitor(QiCommandVisitor):
    """Visitor to check which cells are used inside context managers."""

    def __init__(self) -> None:
        self.contained_cells: set[QiCell] = set()

    def visit_cell_command(self, cell_cmd, *args, **kwargs):
        self.contained_cells.update(cell_cmd._relevant_cells)

    def visit_context_manager(self, context_manager, *args, **kwargs):
        visitor = QiCMContainedCellVisitor()
        for item in context_manager.body:
            item.accept(visitor)

        context_manager._relevant_cells.update(visitor.contained_cells)

        self.contained_cells.update(visitor.contained_cells)

    def visit_if(self, if_cm, *args, **kwargs):
        visitor = QiCMContainedCellVisitor()
        for command in if_cm.body:
            command.accept(visitor)

        for command in if_cm.else_body:
            command.accept(visitor)

        if_cm._relevant_cells.update(visitor.contained_cells)

        self.contained_cells.update(visitor.contained_cells)

    def visit_parallel(self, parallel_cm, *args, **kwargs):
        visitor = QiCMContainedCellVisitor()
        for cmd_list in parallel_cm.entries:
            for cmd in cmd_list:
                cmd.accept(visitor)

        parallel_cm._relevant_cells.update(visitor.contained_cells)

        self.contained_cells.update(visitor.contained_cells)

    def visit_variable_command(self, variable_cmd, *args, **kwargs):
        self.contained_cells.update(variable_cmd._relevant_cells)

    def visit_sync_command(self, sync_cmd, *args, **kwargs):
        self.contained_cells.update(sync_cmd._relevant_cells)

    def visit_asm_command(self, asm_cmd, *args, **kwargs):
        self.contained_cells.update(asm_cmd._relevant_cells)

    def visit_mem_store_command(self, store_cmd, *args, **kwargs):
        self.contained_cells.update(store_cmd._relevant_cells)


class QiVarInForRange(QiCommandVisitor):
    """Visitor used to visit QiCommands inside ForRange-Contextmanager. Raises error, if variable used in ForRange-Head is target of an Assign or Store
    command inside ForRange-Body. Additionally generates UserWarning when loop-variable is used inside Parallel-CM.
    """

    def __init__(self, var) -> None:
        self.var = var

    def _raise_exception(self):
        raise RuntimeError(
            f"Variable used in ForRange must not be used in internal Assign-Commands, var: {self.var}"
        )

    def visit_cell_command(self, cell_cmd, *args, **kwargs):
        from .qi_command import StoreCommand

        if isinstance(cell_cmd, StoreCommand):
            if id(cell_cmd.store_var) == id(self.var):
                self._raise_exception()

    def visit_context_manager(self, context_manager, *args, **kwargs):
        for item in context_manager.body:
            item.accept(self)

    def visit_if(self, if_cm, *args, **kwargs):
        for command in if_cm.body:
            command.accept(self)

        for command in if_cm.else_body:
            command.accept(self)

    def visit_parallel(self, parallel_cm, *args, **kwargs):
        if self.var in parallel_cm._associated_variable_set:
            raise RuntimeError(
                "Loop variable inside Parallel Context Manager might result in unexpected behaviour. "
                "Please unroll loop or change variable."
            )

    def visit_assign_command(self, assign_cmd, *args, **kwargs):
        if id(assign_cmd.var) == id(self.var):
            self._raise_exception()


class QiCmdVariableInspection(QiCommandVisitor):
    """Visits QiCommands and assigns cell to a QiVariable, if the variable is used for the cells program execution

    QiCMContainedCellVisitor needs to be run beforehand"""

    def visit_cell_command(self, cell_cmd, *args, **kwargs):
        for variable in cell_cmd._associated_variable_set:
            for cell in cell_cmd._relevant_cells:
                self._add_cell_to_var(cell, variable)

    def visit_context_manager(self, context_manager, *args, **kwargs):
        # TODO does Else need to have the same relevant cells as If?
        for command in reversed(context_manager.body):
            command.accept(self)

        for variable in context_manager._associated_variable_set:
            for cell in context_manager._relevant_cells:
                self._add_cell_to_var(cell, variable)

    def visit_if(self, if_cm, *args, **kwargs):
        # TODO does Else need to have the same relevant cells as If?
        for command in reversed(if_cm.body):
            command.accept(self)

        for command in reversed(if_cm.else_body):
            command.accept(self)

        for variable in if_cm._associated_variable_set:
            for cell in if_cm._relevant_cells:
                self._add_cell_to_var(cell, variable)

    def visit_parallel(self, parallel_cm, *args, **kwargs):
        for cmd_list in parallel_cm.entries:
            for cmd in reversed(cmd_list):
                cmd.accept(self)

    def visit_variable_command(self, variable_cmd, *args, **kwargs):
        self.visit_cell_command(variable_cmd)

    def visit_assign_command(self, assign_cmd, *args, **kwargs):
        """assign_cmd.var is the destination variable. For every relevant cell of the variable, which were defined
        beforehand, the assign command is also relevant for the same cell.

        Variables that are needed to calculate assign_cmd.var are contained in assign_cmd._associated_variable_set. For every
        one of these associated variables they must at least have the same relevant cells as assign_cmd.var, therefore
        they are added here"""

        for cell in assign_cmd.var._relevant_cells:
            assign_cmd._relevant_cells.add(cell)

            for variable in assign_cmd._associated_variable_set:
                self._add_cell_to_var(cell, variable)

    def visit_declare_command(self, declare_cmd, *args, **kwargs):
        for cell in declare_cmd.var._relevant_cells:
            declare_cmd._relevant_cells.add(cell)

    def visit_sync_command(self, sync_cmd, *args, **kwargs):
        pass

    def _add_cell_to_var(self, cell, var):
        var._relevant_cells.add(cell)
        cell.add_variable(var)


class QiResultCollector(QiCommandVisitor):
    def __init__(self):
        # If there are multiple QiResults used, we need to
        # simulate in which order they record.
        self.found_qi_results = set()
        # We also collect the recordings which contain the qi_results above
        self.corresponding_recordings = set()

        # Is a recording which saves to a QiResult within an if.
        # In these cases we can not necessarily simulate the recording order.
        self.recording_in_if = False

        self.if_else_depth = 0

    def visit_cell_command(self, cell_cmd, *args, **kwargs):
        from .qi_jobs import PlayReadoutCommand, RecordingCommand

        if isinstance(cell_cmd, PlayReadoutCommand) and cell_cmd.recording is not None:
            cell_cmd = cell_cmd.recording

        if isinstance(cell_cmd, RecordingCommand):
            if self.if_else_depth > 0:
                self.recording_in_if = True

            self.found_qi_results.add(cell_cmd.save_to)
            self.corresponding_recordings.add(cell_cmd)

    def visit_if(self, if_cm, *args, **kwargs):
        self.if_else_depth += 1

        for cmd in if_cm.body:
            cmd.accept(self)

        for cmd in if_cm.body:
            cmd.accept(self)

        self.if_else_depth -= 1

    def visit_parallel(self, parallel_cm, *args, **kwargs):
        for cmd in parallel_cm.body:
            cmd.accept(self)

    def visit_for_range(self, for_range_cm, *args, **kwargs):
        for cmd in for_range_cm.body:
            cmd.accept(self)


class QiFindVarCmds(QiCommandVisitor):
    """Used to find Pulse and Wait commands containing given QiTimeVariable"""

    def __init__(self, var) -> None:
        self.requested_var = var
        self.found_cmds: list[QiCommand] = []
        self.calc_in_wait = False

    def visit_cell_command(self, cell_cmd, *args, **kwargs):
        """Add commands if the use QiTimeVariable. If variable is used in calculation in wait, it is registered in calc_in_wait"""
        from .qi_command import AnyPlayCommand, WaitCommand
        from .qi_var_definitions import _QiVariableBase

        if (
            isinstance(cell_cmd, AnyPlayCommand)
            and cell_cmd.is_variable_relevant(self.requested_var)
        ) or (
            isinstance(cell_cmd, WaitCommand)
            and isinstance(cell_cmd.length, _QiVariableBase)
            and cell_cmd.length.id == self.requested_var.id
        ):
            self.found_cmds.append(cell_cmd)
        elif isinstance(cell_cmd, WaitCommand) and cell_cmd.is_variable_relevant(
            self.requested_var
        ):
            self.found_cmds.append(cell_cmd)
            self.calc_in_wait = True

    def visit_context_manager(self, context_manager, *args, **kwargs):
        """Search for variable commands in context manager's bodies"""
        for command in context_manager.body:
            command.accept(self)

    def visit_if(self, if_cm, *args, **kwargs):
        """Search for variable commands in context manager's bodies"""
        for command in if_cm.body:
            command.accept(self)

        for command in if_cm.else_body:
            command.accept(self)

    def visit_parallel(self, parallel_cm, *args, **kwargs):
        """Avoid multiple additions to list, if multiple commands use self.requested_var"""
        for command in parallel_cm.body:
            if self.requested_var in command._associated_variable_set:
                self.found_cmds.append(command)
                return

    def visit_variable_command(self, variable_cmd, *args, **kwargs):
        pass

    def visit_sync_command(self, sync_cmd, *args, **kwargs):
        pass


class QiExpressionVisitor:
    def visit_variable(self, var):
        pass

    def visit_calc(self, calc):
        calc.val1.accept(self)

        if calc.val2 is not None:
            calc.val2.accept(self)

    def visit_constant(self, const):
        pass

    def visit_cell_property(self, cell_prop):
        pass


class QiJobVisitor(QiCommandVisitor, QiExpressionVisitor):
    """Visitor over every program construct in qicode.
    Visits all commands, expressions and conditions."""

    def visit_cell_command(self, cell_cmd, *args, **kwargs):
        from .qi_command import AnyPlayCommand, RecordingCommand, WaitCommand
        from .qi_var_definitions import QiExpression

        if isinstance(cell_cmd, WaitCommand):
            if isinstance(cell_cmd._length, QiExpression):
                cell_cmd._length.accept(self)

        elif isinstance(cell_cmd, AnyPlayCommand):
            if isinstance(cell_cmd.pulse.length, QiExpression):
                cell_cmd.pulse._length.accept(self)

        elif isinstance(cell_cmd, RecordingCommand):
            if isinstance(cell_cmd.var, QiExpression):
                cell_cmd.var.accept(self)
            if isinstance(cell_cmd._length, QiExpression):
                cell_cmd._length.accept(self)

    def visit_context_manager(self, context_manager, *args, **kwargs):
        for cmd in context_manager.body:
            cmd.accept(self)

    def visit_if(self, if_cm, *args, **kwargs):
        if_cm.condition.accept(self)

        for cmd in if_cm.body:
            cmd.accept(self)

        for cmd in if_cm._else_body:
            cmd.accept(self)

    def visit_parallel(self, parallel_cm, *args, **kwargs):
        self.visit_context_manager(parallel_cm)

    def visit_for_range(self, for_range_cm, *args, **kwargs):
        self.visit_context_manager(for_range_cm)

    def visit_variable_command(self, variable_cmd, *args, **kwargs):
        from .qi_command import AssignCommand

        if isinstance(variable_cmd, AssignCommand):
            variable_cmd.value.accept(self)

    def visit_assign_command(self, assign_cmd, *args, **kwargs):
        self.visit_variable_command(assign_cmd)

    def visit_declare_command(self, declare_cmd, *args, **kwargs):
        self.visit_variable_command(declare_cmd)

    def visit_sync_command(self, sync_cmd, *args, **kwargs):
        pass

    def visit_variable(self, var):
        pass

    def visit_calc(self, calc):
        calc.val1.accept(self)

        if calc.val2 is not None:
            calc.val2.accept(self)

    def visit_constant(self, const):
        pass

    def visit_condition(self, condition):
        condition.val1.accept(self)
        condition.val2.accept(self)

    def visit_cell_property(self, cell_prop):
        pass


class StringFunctionPatcher:
    orig_map: ClassVar[dict[type[Any], Callable]] = {}

    def _replace_str_func(self, klass, orig_func, new_func):
        self.orig_map[klass] = orig_func
        klass.__str__ = new_func

    def _remove_str_func(self, klass, orig_func):
        self.orig_map[klass] = orig_func
        del klass.__str__

    def _restore_str_funcs(self):
        for klass, orig_func in self.orig_map.items():
            klass.__str__ = orig_func
        self.orig_map.clear()

    def patch_str(self, function):
        """
        Decorator which can be applied to functions.
        Patches __str__ of QiCell and QiVariable to better suit stringification.
        This patch is reverted once the function exits.
        """

        @wraps(function)
        def wrapper(*args, **kwargs):
            from .qi_jobs import (
                QiCell,
                QiCellProperty,
                _QiVariableBase,
            )

            # Fall back to just executing if patching already happened
            if len(self.orig_map) != 0:
                return function(*args, **kwargs)

            try:
                # Patch __str__ functions, keeping originals
                self._replace_str_func(
                    QiCell, QiCell.__str__, lambda x: f"q[{x.cell_id}]"
                )

                self._replace_str_func(
                    _QiVariableBase, _QiVariableBase.__str__, lambda x: f"v{x.str_id}"
                )

                self._replace_str_func(
                    QiCellProperty,
                    QiCellProperty.__str__,
                    lambda x: x.opcode.replace("x", f'{x.cell}["{x.name}"]'),
                )

                # Call the wrapped function
                result = function(*args, **kwargs)

            finally:
                # Revert patches
                self._restore_str_funcs()

            return result

        return wrapper


class QiStringifyJob(QiCommandVisitor):
    """Stringify a QiJob"""

    str_patcher = StringFunctionPatcher()

    def __init__(self) -> None:
        super().__init__()
        self.strings: list[str] = []
        self.indent_level = 0

    def _add_string(self, string: str):
        self.strings.append("    " * self.indent_level + string)

    def stringify(self, job) -> str:
        self._add_string(f"q = QiCells({len(job.cells)})")
        for command in job.commands:
            command.accept(self)
        return "QiJob:\n" + "\n".join(["    " + x for x in self.strings])

    @str_patcher.patch_str
    def visit_cell_command(self, cell_cmd):
        from .qi_command import PlayReadoutCommand

        self._add_string(cell_cmd._stringify())
        if isinstance(cell_cmd, PlayReadoutCommand):
            # Handle RecordingCommand commands "hidden" by PlayReadoutCommand
            if cell_cmd.recording is not None:
                self.visit_cell_command(cell_cmd.recording)

    def visit_context_manager(self, context_manager, *args, **kwargs):
        self.indent_level += 1
        for command in context_manager:
            command.accept(self)
        self.indent_level -= 1

    def visit_if(self, if_cm, *args, **kwargs):
        # Only wrap the actual "If" with str patching
        @self.str_patcher.patch_str
        def _addIf(self):
            self._add_string(if_cm._stringify() + ":")

        _addIf(self)
        self.visit_context_manager(if_cm)

        if if_cm.is_followed_by_else():
            self._add_string("Else:")
            self.visit_context_manager(if_cm._else_body)

    def visit_parallel(self, parallel_cm, *args, **kwargs):
        for block in parallel_cm.entries:
            self._add_string(parallel_cm._stringify() + ":")
            self.visit_context_manager(block)

    def visit_for_range(self, for_range_cm, *args, **kwargs):
        # Only wrap the actual "ForRange" with str patching
        @self.str_patcher.patch_str
        def _addFor(self):
            self._add_string(for_range_cm._stringify() + ":")

        _addFor(self)
        self.visit_context_manager(for_range_cm)

    @str_patcher.patch_str
    def visit_assign_command(self, assign_cmd):
        self._add_string(assign_cmd._stringify())

    def visit_declare_command(self, declare_cmd, *args, **kwargs):
        self._add_string(declare_cmd._stringify())

    @str_patcher.patch_str
    def visit_sync_command(self, sync_cmd):
        self._add_string(sync_cmd._stringify())

    @str_patcher.patch_str
    def visit_mem_store_command(self, store_cmd):
        self._add_string(store_cmd._stringify())
