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
This module provides basic infrastructure to perform dataflow analyses on qicode programs.

Dataflow analyses are computed on the control flow graph (CFG) of a QiJob which should be created when necessary.

The dataflow analysis itself is performed in using a standard worklist algorithm.

The abstract domain is modeled using DataflowValue. Its merge function represents the supremum calculation.
It is recommended to treat DataflowValues as immutable.
"""

from __future__ import annotations

from abc import abstractmethod
from copy import copy
from dataclasses import dataclass, field, replace
from enum import Enum
from itertools import count

from qiclib.code.qi_var_definitions import (
    QiExpression,
    _QiVariableBase,
)

from .qi_command import ForRangeCommand, IfCommand, ParallelCommand
from .qi_jobs import (
    QiCell,
    QiCommand,
    QiJob,
)


class _CFGNode:
    class Type(Enum):
        START = 0
        END = 1
        COMMAND = 2

    class SrcEdgeType(Enum):
        """CFG Edge information about the source node"""

        IF_TRUE = 0
        IF_FALSE = 1
        FOR_BODY = 2
        FOR_END = 4
        NORMAL = 5

        def __str__(self):
            return {
                _CFGNode.SrcEdgeType.IF_TRUE: "if_true",
                _CFGNode.SrcEdgeType.IF_FALSE: "if_false",
                _CFGNode.SrcEdgeType.FOR_BODY: "for_true",
                _CFGNode.SrcEdgeType.FOR_END: "for_end",
                _CFGNode.SrcEdgeType.NORMAL: "normal",
            }[self]

    class DestEdgeType(Enum):
        """CFG Edge information about the destination node"""

        FOR_BODY_RETURN = 0
        FOR_ENTRY = 1
        NORMAL = 2

        def __str__(self):
            return {
                _CFGNode.DestEdgeType.FOR_BODY_RETURN: "for_body_ret",
                _CFGNode.DestEdgeType.FOR_ENTRY: "for_entry",
                _CFGNode.DestEdgeType.NORMAL: "normal",
            }[self]

    @dataclass(unsafe_hash=True)
    class Neighbor:
        """Combination of node and both edge types. Each edge in the CFG is represented by an instance of this class"""

        node: _CFGNode
        src_edge_type: _CFGNode.SrcEdgeType
        """
        Information about the edge for the src node for example, if this edge goes to the 'else' block of an 'if' statement.)
        """
        dest_edge_type: _CFGNode.DestEdgeType = field(
            default_factory=lambda: _CFGNode.DestEdgeType.NORMAL
        )
        """
        Information about the edge for the destination node (for example, if the edge loops back from the body of a for statement.)
        """

    _cfg_node_id = count()

    def __init__(
        self,
        type: _CFGNode.Type | QiCommand,
        instruction_list,
        index,
        *predecessors: tuple[_CFGNode, _CFGNode.SrcEdgeType],
    ):
        if isinstance(type, QiCommand):
            self.type = _CFGNode.Type.COMMAND
            self.command = type
        else:
            assert isinstance(type, _CFGNode.Type)
            self.type = type

        # This field is used to associated arbitrary data with every node.
        # For example, a dataflow analysis might use this dictionary to
        # the nodes current abstract value.
        self.value_map: dict[str, CellValues] = {}

        self.predecessors: set[_CFGNode.Neighbor] = set()
        self.successors: set[_CFGNode.Neighbor] = set()

        # Used to find commands in job command list, so we can insert new instruction before or after this
        # command.
        self.instruction_list = instruction_list
        self.instruction_index = index

        self.id = next(_CFGNode._cfg_node_id)

        self.connect_predecessors(*predecessors)

    def connect_successors(self, *successors: _CFGNode.Neighbor):
        assert all(isinstance(x, _CFGNode.Neighbor) for x in successors)

        for succ_neighbor in successors:
            succ = succ_neighbor.node

            pred_neighbor = replace(succ_neighbor, node=self)

            self.successors.add(succ_neighbor)
            succ.predecessors.add(pred_neighbor)

    def connect_predecessors(self, *predecessors: _CFGNode.Neighbor):
        assert all(isinstance(x, _CFGNode.Neighbor) for x in predecessors)

        for pred_neighbor in predecessors:
            pred = pred_neighbor.node

            succ_neighbor = replace(pred_neighbor, node=self)

            self.predecessors.add(pred_neighbor)
            pred.successors.add(succ_neighbor)


class _CFG:
    """Constructs a control flow graph (CFG) from the commands of a QiJob.
    The end node does not contain a command, if the last top level command is an If-else or ForRange
    """

    def __init__(self, job: QiJob):
        self.nodes: set[_CFGNode] = set()

        start, end = recursive_build_sub_cfg(job.commands, self.nodes)

        self.end = _CFGNode(_CFGNode.Type.END, None, None, *end)
        self.start = _CFGNode(_CFGNode.Type.START, None, None)
        self.start.connect_successors(
            _CFGNode.Neighbor(start, _CFGNode.SrcEdgeType.NORMAL)
        )

    def node_iterator(self):
        visited = set()
        stack = [self.start]

        while len(stack) > 0:
            node = stack.pop()
            visited.add(node)

            yield node

            for successor in node.successors:
                successor = successor.node
                if successor not in visited:
                    stack.append(successor)

    def add_value(self, key, initial):
        for node in self.node_iterator():
            if key not in node.value_map:
                node.value_map[key] = initial

    def dump_dot_graph(self, path):
        """Dump the current cfg topology as a dot file for inspecting and debugging purposes."""

        with open(path, "w", encoding="utf-8") as f:
            f.write("\ndigraph {\n")

            queue = [self.start]
            node_visited_or_in_queue = set()
            node_visited_or_in_queue.add(self.start)

            while len(queue) > 0:
                node = queue.pop(0)

                node_attributes = "\n".join(
                    [f"{name} = {value}" for name, value in node.value_map.items()]
                )

                if node.type == _CFGNode.Type.COMMAND:
                    if isinstance(node.command, QiCommand):
                        node_text = f"{node.command._stringify()}"
                    else:
                        node_text = f"{node.command}"

                    label = f"{node_text}\n{node_attributes}"
                    shape = "box"

                elif node.type == _CFGNode.Type.START:
                    label = f"start\n{node_attributes}"
                    shape = "oval"
                elif node.type == _CFGNode.Type.END:
                    label = f"end\n{node_attributes}"
                    shape = "oval"

                escaped_label = label.translate(str.maketrans({'"': '\\"'}))

                f.write(f'\t{node.id} [shape={shape}, label="{escaped_label}"];\n')

                for successor in node.successors:
                    src_edge_type = successor.src_edge_type
                    dest_edge_type = successor.dest_edge_type
                    successor = successor.node

                    assert isinstance(successor, _CFGNode)

                    label = []

                    if src_edge_type is not _CFGNode.SrcEdgeType.NORMAL:
                        label.append(f"{src_edge_type}")
                    if dest_edge_type is not _CFGNode.DestEdgeType.NORMAL:
                        label.append(f"{dest_edge_type}")

                    label = ", ".join(label)

                    node_label = f'[label="{label}"]'

                    f.write(f"\t{node.id} -> {successor.id} {node_label};\n")
                    if successor not in node_visited_or_in_queue:
                        queue.append(successor)
                        node_visited_or_in_queue.add(successor)

            f.write("}")


def recursive_build_sub_cfg(
    commands: list[QiCommand], nodes
) -> tuple[_CFGNode, list[_CFGNode.Neighbor]]:
    """
    Constructs the nodes and edges for a CFG containing provided commands.
    `nodes` accumulates all nodes of the CFG.
    """

    assert len(commands) > 0

    prev: list[_CFGNode.Neighbor] = []

    for idx, command in enumerate(commands):
        if isinstance(command, IfCommand):
            node = _CFGNode(command, commands, idx, *prev)
            nodes.add(node)

            if len(command.body) > 0:
                body_start, body_end = recursive_build_sub_cfg(command.body, nodes)
                node.connect_successors(
                    _CFGNode.Neighbor(body_start, _CFGNode.SrcEdgeType.IF_TRUE)
                )
                prev = body_end
            else:
                prev = [_CFGNode.Neighbor(node, _CFGNode.SrcEdgeType.IF_TRUE)]

            if command.is_followed_by_else():  # len(command._else_body) > 0
                else_start, else_end = recursive_build_sub_cfg(
                    command._else_body, nodes
                )
                node.connect_successors(
                    _CFGNode.Neighbor(else_start, _CFGNode.SrcEdgeType.IF_FALSE)
                )
                prev += else_end
            else:
                prev.append(_CFGNode.Neighbor(node, _CFGNode.SrcEdgeType.IF_FALSE))

        elif isinstance(command, ForRangeCommand):
            for p in prev:
                p.dest_edge_type = _CFGNode.DestEdgeType.FOR_ENTRY

            node = _CFGNode(command, commands, idx, *prev)
            nodes.add(node)

            if len(command.body) > 0:
                body_start, body_end = recursive_build_sub_cfg(command.body, nodes)

                dest_edge_type = (
                    _CFGNode.DestEdgeType.FOR_ENTRY
                    if isinstance(body_start.command, ForRangeCommand)
                    else None
                )

                node.connect_successors(
                    _CFGNode.Neighbor(
                        body_start, _CFGNode.SrcEdgeType.FOR_BODY, dest_edge_type
                    )
                )

                for b in body_end:
                    b.dest_edge_type = _CFGNode.DestEdgeType.FOR_BODY_RETURN

                node.connect_predecessors(*body_end)
            else:
                node.connect_predecessors(
                    _CFGNode.Neighbor(
                        node,
                        _CFGNode.SrcEdgeType.FOR_BODY,
                        _CFGNode.DestEdgeType.FOR_BODY_RETURN,
                    )
                )

            prev = [_CFGNode.Neighbor(node, _CFGNode.SrcEdgeType.FOR_END)]

        elif isinstance(command, ParallelCommand):
            # Parallel Blocks have somewhat tricky semantics and don't fit neatly into a CFG schema.
            # Therefore we just treat them as a single command and the respective analyses can deal with them
            # as they see fit.
            node = _CFGNode(command, commands, idx, *prev)
            nodes.add(node)
            prev = [_CFGNode.Neighbor(node, _CFGNode.SrcEdgeType.NORMAL)]
        else:
            node = _CFGNode(command, commands, idx, *prev)
            nodes.add(node)
            prev = [_CFGNode.Neighbor(node, _CFGNode.SrcEdgeType.NORMAL)]

        if idx == 0:
            start = node

    end = prev

    return start, end


class DataflowValue:
    """
    Interface for the abstract value used by dataflow analyses
    An implementation of DataflowValue should be a bounded lattice.
    """

    @abstractmethod
    def merge(self, other: DataflowValue) -> DataflowValue:
        raise NotImplementedError(
            f"{self.__class__} doesn't implement merge function. This is a bug."
        )


class DataflowVisitor:
    """Visitor for dataflow analyses. The input (of type DataflowValue) is in the input field.
    The resulting output is returned by the respective visitor methods."""

    def visit_cell_command(self, cell_cmd, input, node):
        return input

    def visit_context_manager(self, context_manager, input, node):
        return input

    def visit_if(self, if_cm, input, node):
        return input

    def visit_parallel(self, parallel_cm, input, node):
        return input

    def visit_for_range(self, for_range_cm, input, node):
        return input

    def visit_variable_command(self, variable_cmd, input, node):
        return input

    def visit_assign_command(self, assign_cmd, input, node):
        return input

    def visit_declare_command(self, declare_cmd, input, node):
        return input

    def visit_sync_command(self, sync_cmd, input, node):
        return input

    def visit_asm_command(self, asm_command, input, node):
        return input


def forward_dataflow(
    cfg: _CFG,
    name,
    visitor: DataflowVisitor,
    initial: DataflowValue,
):
    dataflow(
        cfg,
        name,
        visitor,
        initial,
        lambda x: x.predecessors,
        lambda x: x.successors,
    )


def reverse_dataflow(
    cfg: _CFG,
    name,
    visitor: DataflowVisitor,
    initial: DataflowValue,
):
    dataflow(
        cfg,
        name,
        visitor,
        initial,
        lambda x: x.successors,
        lambda x: x.predecessors,
    )


def dataflow(
    cfg: _CFG,
    name,
    visitor: DataflowVisitor,
    initial: DataflowValue,
    predecessors,
    successors,
):
    """Implementation of (a fairly naive) worklist algorithm which performs the dataflow analysis,
    with the given visitor."""

    queue = list(cfg.nodes)

    cfg.add_value(name, initial)

    while len(queue) != 0:
        next = queue.pop(0)

        preds = list(predecessors(next))
        if len(preds) != 0:
            input = preds[0].node.value_map[name]

            for pred in preds[1:]:
                input = input.merge(pred.node.value_map[name])
        else:
            input = initial

        if next.type == _CFGNode.Type.COMMAND:
            output = next.command.accept(visitor, input, next)
        else:
            output = input

        original = next.value_map[name]

        if output != original:
            next.value_map[name] = output

            for succ in successors(next):
                queue.append(succ.node)


class FlatLatticeValue(DataflowValue):
    """
    FlatLatticeValue is a commonly used abstract value.

    * undefined: represents no value.
    * value: represents a single value.
    * no_const: represents all values.

    One should not use this constructor directly but instead use the :meth:`undefined` :meth:`no_const` and
    :meth:`value` class functions instead.
    """

    class Type(Enum):
        UNDEFINED = 0
        VALUE = 1
        NO_CONST = 2

    def __init__(self, type, value: QiExpression):
        self.type = type
        self.value = value

    @classmethod
    def undefined(cls):
        return cls(FlatLatticeValue.Type.UNDEFINED, None)

    @classmethod
    def no_const(cls):
        return cls(FlatLatticeValue.Type.NO_CONST, None)

    @classmethod
    def value(cls, value: QiExpression):
        assert isinstance(
            value, QiExpression
        ), f"Expected expression but got {value} of type {type(value)}"
        return cls(FlatLatticeValue.Type.VALUE, value)

    def merge(self, other):
        assert isinstance(other, FlatLatticeValue)

        if self.type == other.type and self.type == FlatLatticeValue.Type.VALUE:
            if self.value._equal_syntax(other.value):
                return self
            else:
                return FlatLatticeValue.no_const()
        else:
            if self.type == FlatLatticeValue.Type.UNDEFINED:
                return other
            elif other.type == FlatLatticeValue.Type.UNDEFINED:
                return self
            elif self.type == FlatLatticeValue.Type.NO_CONST:
                return self
            elif other.type == FlatLatticeValue.Type.NO_CONST:
                return other
            else:
                raise NotImplementedError(f"Merge of {other.type} not implemented")

    def __eq__(self, other):
        return self.type == other.type and (
            self.value._equal_syntax(other.value)
            if self.type == FlatLatticeValue.Type.VALUE
            else True
        )

    def __str__(self):
        if self.type == FlatLatticeValue.Type.VALUE:
            return str(self.value)
        else:
            return str(self.type)

    def __repr__(self):
        if self.type == FlatLatticeValue.Type.UNDEFINED:
            return "<undefined>"
        elif self.type == FlatLatticeValue.Type.VALUE:
            return f"<value: {self.value}>"
        elif self.type == FlatLatticeValue.Type.NO_CONST:
            return "<no_const>"
        else:
            raise NotImplementedError(f"__repr__ for type {self.type} not implemented")


class CellValues(DataflowValue):
    """
    DataflowValue which generalises FlatLatticeValue so every cell has its own FlatLatticeValue.
    """

    def __init__(self, values: dict[QiCell, FlatLatticeValue] | None = None):
        self.values: dict[QiCell, FlatLatticeValue] = copy(values or {})

    @classmethod
    def default(cls, cells: list[QiCell], value: FlatLatticeValue):
        return cls(dict.fromkeys(cells, value))

    def merge(self, other):
        assert isinstance(other, CellValues)

        result_values = {}

        for cell, val in self.values.items():
            if cell in other.values:
                result_values[cell] = val.merge(other[cell])
            else:
                result_values[cell] = val

        for cell, val in other.values.items():
            if cell not in result_values:
                result_values[cell] = val

        result = CellValues()

        result.values = result_values

        return result

    def merge_cell_value(self, cell: QiCell, value: FlatLatticeValue):
        assert isinstance(value, DataflowValue)
        if cell in self.values:
            self.values[cell] = self.values[cell].merge(value)
        else:
            self.values[cell] = value

    def set_cell_value(self, cell: QiCell, value: FlatLatticeValue):
        assert isinstance(value, DataflowValue)
        self.values[cell] = value

    def get_cell_value(self, cell: QiCell):
        if cell in self.values:
            return self.values[cell]
        else:
            return FlatLatticeValue.undefined()

    def invalidate_values_containing(self, var: _QiVariableBase):
        result = copy(self)

        for cell, value in result.values.items():
            if (
                value.type == FlatLatticeValue.Type.VALUE
                and var in value.value.contained_variables
            ):
                result.values[cell] = FlatLatticeValue.no_const()

        return result

    def __copy__(self):
        values = copy(self.values)
        return CellValues(values)

    def __getitem__(self, idx):
        if idx not in self.values:
            return FlatLatticeValue.undefined()
        else:
            return self.values[idx]

    def __setitem__(self, idx, val):
        assert isinstance(val, DataflowValue)
        self.values[idx] = val

    def __str__(self):
        return ",\n".join(
            f"{cell.cell_id} -> {value}" for cell, value in self.values.items()
        )

    def __eq__(self, other):
        if not isinstance(other, CellValues):
            return False

        for cell, value in self.values.items():
            if value.type != FlatLatticeValue.Type.UNDEFINED and (
                cell not in other.values or other[cell] != value
            ):
                return False

        for cell, value in other.values.items():
            if value.type != FlatLatticeValue.Type.UNDEFINED and (
                cell not in self.values or self[cell] != value
            ):
                return False

        return True
