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
from qiclib.code.qi_seq_instructions import (
    SeqAwaitQubitState,
    SeqBranch,
    SeqEnd,
    SeqJump,
    SeqLoadUpperImm,
    SeqRegImmediateInst,
    SeqRegRegInst,
    SeqTrigger,
    SeqWaitImm,
)
from qiclib.code.qi_var_definitions import QiOp, QiOpCond


def test_branch_instruction():
    inst = SeqBranch(QiOpCond.EQ, 1, 2, 3)
    expected = 0b0000000_00010_00001_000_00110_1100011

    assert inst.get_riscv_instruction() == expected, (
        bin(inst.get_riscv_instruction()) + " != " + bin(expected)
    )


def test_jump_instruction():
    inst = SeqJump(3)
    expected = 0b0_0000000011_0_00000000_00000_1101111

    assert inst.get_riscv_instruction() == expected, (
        bin(inst.get_riscv_instruction()) + " != " + bin(expected)
    )


def test_neg_jump_instruction():
    inst = SeqJump(-3)
    expected = 0b1_1111111101_1_11111111_00000_1101111

    assert inst.get_riscv_instruction() == expected, (
        bin(inst.get_riscv_instruction()) + " != " + bin(expected)
    )


def test_reg_reg_instruction():
    inst = SeqRegRegInst(QiOp.AND, 1, 2, 3)
    expected = 0b0000000_00011_00010_111_00001_0110011

    assert inst.get_riscv_instruction() == expected, (
        bin(inst.get_riscv_instruction()) + " != " + bin(expected)
    )


def test_reg_immediate_instruction():
    inst = SeqRegImmediateInst(QiOp.RSH, 1, 2, 3)
    expected = 0b0100000_00011_00010_101_00001_0010011

    assert inst.get_riscv_instruction() == expected, (
        bin(inst.get_riscv_instruction()) + " != " + bin(expected)
    )


def test_load_upper_immediate_instruction():
    inst = SeqLoadUpperImm(1, 0xF0F0F0F0)
    expected = 0b11110000111100001111_00001_0110111  # uses higher 20 Bits of immediate

    assert inst.get_riscv_instruction() == expected, (
        bin(inst.get_riscv_instruction()) + " != " + bin(expected)
    )


def test_wait_immediate_instruction():
    inst = SeqWaitImm(0xF0F0F0F0)
    expected = 0b00001111000011110000_00000_0000100  # uses lower 20 Bits of immediate

    assert inst.get_riscv_instruction() == expected, (
        bin(inst.get_riscv_instruction()) + " != " + bin(expected)
    )


def test_trigger_instruction():
    inst = SeqTrigger(5, 0, 4, 2, 1, 3)
    expected = 0b11_01_10_0100_00_0101_00_0000000_0000010

    assert inst.get_riscv_instruction() == expected, (
        bin(inst.get_riscv_instruction()) + " != " + bin(expected)
    )


def test_synch_start_immediate():
    inst = SeqEnd()
    expected = 0b0000000_00000_00000_000_00000_0001000

    assert inst.get_riscv_instruction() == expected, (
        bin(inst.get_riscv_instruction()) + " != " + bin(expected)
    )


def test_synch_await_qubit():
    inst = SeqAwaitQubitState(cell=3, dst=2)
    expected = 0b000000000011_00000_010_00010_0001000

    assert inst.get_riscv_instruction() == expected, (
        bin(inst.get_riscv_instruction()) + " != " + bin(expected)
    )


def test_reg_reg_to_string():
    assert (
        str(SeqRegRegInst(QiOp.PLUS, dst_reg=1, reg_1=5, reg_2=0)) == "add r1, r5, r0"
    )
    assert (
        str(SeqRegRegInst(QiOp.MINUS, dst_reg=1, reg_1=5, reg_2=0)) == "sub r1, r5, r0"
    )
    assert (
        str(SeqRegRegInst(QiOp.MULT, dst_reg=1, reg_1=5, reg_2=0)) == "mul r1, r5, r0"
    )
    assert str(SeqRegRegInst(QiOp.LSH, dst_reg=1, reg_1=5, reg_2=0)) == "sll r1, r5, r0"
    assert str(SeqRegRegInst(QiOp.RSH, dst_reg=1, reg_1=5, reg_2=0)) == "sra r1, r5, r0"
    assert str(SeqRegRegInst(QiOp.AND, dst_reg=1, reg_1=5, reg_2=0)) == "and r1, r5, r0"
    assert str(SeqRegRegInst(QiOp.OR, dst_reg=1, reg_1=5, reg_2=0)) == "or r1, r5, r0"
    assert str(SeqRegRegInst(QiOp.XOR, dst_reg=1, reg_1=5, reg_2=0)) == "xor r1, r5, r0"
