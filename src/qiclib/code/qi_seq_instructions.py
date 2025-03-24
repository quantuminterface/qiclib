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
This module defines the customized RISC-V instruction set used by the sequencers
and how to encode the instruction into their binary format.
"""

from __future__ import annotations

import abc
from abc import abstractmethod
from enum import Enum
from typing import Generic, TypeVar

from .qi_var_definitions import QiOp, QiOpCond


class SeqOpCode(Enum):
    """Enumeration containing Opcodes of Sequencer instructions"""

    JUMP = 0b1101111
    BRANCH = 0b1100011
    REG_IMM = 0b0010011
    LOAD_UPPER_IMM = 0b0110111
    REGISTER_REGISTER = 0b0110011
    LOAD = 0b0000011
    STORE = 0b0100011
    SYNCH = 0b0001000
    WAIT_IMM = 0b0000100
    WAIT_REG = 0b0000110
    TRIG_WAIT_REG = 0b0001010
    TRIGGER = 0b0000010
    CELL_SYNC = 0b0001100
    REG_SEND = 0b0001110
    REG_RECEIVE = 0b0011100


class SeqRegImmFunct3(Enum):
    """Enumeration containing funct3 values of Sequencer Register Immediate instructions"""

    ADD = 0b000
    SLL = 0b001
    LW = 0b010
    SW = 0b010
    XOR = 0b100
    SR = 0b101
    OR = 0b110
    AND = 0b111


class SeqRegImmFunct7(Enum):
    """Enumeration containing funct7 values of Sequencer Register Immediate instructions"""

    SRL = 0b0000000
    SRA = 0b0100000


class SeqExtSynchFunct3(Enum):
    """Enumeration containing funct3 values of Sequencer External Synch instructions"""

    START = 0b000
    QUBIT_STATE = 0b010


class SeqBranchFunct3(Enum):
    """Enumeration containing funct3 values of Sequencer Branch instructions"""

    BEQ = 0b000
    BNE = 0b001
    BLT = 0b100
    BGE = 0b101
    BLTU = 0b110
    BGEU = 0b111


class SeqRegRegFunct3(Enum):
    """Enumeration containing funct3 values of Sequencer Register Register instructions"""

    ADD_SUB_MUL = 0b000
    SLL_MULH = 0b001
    XOR = 0b100
    SRL_SRA = 0b101
    OR = 0b110
    AND = 0b111


class SeqMemFunct3(Enum):
    """
    Enumeration containing funct3 values for Store and Load Sequencer instructions.
    B = byte 8-bit
    H = half 16-bit
    W = wide 32-bit
    The following are only applicable to load instructions and will not sign extend the loaded value.
    BU = unsigned byte 8-bit
    BH = unsigned half 16-bit
    """

    B = 0b000
    H = 0b001
    W = 0b010
    BU = 0b100
    HU = 0b101

    @staticmethod
    def get_from_width(width: int, signed: bool = False):
        return {
            (8, False): SeqMemFunct3.B,
            (16, False): SeqMemFunct3.H,
            (32, False): SeqMemFunct3.W,
            (8, True): SeqMemFunct3.BU,
            (16, True): SeqMemFunct3.HU,
        }[width, signed]


class SeqRegSendFunct3(Enum):
    """Enumeration containing funct3 values of Sequencer Register Send Instructions"""

    Single = 0b000
    Multi = 0b001


class SeqRegRegFunct7(Enum):
    """Enumeration containing funct7 values of Sequencer Register Immediate instructions"""

    ADD = 0b0000000
    SUB = 0b0100000
    MUL = 0b0000001
    SLL = 0b0000000
    MULH = 0b0000001
    XOR = 0b0000000
    SRL = 0b0000000
    SRA = 0b0100000
    OR = 0b0000000
    AND = 0b0000000

    @staticmethod
    def get_name(funct3, funct7):
        """Provides correct name for funct7 value, enum.name would only provide name for the first matching value"""
        if funct3 == SeqRegRegFunct3.ADD_SUB_MUL:
            switcher = {
                SeqRegRegFunct7.ADD: "ADD",
                SeqRegRegFunct7.SUB: "SUB",
                SeqRegRegFunct7.MUL: "MUL",
            }
        elif funct3 == SeqRegRegFunct3.SLL_MULH:
            switcher = {
                SeqRegRegFunct7.SLL: "SLL",
                SeqRegRegFunct7.MULH: "MULH",
                SeqRegRegFunct7.MUL: "MUL",
            }
        elif funct3 == SeqRegRegFunct3.XOR:
            return "XOR"
        elif funct3 == SeqRegRegFunct3.SRL_SRA:
            switcher = {
                SeqRegRegFunct7.SRL: "SRL",
                SeqRegRegFunct7.SRA: "SRA",
            }
        elif funct3 == SeqRegRegFunct3.OR:
            return "OR"
        elif funct3 == SeqRegRegFunct3.AND:
            return "AND"
        else:
            return "N/A"

        return switcher.get(funct7, "N/A")


class SequencerInstruction(abc.ABC):
    """
    Sequencer instructions are standard RISC-V instructions with some exceptions:
    a) Some commands of the base instruction set are not implemented
    b) Some custom commands have been added for the purposes of quantum computing.
    """

    OPCODE_WIDTH = 7
    FUNCT3_WIDTH = 3
    FUNCT7_WIDTH = 7
    REGISTER_WIDTH = 5
    LOWER_IMMEDIATE_WIDTH = 12
    UPPER_IMMEDIATE_WIDTH = 20

    LOWER_IMM_MAX = (
        2 ** (LOWER_IMMEDIATE_WIDTH - 1)
    ) - 1  # Lower immediate 12 Bits - 1Bit Signed
    LOWER_IMM_MIN = -(2 ** (LOWER_IMMEDIATE_WIDTH - 1))

    UPPER_IMM_MAX = (
        2 ** (UPPER_IMMEDIATE_WIDTH - 1)
    ) - 1  # Upper immediate 20 Bits - 1Bit Signed
    UPPER_IMM_MIN = -(2 ** (UPPER_IMMEDIATE_WIDTH - 1))
    UPPER_IMM_MAX_UNSIGNED = 2**UPPER_IMMEDIATE_WIDTH

    def __init__(self, opc: SeqOpCode) -> None:
        self.op = opc

    @staticmethod
    def is_value_in_lower_immediate(val: int) -> bool:
        """
        Returns whether a value can be encoded in the lower immediate value (12 bit)
        """
        return (
            SequencerInstruction.LOWER_IMM_MIN
            <= val
            <= SequencerInstruction.LOWER_IMM_MAX
        )

    @staticmethod
    def is_value_in_unsigned_upper_immediate(val: int) -> bool:
        """
        Returns whether a value can be encoded in the upper immediate value
        """
        return SequencerInstruction.UPPER_IMM_MAX_UNSIGNED >= abs(val)

    @abstractmethod
    def get_riscv_instruction(self) -> int:
        """
        Returns the actual 32-bit code RISC-V instruction from this object.
        """
        raise NotImplementedError


_AnyFunct3 = TypeVar("_AnyFunct3")


class SeqITypeInst(SequencerInstruction, abc.ABC, Generic[_AnyFunct3]):
    """
    An I-type instruction is an instruction that holds two register values and one immediate value.
    The two register values are called the source and destination register.
    Furthermore, there are two functors encoded in the operation; a SeqRegImmFunct3 and a SeqRegImmFunct7.
    Together, they define the operation to perform.

    :param opc:
        The Op Code
    :param funct3:
        The first function that determines the operation
    :param dst_reg:
        The destination register
    :param register:
        The source register
    :param immediate:
        The immediate value
    :param funct7:
        The second function that determines the operation
    """

    def __init__(
        self,
        opc: SeqOpCode,
        funct3: _AnyFunct3,
        dst_reg: int = 0,
        register: int = 0,
        immediate: int = 0,
        funct7: SeqRegImmFunct7 = SeqRegImmFunct7.SRL,
    ):
        super().__init__(opc)
        self.dst_reg = dst_reg
        self.register = register
        self.funct3 = funct3
        self.immediate = immediate
        self.funct7 = funct7

    @staticmethod
    def QiOpToFunct3(operator: QiOp) -> SeqRegImmFunct3:
        funct3 = {
            QiOp.PLUS: SeqRegImmFunct3.ADD,
            QiOp.LSH: SeqRegImmFunct3.SLL,
            QiOp.XOR: SeqRegImmFunct3.XOR,
            QiOp.RSH: SeqRegImmFunct3.SR,
            QiOp.OR: SeqRegImmFunct3.OR,
            QiOp.AND: SeqRegImmFunct3.AND,
        }.get(operator)
        if funct3 is None:
            raise NotImplementedError(
                "Operator not defined for Register Immediate Instruction"
            )
        return funct3

    @staticmethod
    def QiOpToFunct7(operator: QiOp) -> SeqRegImmFunct7:
        switcher = {QiOp.RSH: SeqRegImmFunct7.SRA}
        return switcher.get(operator, SeqRegImmFunct7.SRL)  # SRL is 0

    def get_riscv_instruction(self) -> int:
        instruction = 0
        instruction |= self.op.value
        instruction |= (self.dst_reg & 0x1F) << SequencerInstruction.OPCODE_WIDTH
        instruction |= (self.funct3.value & 0x7) << (
            SequencerInstruction.OPCODE_WIDTH + SequencerInstruction.REGISTER_WIDTH
        )
        instruction |= (self.register & 0x1F) << (
            SequencerInstruction.OPCODE_WIDTH
            + SequencerInstruction.REGISTER_WIDTH
            + SequencerInstruction.FUNCT3_WIDTH
        )
        instruction |= (self.immediate & 0xFFF) << (
            SequencerInstruction.OPCODE_WIDTH
            + 2 * SequencerInstruction.REGISTER_WIDTH
            + SequencerInstruction.FUNCT3_WIDTH
        )

        if self.funct3 == SeqRegImmFunct3.SR:
            instruction |= self.funct7.value << (
                SequencerInstruction.OPCODE_WIDTH
                + 3 * SequencerInstruction.REGISTER_WIDTH
                + SequencerInstruction.FUNCT3_WIDTH
            )

        return instruction


class SeqRTypeInst(SequencerInstruction, abc.ABC):
    """
    An R-type instruction encodes two source registers and one destination register.
    This instruction is used to perform some calculation, encoded in the funct3 and funct7
    arguments, using these two registers and storing the result into the destination register

    :param opc:
        The Op-Code
    :param funct3:
        The first function used to determine the operation
    :param funct7:
        The second functino used to determine the operation
    :param dst_reg:
        The destination register
    :param reg1:
        The first register
    :param reg2:
        The second register
    """

    def __init__(
        self,
        opc: SeqOpCode,
        funct3: SeqRegRegFunct3,
        funct7: SeqRegRegFunct7,
        dst_reg=0,
        reg1=0,
        reg2=0,
    ):
        super().__init__(opc)
        self.dst_reg = dst_reg
        self.reg1 = reg1
        self.funct3 = funct3
        self.reg2 = reg2
        self.funct7 = funct7

    @staticmethod
    def QiOpToFunct3(operator: QiOp):
        funct3 = {
            QiOp.PLUS: SeqRegRegFunct3.ADD_SUB_MUL,
            QiOp.MINUS: SeqRegRegFunct3.ADD_SUB_MUL,
            QiOp.MULT: SeqRegRegFunct3.ADD_SUB_MUL,
            QiOp.LSH: SeqRegRegFunct3.SLL_MULH,
            QiOp.XOR: SeqRegRegFunct3.XOR,
            QiOp.RSH: SeqRegRegFunct3.SRL_SRA,
            QiOp.OR: SeqRegRegFunct3.OR,
            QiOp.AND: SeqRegRegFunct3.AND,
        }.get(operator)
        if funct3 is None:
            raise NotImplementedError(
                "Operator not defined for Register Register Instruction"
            )
        return funct3

    @staticmethod
    def QiOpToFunct7(operator: QiOp):
        switcher = {
            QiOp.PLUS: SeqRegRegFunct7.ADD,
            QiOp.MINUS: SeqRegRegFunct7.SUB,
            QiOp.MULT: SeqRegRegFunct7.MUL,
            QiOp.LSH: SeqRegRegFunct7.SLL,
            QiOp.XOR: SeqRegRegFunct7.XOR,
            QiOp.RSH: SeqRegRegFunct7.SRA,
            QiOp.OR: SeqRegRegFunct7.OR,
            QiOp.AND: SeqRegRegFunct7.AND,
        }
        funct7 = switcher.get(operator)
        if funct7 is None:
            raise NotImplementedError(
                "Operator not defined for Register Register instruction"
            )
        return funct7

    def get_riscv_instruction(self) -> int:
        instruction = 0
        instruction |= self.op.value
        instruction |= (self.dst_reg & 0x1F) << SequencerInstruction.OPCODE_WIDTH
        instruction |= (self.funct3.value & 0x7) << (
            SequencerInstruction.OPCODE_WIDTH + SequencerInstruction.REGISTER_WIDTH
        )
        instruction |= (self.reg1 & 0x1F) << (
            SequencerInstruction.OPCODE_WIDTH
            + SequencerInstruction.REGISTER_WIDTH
            + SequencerInstruction.FUNCT3_WIDTH
        )
        instruction |= (self.reg2 & 0x1F) << (
            SequencerInstruction.OPCODE_WIDTH
            + 2 * SequencerInstruction.REGISTER_WIDTH
            + SequencerInstruction.FUNCT3_WIDTH
        )
        instruction |= (self.funct7.value & 0x7F) << (
            SequencerInstruction.OPCODE_WIDTH
            + 3 * SequencerInstruction.REGISTER_WIDTH
            + SequencerInstruction.FUNCT3_WIDTH
        )

        return instruction


class SeqUTypeInst(SequencerInstruction, abc.ABC):
    """
    A U-Type instruction contains a destination register and an immediate value.
    It is mostly used for load instructions. In the context of the QiController,
    it is also used for wait, trigger and sync instructions.
    """

    def __init__(self, opc: SeqOpCode, dst_reg: int = 0, immediate: int = 0):
        super().__init__(opc)
        self.dst_reg = dst_reg
        self._immediate = immediate

    @property
    def immediate(self):
        return self._immediate

    @immediate.setter
    def immediate(self, imm):
        self._immediate = imm

    def get_riscv_instruction(self) -> int:
        instruction = 0
        instruction |= self.op.value
        instruction |= (self.dst_reg & 0x1F) << SequencerInstruction.OPCODE_WIDTH

        instruction |= ((self._immediate & 0xFFFFF000) >> 12) << (
            SequencerInstruction.OPCODE_WIDTH + SequencerInstruction.REGISTER_WIDTH
        )

        return instruction

    def __str__(self):
        op_name = {
            SeqOpCode.REG_RECEIVE: "rcv",
            SeqOpCode.LOAD_UPPER_IMM: "lui",
            SeqOpCode.WAIT_REG: "wtr",
            SeqOpCode.TRIG_WAIT_REG: "twr",
            SeqOpCode.CELL_SYNC: "sync",
        }[self.op]
        return f"{op_name} r{self.dst_reg}, {hex(self.immediate & 0xFFFFF000)}"


class SeqSTypeInst(SequencerInstruction):
    def __init__(
        self,
        opc: SeqOpCode,
        funct3,
        reg1,
        reg2,
        immediate: int = 0,
    ):
        super().__init__(opc)
        self.funct3 = funct3
        self.reg1 = reg1
        self.reg2 = reg2
        self.immediate = immediate

    def get_riscv_instruction(self) -> int:
        instruction = 0
        instruction |= self.op.value
        instruction |= (self.immediate & 0x1F) << SequencerInstruction.OPCODE_WIDTH
        instruction |= (self.funct3.value & 0x7) << (
            SequencerInstruction.OPCODE_WIDTH + SequencerInstruction.REGISTER_WIDTH
        )
        instruction |= (self.reg1 & 0x1F) << (
            SequencerInstruction.OPCODE_WIDTH
            + SequencerInstruction.REGISTER_WIDTH
            + SequencerInstruction.FUNCT3_WIDTH
        )
        instruction |= (self.reg2 & 0x1F) << (
            SequencerInstruction.OPCODE_WIDTH
            + 2 * SequencerInstruction.REGISTER_WIDTH
            + SequencerInstruction.FUNCT3_WIDTH
        )
        instruction |= ((self.immediate & 0xFE0) >> 5) << (
            SequencerInstruction.OPCODE_WIDTH
            + 3 * SequencerInstruction.REGISTER_WIDTH
            + SequencerInstruction.FUNCT3_WIDTH
        )

        return instruction

    def __str__(self) -> str:
        if self.funct3 == SeqExtSynchFunct3.START:
            return "end"
        if self.funct3 == SeqOpCode.SYNCH:
            op = "synch"
        elif self.funct3 in {SeqRegSendFunct3.Single, SeqRegSendFunct3.Multi}:
            op = "snd"
        elif self.funct3 == SeqMemFunct3.B:
            op = "sb"
        elif self.funct3 == SeqMemFunct3.H:
            op = "sh"
        elif self.funct3 == SeqMemFunct3.W:
            op = "sw"
        elif self.funct3 == SeqMemFunct3.BU:
            op = "sbu"
        elif self.funct3 == SeqMemFunct3.HU:
            op = "shu"
        else:
            raise AttributeError(f"funct3 {self.funct3} not a valid RISC-V operation")

        return f"{op} r{self.reg2}, {self.immediate}(r{self.reg1})"


class SeqBTypeInst(SequencerInstruction, abc.ABC):
    def __init__(
        self,
        opc: SeqOpCode,
        funct3,
        reg1,
        reg2,
        immediate: int = 0,
    ):
        super().__init__(opc)
        self.funct3 = funct3
        self.immediate = immediate
        self.reg1 = reg1
        self.reg2 = reg2

    @staticmethod
    def QiCondToFunct3(operator: QiOpCond):
        switcher = {
            QiOpCond.EQ: SeqBranchFunct3.BEQ,
            QiOpCond.NE: SeqBranchFunct3.BNE,
            QiOpCond.GT: SeqBranchFunct3.BLT,
            QiOpCond.LE: SeqBranchFunct3.BGE,
            QiOpCond.LT: SeqBranchFunct3.BLT,
            QiOpCond.GE: SeqBranchFunct3.BGE,
        }
        return switcher[operator]

    @staticmethod
    def get_register_operation_tuple(
        operator: QiOpCond, reg1: int, reg2: int
    ) -> tuple[SeqBranchFunct3, int, int]:
        """> and <= not implemented in hardware, so just switch operands and instead use <, respective >="""
        if operator in (QiOpCond.GT, QiOpCond.LE):
            reg1, reg2 = reg2, reg1

        return SeqBTypeInst.QiCondToFunct3(operator), reg1, reg2

    def get_riscv_instruction(self) -> int:
        """Does not represent actual B-Type Instruction, RISC-V only supports address sizes as multiples of 2"""
        instruction = 0
        instruction |= self.op.value
        instruction |= (
            (self.immediate & 0x400) >> 10
        ) << SequencerInstruction.OPCODE_WIDTH
        instruction |= (self.immediate & 0xF) << SequencerInstruction.OPCODE_WIDTH + 1
        instruction |= (self.funct3.value & 0x7) << (
            SequencerInstruction.OPCODE_WIDTH + SequencerInstruction.REGISTER_WIDTH
        )
        instruction |= (self.reg1 & 0x1F) << (
            SequencerInstruction.OPCODE_WIDTH
            + SequencerInstruction.REGISTER_WIDTH
            + SequencerInstruction.FUNCT3_WIDTH
        )
        instruction |= (self.reg2 & 0x1F) << (
            SequencerInstruction.OPCODE_WIDTH
            + 2 * SequencerInstruction.REGISTER_WIDTH
            + SequencerInstruction.FUNCT3_WIDTH
        )
        instruction |= ((self.immediate & 0x3F0) >> 4) << (
            SequencerInstruction.OPCODE_WIDTH
            + 3 * SequencerInstruction.REGISTER_WIDTH
            + SequencerInstruction.FUNCT3_WIDTH
        )
        instruction |= ((self.immediate & 0x800) >> 11) << (
            SequencerInstruction.OPCODE_WIDTH
            + 3 * SequencerInstruction.REGISTER_WIDTH
            + SequencerInstruction.FUNCT3_WIDTH
            + 6
        )

        return instruction


class SeqRegImmediateInst(SeqITypeInst[SeqRegImmFunct3]):
    """
    A register-immediate instruction is an instruction that computes some value based on the contents of some register
    and some immediate value. The result is being stored into a different register.

    Assembly format
    ===============
    <op> <dest>, <source>, <imm>

    <op>: The operation
    <dest>: The destination register
    <source>: The source register
    <imm>: The immediate (constant) value

    Allowed operations
    ==================
    The following operations are supported:
    addi: Adds two numbers
    xori: computes bitwise xor
    ori: computes bitwise or
    andi: computes bitwise and
    sll: Shifts the number to the left by an amount encoded in the immediate
    sra: Shifts the numer to the right while sign-extending the bit
    sla: Shifts the number to the right while ignoring the sign bit

    Examples
    ========
    Let's assume that register r2 holds the value 5. The instruction
    addi r1, r2, 10
    would add 10 to the value of register r2 and store that in register r1.
    After this instruction, register r1 holds the value 15.

    :param operator: The operation to perform
    :param dst_reg: The address of the register used to store the result
    :param register: The source register
    :param immediate: The immediate value
    """

    def __init__(
        self,
        operator: QiOp,
        dst_reg: int = 0,
        register: int = 0,
        immediate: int = 0,
    ) -> None:
        funct3 = SeqITypeInst.QiOpToFunct3(operator)
        funct7 = SeqITypeInst.QiOpToFunct7(operator)
        super().__init__(
            SeqOpCode.REG_IMM, funct3, dst_reg, register, immediate, funct7
        )

    def __str__(self):
        if self.funct3 == SeqRegImmFunct3.SR:
            op_name = {SeqRegImmFunct7.SRA: "sra", SeqRegImmFunct7.SRL: "srl"}[
                self.funct7
            ]
        else:
            op_name = {
                SeqRegImmFunct3.ADD: "addi",
                SeqRegImmFunct3.SLL: "sll",
                SeqRegImmFunct3.XOR: "xori",
                SeqRegImmFunct3.OR: "ori",
                SeqRegImmFunct3.AND: "andi",
            }[self.funct3]

        return f"{op_name} r{self.dst_reg}, r{self.register}, {hex(self.immediate & 0xFFF)}"


class SeqCellRegSend(SeqSTypeInst):
    def __init__(
        self, send_reg: int = 0, sync_cell: int = 0, sync_reg: int = 0
    ) -> None:
        if not sync_reg:
            funct3 = SeqRegSendFunct3.Single
        else:
            funct3 = SeqRegSendFunct3.Multi

        super().__init__(SeqOpCode.REG_SEND, funct3, send_reg, sync_reg, sync_cell)


class SeqCellRegReceive(SeqUTypeInst):
    def __init__(
        self,
        sender_cell: int = 0,
        dst_reg: int = 0,
        sync_cells: list[int] | None = None,
    ) -> None:
        sync_cells = sync_cells or []
        sync_cells.append(sender_cell)
        immediate = 0
        for x in sync_cells:
            immediate |= 1 << x
        immediate <<= 16
        immediate |= sender_cell << 12
        sync_cells.clear()
        super().__init__(SeqOpCode.REG_RECEIVE, dst_reg, immediate)

    def __str__(self):
        return f"rcv r{self.dst_reg}, {self.immediate}"


class SeqRegRegInst(SeqRTypeInst):
    def __init__(
        self, operator: QiOp, dst_reg: int = 0, reg_1: int = 0, reg_2: int = 0
    ) -> None:
        funct3 = SeqRTypeInst.QiOpToFunct3(operator)
        funct7 = SeqRTypeInst.QiOpToFunct7(operator)
        super().__init__(
            SeqOpCode.REGISTER_REGISTER, funct3, funct7, dst_reg, reg_1, reg_2
        )

    def __str__(self):
        if self.funct3 == SeqRegRegFunct3.ADD_SUB_MUL:
            op_name = {
                SeqRegRegFunct7.ADD: "add",
                SeqRegRegFunct7.SUB: "sub",
                SeqRegRegFunct7.MUL: "mul",
            }[self.funct7]
        elif self.funct3 == SeqRegRegFunct3.SLL_MULH:
            op_name = {
                SeqRegRegFunct7.SLL: "sll",
                SeqRegRegFunct7.MULH: "mulh",
                SeqRegRegFunct7.MUL: "mul",
            }[self.funct7]
        elif self.funct3 == SeqRegRegFunct3.XOR:
            op_name = "xor"
        elif self.funct3 == SeqRegRegFunct3.SRL_SRA:
            op_name = {
                SeqRegRegFunct7.SRL: "srl",
                SeqRegRegFunct7.SRA: "sra",
            }[self.funct7]
        elif self.funct3 == SeqRegRegFunct3.OR:
            op_name = "or"
        elif self.funct3 == SeqRegRegFunct3.AND:
            op_name = "and"
        else:
            raise AttributeError(
                f"Invalid combination of funct3/funct7: {self.funct3}, {self.funct7}"
            )
        return f"{op_name} r{self.dst_reg}, r{self.reg1}, r{self.reg2}"


class SeqLoadUpperImm(SeqUTypeInst):
    """
    Loads the immediate value into the upper part of a register
    """

    def __init__(self, dst_reg: int = 0, immediate: int = 0) -> None:
        super().__init__(SeqOpCode.LOAD_UPPER_IMM, dst_reg, immediate)

    def __str__(self):
        return f"lui r{self.dst_reg}, {self.immediate}"


class SeqBranch(SeqBTypeInst):
    """
    Branch instructions are used to conditionally jump over a sequence of code.
    """

    def __init__(self, operator, reg1: int, reg2: int, rel_jump: int = 0) -> None:
        op, reg1, reg2 = super().get_register_operation_tuple(operator, reg1, reg2)
        super().__init__(SeqOpCode.BRANCH, op, reg1, reg2, rel_jump)

    def set_jump_value(self, jump_val: int):
        self.immediate = jump_val

    def __str__(self):
        op_name = {
            SeqBranchFunct3.BEQ: "beq",
            SeqBranchFunct3.BLT: "blt",
            SeqBranchFunct3.BGE: "bge",
            SeqBranchFunct3.BNE: "bne",
            SeqBranchFunct3.BGEU: "bgeu",
            SeqBranchFunct3.BLTU: "bltu",
        }[self.funct3]
        return f"{op_name} r{self.reg1}, r{self.reg2}, {hex(self.immediate)}"


class SeqJump(SequencerInstruction):
    """Does not represent actual J-Type instruction, RISC-V only supports address sizes as multiples of 2"""

    def __init__(self, rel_jump: int = 0) -> None:
        super().__init__(SeqOpCode.JUMP)
        self.jump_val = rel_jump

    def get_riscv_instruction(self) -> int:
        instruction = 0
        instruction |= self.op.value
        instruction |= (
            (self.jump_val & 0x7F800) >> 11
        ) << SequencerInstruction.OPCODE_WIDTH + SequencerInstruction.REGISTER_WIDTH
        instruction |= (
            (self.jump_val & 0x400) >> 10
        ) << SequencerInstruction.OPCODE_WIDTH + SequencerInstruction.REGISTER_WIDTH + 8
        instruction |= (
            self.jump_val & 0x3FF
        ) << SequencerInstruction.OPCODE_WIDTH + SequencerInstruction.REGISTER_WIDTH + 9
        instruction |= (
            ((self.jump_val & 0x80000) >> 19)
            << SequencerInstruction.OPCODE_WIDTH
            + SequencerInstruction.REGISTER_WIDTH
            + 19
        )

        return instruction

    def __str__(self) -> str:
        return f"j {hex(self.jump_val)}"


class SeqWaitImm(SeqUTypeInst):
    def __init__(self, duration: int = 0) -> None:
        super().__init__(opc=SeqOpCode.WAIT_IMM, immediate=((duration & 0xFFFFF) << 12))

    @property
    def immediate(self):
        return self._immediate >> 12

    def __str__(self):
        return f"wti {hex(self.immediate & 0x000FFFFF)}"


class SeqWaitRegister(SeqUTypeInst):
    def __init__(self, reg: int) -> None:
        super().__init__(opc=SeqOpCode.WAIT_REG, dst_reg=reg)


class SeqTriggerWaitRegister(SeqUTypeInst):
    def __init__(self, reg: int) -> None:
        super().__init__(opc=SeqOpCode.TRIG_WAIT_REG, dst_reg=reg)


class SeqTrigger(SeqUTypeInst):
    def __init__(
        self,
        module0: int = 0,
        module1: int = 0,
        module2: int = 0,
        module3: int = 0,
        module4: int = 0,
        module5: int = 0,
        sync=False,
        reset=False,
    ) -> None:
        self._trig_indices = [module0, module1, module2, module3, module4, module5]

        immediate = 0
        immediate |= (reset & 0x1) << 12
        immediate |= (sync & 0x1) << 14
        immediate |= (module0 & 0xF) << 16
        immediate |= (module1 & 0xF) << 20
        immediate |= (module2 & 0xF) << 22
        immediate |= (module3 & 0x3) << 26
        immediate |= (module4 & 0x3) << 28
        immediate |= (module5 & 0x3) << 30
        super().__init__(opc=SeqOpCode.TRIGGER, immediate=immediate)

    def __str__(self) -> str:
        return "tr " + ", ".join(map(hex, self._trig_indices))


class SeqCellSync(SeqUTypeInst):
    def __init__(self, cells: list):
        assert (
            17 > len(cells) > 1
        ), "Number of cells to be synchronized is out of range."
        immediate = 0
        for x in cells:
            immediate |= 1 << x
        immediate <<= 16
        super().__init__(opc=SeqOpCode.CELL_SYNC, immediate=immediate)


class SeqEnd(SeqSTypeInst):
    def __init__(self) -> None:
        super().__init__(SeqOpCode.SYNCH, SeqExtSynchFunct3.START, 0, 0, 0)


class SeqAwaitQubitState(SeqITypeInst[SeqExtSynchFunct3]):
    def __init__(
        self,
        cell: int = 0,
        dst: int = 0,
    ) -> None:
        super().__init__(
            SeqOpCode.SYNCH,
            SeqExtSynchFunct3.QUBIT_STATE,
            dst,
            0,
            cell,
            SeqRegImmFunct7(0),
        )

    def __str__(self):
        return f"wtq r{self.dst_reg}, {self.immediate}"


class SeqStore(SeqSTypeInst):
    """Store Sequencer instruction.

    :param src: The register address which contains the value to be stored.
    :param base: The register address which contains the destination address.
    :param offset: Constant offset added to the destination address. Defaults to 0.
    """

    def __init__(
        self,
        src: int,
        base: int,
        offset: int = 0,
    ):
        assert SequencerInstruction.is_value_in_lower_immediate(
            offset
        ), "Invalid offset ({offset}) to store instruction."

        # The hardware currently only supports 32 bit memory accesses.
        super().__init__(
            SeqOpCode.STORE, SeqMemFunct3.get_from_width(32, False), base, src, offset
        )

    @property
    def base_reg(self):
        return self.reg1

    @property
    def src_reg(self):
        return self.reg2


class SeqLoad(SeqITypeInst[SeqMemFunct3]):
    """
    Load instructions load a word, half-word or byte from memory into a register.
    Furthermore, for half words and bytes, the value being loaded into a register can be sign-extended or
    non sign-extended.

    Assembly format
    ===============
    <op> <dest>, <imm>(<source>)

    <op>: The operation
    <dest>: The destination register
    <source>: The source register
    <imm>: The immediate (constant) value

    Examples
    ========
    Suppose the following memory layout with contents:

         24   16   8    0
        +----|----|----|----+
    0x0 |                   |
    ... |        ...        |
    0xA | AF | 2F | 0A | D7 |
    ... |                   |
    ... | remaining memory  |
        +----|----|----|----+

    Also suppose that r2 contains the value 0xA (which will be used as address).
    The command
    lw r5, 0(r2)
    loads the 32-bit word 0xAF2F0AD7 into register r5. Similarly, the command
    lh r5, 0(r2)
    loads the 16-bit word 0x0AD7 into register r5.
    The remaining bits of r5 are set to zero as 0x0AD7 does not need to be sign-extended.
    However, the command
    lb r5, 0(r2)
    loads the value 0xD7 and sign-extends it to 0xFFFFFFD7 as 0xD7 is a negative integer
    if interpreted as signed value.
    Note that for the variant
    lbu r5, 0(r2) would load the value 0xD7 as-is into register r5, padding the remaining 24 bits
    with zeroes

    Operations
    ==========
    lw, lh, lb: Load the word, half-word or byte from memory and sign-extend where applicable
    lhu, lbu: Load the half-word or byte from memory and do not sign-extend.

    :param dst:
        The register address which will contain the loaded value.
    :param base:
        The register address which contains the source address.
    :param offset:
        Constant offset added to the source address. Defaults to 0.
    """

    def __init__(
        self,
        dst: int,
        base: int,
        offset: int = 0,
    ):
        assert SequencerInstruction.is_value_in_lower_immediate(
            offset
        ), "Invalid offset ({offset}) to load instruction."

        # The hardware currently only supports 32 bit memory accesses.
        super().__init__(
            SeqOpCode.LOAD,
            SeqMemFunct3.get_from_width(32, False),
            dst,
            base,
            offset,
        )

    @property
    def base_reg(self):
        return self.register

    def __str__(self):
        op_name = {
            SeqMemFunct3.W: "lw",
            SeqMemFunct3.H: "lh",
            SeqMemFunct3.B: "lb",
            SeqMemFunct3.BU: "lbu",
            SeqMemFunct3.HU: "lhu",
        }[self.funct3]

        return f"{op_name} r{self.dst_reg}, {self.immediate}(r{self.base_reg})"
