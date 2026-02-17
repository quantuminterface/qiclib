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

"""Tests for SequencerInstruction.from_str() method and individual instruction parsers."""

import pytest

from qiclib.code.qi_seq_instructions import (
    SeqAwaitQubitState,
    SeqBranch,
    SeqCellSync,
    SeqEnd,
    SeqJump,
    SeqLoad,
    SeqLoadUpperImm,
    SeqRegImmediateInst,
    SeqRegRegInst,
    SeqStore,
    SeqTrigger,
    SeqTriggerWaitRegister,
    SequencerInstruction,
    SeqWaitImm,
    SeqWaitRegister,
)
from qiclib.code.qi_var_definitions import QiOp, QiOpCond


class TestSeqRegImmediateInstFromStr:
    """Tests for parsing register-immediate instructions."""

    @pytest.mark.parametrize(
        "inst_str,dst,reg,imm",
        [
            ("addi r1, r2, 0x10", 1, 2, 0x10),
            ("sll r3, r4, 0x5", 3, 4, 0x5),
            ("xori r5, r6, 0xff", 5, 6, 0xFF),
            ("ori r0, r1, 100", 0, 1, 100),
            ("andi r2, r3, 42", 2, 3, 42),
            ("sra r4, r5, 0x20", 4, 5, 0x20),
            ("srl r6, r7, 0xc", 6, 7, 0xC),
        ],
    )
    def test_reg_immediate_parsing(self, inst_str, dst, reg, imm):
        inst = SeqRegImmediateInst.from_str(inst_str)
        assert inst.dst_reg == dst
        assert inst.register == reg
        assert inst.immediate == imm

    def test_roundtrip_reg_immediate(self):
        """Test that from_str preserves instruction properties via roundtrip."""
        original = SeqRegImmediateInst(QiOp.PLUS, dst_reg=1, register=2, immediate=10)
        original_str = str(original)
        parsed = SeqRegImmediateInst.from_str(original_str)
        assert str(parsed) == original_str
        assert parsed.dst_reg == original.dst_reg
        assert parsed.register == original.register


class TestSeqRegRegInstFromStr:
    """Tests for parsing register-register instructions."""

    @pytest.mark.parametrize(
        "inst_str,dst,reg1,reg2",
        [
            ("add r1, r2, r3", 1, 2, 3),
            ("sub r4, r5, r6", 4, 5, 6),
            ("mul r0, r0, r0", 0, 0, 0),
            ("sll r7, r8, r9", 7, 8, 9),
            ("xor r2, r3, r4", 2, 3, 4),
            ("or r10, r11, r12", 10, 11, 12),
            ("and r13, r14, r15", 13, 14, 15),
        ],
    )
    def test_reg_reg_parsing(self, inst_str, dst, reg1, reg2):
        inst = SeqRegRegInst.from_str(inst_str)
        assert inst.dst_reg == dst
        assert inst.reg1 == reg1
        assert inst.reg2 == reg2

    def test_roundtrip_reg_reg(self):
        """Test roundtrip for register-register instructions."""
        original = SeqRegRegInst(QiOp.PLUS, dst_reg=5, reg_1=10, reg_2=15)
        original_str = str(original)
        parsed = SeqRegRegInst.from_str(original_str)
        assert str(parsed) == original_str
        assert parsed.dst_reg == original.dst_reg
        assert parsed.reg1 == original.reg1
        assert parsed.reg2 == original.reg2


class TestSeqBranchFromStr:
    """Tests for parsing branch instructions."""

    @pytest.mark.parametrize(
        "inst_str,reg1,reg2,imm",
        [
            ("beq r1, r2, 0x10", 1, 2, 0x10),
            ("bne r3, r4, 0x20", 3, 4, 0x20),
            ("blt r5, r6, 100", 5, 6, 100),
            ("bge r7, r8, -50", 7, 8, -50),
            ("bltu r0, r1, 0x40", 0, 1, 0x40),
            ("bgeu r2, r3, 0x80", 2, 3, 0x80),
        ],
    )
    def test_branch_parsing(self, inst_str, reg1, reg2, imm):
        inst = SeqBranch.from_str(inst_str)
        assert inst.reg1 == reg1
        assert inst.reg2 == reg2
        assert inst.immediate == imm

    def test_roundtrip_branch(self):
        """Test roundtrip for branch instructions."""
        original = SeqBranch(QiOpCond.EQ, 1, 2, 0x10)
        original_str = str(original)
        parsed = SeqBranch.from_str(original_str)
        assert str(parsed) == original_str


class TestSeqJumpFromStr:
    """Tests for parsing jump instructions."""

    @pytest.mark.parametrize(
        "inst_str,jump_val",
        [
            ("j 0x100", 0x100),
            ("j -0x50", -0x50),
            ("j 256", 256),
        ],
    )
    def test_jump_parsing(self, inst_str, jump_val):
        inst = SeqJump.from_str(inst_str)
        assert inst.jump_val == jump_val

    def test_roundtrip_jump(self):
        """Test roundtrip for jump instructions."""
        original = SeqJump(0x100)
        original_str = str(original)
        parsed = SeqJump.from_str(original_str)
        assert str(parsed) == original_str


class TestSeqLoadUpperImmFromStr:
    """Tests for parsing load upper immediate instructions."""

    @pytest.mark.parametrize(
        "inst_str,dst,imm",
        [
            ("lui r1, 0x12345", 1, 0x12345),
            ("lui r0, 0xf0f0f", 0, 0xF0F0F),
        ],
    )
    def test_lui_parsing(self, inst_str, dst, imm):
        inst = SeqLoadUpperImm.from_str(inst_str)
        assert inst.dst_reg == dst
        assert inst.immediate == imm

    def test_roundtrip_lui(self):
        """Test roundtrip for load upper immediate instructions."""
        original = SeqLoadUpperImm(5, 0x12345)
        original_str = str(original)
        parsed = SeqLoadUpperImm.from_str(original_str)
        assert str(parsed) == original_str


class TestSeqWaitImmFromStr:
    """Tests for parsing wait immediate instructions."""

    @pytest.mark.parametrize(
        "inst_str,imm",
        [
            ("wti 0x1000", 0x1000),
            ("wti 4096", 4096),
        ],
    )
    def test_wti_parsing(self, inst_str, imm):
        inst = SeqWaitImm.from_str(inst_str)
        assert inst.immediate == imm

    def test_roundtrip_wti(self):
        """Test roundtrip for wait immediate instructions."""
        original = SeqWaitImm(0x5000)
        original_str = str(original)
        parsed = SeqWaitImm.from_str(original_str)
        assert str(parsed) == original_str


class TestSeqWaitRegisterFromStr:
    """Tests for parsing wait register instructions."""

    @pytest.mark.parametrize(
        "inst_str,dst",
        [
            ("wtr r1, 0x0", 1),
            ("wtr r5, 0x0", 5),
        ],
    )
    def test_wtr_parsing(self, inst_str, dst):
        inst = SeqWaitRegister.from_str(inst_str)
        assert inst.dst_reg == dst


class TestSeqTriggerWaitRegisterFromStr:
    """Tests for parsing trigger wait register instructions."""

    @pytest.mark.parametrize(
        "inst_str,dst",
        [
            ("twr r2, 0x0", 2),
            ("twr r7, 0x0", 7),
        ],
    )
    def test_twr_parsing(self, inst_str, dst):
        inst = SeqTriggerWaitRegister.from_str(inst_str)
        assert inst.dst_reg == dst


class TestSeqTriggerFromStr:
    """Tests for parsing trigger instructions."""

    @pytest.mark.parametrize(
        "inst_str,expected_indices",
        [
            ("tr 0x1, 0x2, 0x3, 0x4, 0x5, 0x6", [1, 2, 3, 4, 5, 6]),
            ("tr 0x0, 0x0, 0x0, 0x0, 0x0, 0x0", [0, 0, 0, 0, 0, 0]),
            ("tr 5, 0, 4, 2, 1, 3", [5, 0, 4, 2, 1, 3]),
        ],
    )
    def test_trigger_parsing(self, inst_str, expected_indices):
        inst = SeqTrigger.from_str(inst_str)
        assert inst._trig_indices == expected_indices

    def test_roundtrip_trigger(self):
        """Test roundtrip for trigger instructions."""
        original = SeqTrigger(5, 0, 4, 2, 1, 3)
        original_str = str(original)
        parsed = SeqTrigger.from_str(original_str)
        assert str(parsed) == original_str


class TestSeqEndFromStr:
    """Tests for parsing end instructions."""

    @pytest.mark.parametrize(
        "inst_str",
        [
            "end",
            "end   ",
        ],
    )
    def test_end_parsing(self, inst_str):
        inst = SeqEnd.from_str(inst_str)
        assert isinstance(inst, SeqEnd)


class TestSeqAwaitQubitStateFromStr:
    """Tests for parsing await qubit state instructions."""

    @pytest.mark.parametrize(
        "inst_str,dst,imm",
        [
            ("wtq r2, 3", 2, 3),
            ("wtq r5, 10", 5, 10),
        ],
    )
    def test_wtq_parsing(self, inst_str, dst, imm):
        inst = SeqAwaitQubitState.from_str(inst_str)
        assert inst.dst_reg == dst
        assert inst.immediate == imm

    def test_roundtrip_wtq(self):
        """Test roundtrip for await qubit state instructions."""
        original = SeqAwaitQubitState(cell=3, dst=2)
        original_str = str(original)
        parsed = SeqAwaitQubitState.from_str(original_str)
        assert str(parsed) == original_str


class TestSeqLoadFromStr:
    """Tests for parsing load instructions."""

    @pytest.mark.parametrize(
        "inst_str,dst,base,imm",
        [
            ("lw r1, 0(r2)", 1, 2, 0),
            ("lh r3, 4(r4)", 3, 4, 4),
            ("lb r5, 8(r6)", 5, 6, 8),
            ("lbu r7, -4(r8)", 7, 8, -4),
            ("lhu r9, 100(r10)", 9, 10, 100),
        ],
    )
    def test_load_parsing(self, inst_str, dst, base, imm):
        inst = SeqLoad.from_str(inst_str)
        assert inst.dst_reg == dst
        assert inst.base_reg == base
        assert inst.immediate == imm

    def test_roundtrip_load(self):
        """Test roundtrip for load instructions."""
        original = SeqLoad(dst=5, base=10, offset=8)
        original_str = str(original)
        parsed = SeqLoad.from_str(original_str)
        assert str(parsed) == original_str


class TestSeqStoreFromStr:
    """Tests for parsing store instructions."""

    @pytest.mark.parametrize(
        "inst_str,src,base,offset",
        [
            ("sw r1, 0(r2)", 1, 2, 0),
        ],
    )
    def test_store_parsing(self, inst_str, src, base, offset):
        inst = SeqStore.from_str(inst_str)
        assert inst == SeqStore(src, base, offset)

    def test_roundtrip_store(self):
        """Test roundtrip for store instructions."""
        original = SeqStore(src=3, base=7, offset=16)
        original_str = str(original)
        parsed = SeqStore.from_str(original_str)
        assert str(parsed) == original_str


class TestSeqCellSyncFromStr:
    """Tests for parsing cell sync instructions."""

    def test_sync_parsing(self):
        """Test parsing sync instruction."""
        # Create an instruction first to get the correct format
        original = SeqCellSync([1, 2, 3])
        original_str = str(original)
        # Now parse it
        parsed = SeqCellSync.from_str(original_str)
        # Check that we got the same instruction back
        assert str(parsed) == original_str


@pytest.mark.parametrize(
    "instr_str,inst",
    [
        ("addi r1, r2, 0x10", SeqRegImmediateInst(QiOp.PLUS, 1, 2, 0x10)),
        ("add r1, r2, r3", SeqRegRegInst(QiOp.PLUS, 1, 2, 3)),
        ("beq r1, r2, 0x10", SeqBranch(QiOpCond.EQ, 1, 2, 0x10)),
        ("j 0x100", SeqJump(0x100)),
        ("lui r5, 0x12345", SeqLoadUpperImm(5, 0x12345)),
        ("wti 0x1000", SeqWaitImm(0x1000)),
        ("wtr r1, 0x0", SeqWaitRegister(1)),
        ("twr r2, 0x0", SeqTriggerWaitRegister(2)),
        ("tr 0x1, 0x2, 0x3, 0x4, 0x5, 0x6", SeqTrigger(1, 2, 3, 4, 5, 6)),
        ("end", SeqEnd()),
        ("wtq r2, 3", SeqAwaitQubitState(3, 2)),
        ("lw r1, 0(r2)", SeqLoad(1, 2, 0)),
        ("sw r1, 0(r2)", SeqStore(1, 2, 0)),
    ],
)
def test_sequencer_instruction_factory(instr_str, inst):
    """Parametrized test for SequencerInstruction factory method."""
    assert SequencerInstruction.from_str(instr_str) == inst
    assert str(inst) == instr_str


def test_factory_unknown_instruction():
    """Test factory method with unknown instruction."""
    with pytest.raises(ValueError):
        SequencerInstruction.from_str("unknown_op r1, r2")


def test_factory_malformed_instruction():
    """Test factory method with malformed instruction."""
    with pytest.raises(ValueError):
        SequencerInstruction.from_str("addi r1")
