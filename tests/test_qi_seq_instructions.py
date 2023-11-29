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
import unittest
from qiclib.code.qi_seq_instructions import (
    SeqEnd,
    SeqTrigger,
    SeqBranch,
    SeqJump,
    SeqRegRegInst,
    SeqRegImmediateInst,
    SeqLoadUpperImm,
    SeqAwaitQubitState,
    SeqWaitImm,
)
from qiclib.code.qi_var_definitions import QiOpCond, QiOp


class InstructionToRISCV(unittest.TestCase):
    def test_branch_instruction(self):
        inst = SeqBranch(QiOpCond.EQ, 1, 2, 3)
        expected = 0b0000000_00010_00001_000_00110_1100011

        if inst.get_riscv_instruction() != expected:
            self.fail(bin(inst.get_riscv_instruction()) + " != " + bin(expected))

    def test_jump_instruction(self):
        inst = SeqJump(3)
        expected = 0b0_0000000011_0_00000000_00000_1101111

        if inst.get_riscv_instruction() != expected:
            self.fail(bin(inst.get_riscv_instruction()) + " != " + bin(expected))

    def test_neg_jump_instruction(self):
        inst = SeqJump(-3)
        expected = 0b1_1111111101_1_11111111_00000_1101111

        if inst.get_riscv_instruction() != expected:
            self.fail(bin(inst.get_riscv_instruction()) + " != " + bin(expected))

    def test_reg_reg_instruction(self):
        inst = SeqRegRegInst(QiOp.AND, 1, 2, 3)
        expected = 0b0000000_00011_00010_111_00001_0110011

        if inst.get_riscv_instruction() != expected:
            self.fail(bin(inst.get_riscv_instruction()) + " != " + bin(expected))

    def test_reg_immediate_instruction(self):
        inst = SeqRegImmediateInst(QiOp.RSH, 1, 2, 3)
        expected = 0b0100000_00011_00010_101_00001_0010011

        if inst.get_riscv_instruction() != expected:
            self.fail(bin(inst.get_riscv_instruction()) + " != " + bin(expected))

    def test_load_upper_immediate_instruction(self):
        inst = SeqLoadUpperImm(1, 0xF0F0F0F0)
        expected = (
            0b11110000111100001111_00001_0110111  # uses higher 20 Bits of immediate
        )

        if inst.get_riscv_instruction() != expected:
            self.fail(bin(inst.get_riscv_instruction()) + " != " + bin(expected))

    def test_wait_immediate_instruction(self):
        inst = SeqWaitImm(0xF0F0F0F0)
        expected = (
            0b00001111000011110000_00000_0000100  # uses lower 20 Bits of immediate
        )

        if inst.get_riscv_instruction() != expected:
            self.fail(bin(inst.get_riscv_instruction()) + " != " + bin(expected))

    def test_trigger_instruction(self):
        inst = SeqTrigger(5, 3, 4, 2, 1)
        expected = (
            0b01_0010_0100_11_0101_0000_00000_0000010  # uses lower 20 Bits of immediate
        )

        if inst.get_riscv_instruction() != expected:
            self.fail(bin(inst.get_riscv_instruction()) + " != " + bin(expected))

    def test_synch_start_immediate(self):
        inst = SeqEnd()
        expected = 0b0000000_00000_00000_000_00000_0001000

        if inst.get_riscv_instruction() != expected:
            self.fail(bin(inst.get_riscv_instruction()) + " != " + bin(expected))

    def test_synch_await_qubit(self):
        inst = SeqAwaitQubitState(cell=3, dst=2)

        expected = 0b000000000011_00000_010_00010_0001000

        if inst.get_riscv_instruction() != expected:
            self.fail(bin(inst.get_riscv_instruction()) + " != " + bin(expected))


class InstructionToString(unittest.TestCase):
    def test_reg_reg_to_string(self):
        # Enum returns first name to fitting value, since SUB and SRA have the same funct7 value, SUB is returned by standard
        inst = SeqRegRegInst(QiOp.RSH)

        self.assertEqual(
            "Op: REGISTER_REGISTER, dst: 0, funct3: SRL_SRA, rs1: 0, rs2: 0, funct7: SRA\n",
            str(inst),
        )
