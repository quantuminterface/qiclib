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
import re
from abc import abstractmethod
from enum import Enum
from typing import Generic, TypeVar

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

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

    @classmethod
    def from_str(cls, val: str) -> Self:
        """
        Parse an instruction string and return the appropriate instruction instance.

        :param val:
            String representation of the instruction
        :return:
            An instance of the appropriate instruction class
        :raises ValueError: If the instruction cannot be parsed unambiguously
        """
        val = val.strip()

        op_name = val.split(None, maxsplit=1)[0]

        # Route to the appropriate parser
        parsers = {
            # Reg-Immediate instructions
            "addi": SeqRegImmediateInst.from_str,
            "sll": SeqRegImmediateInst.from_str,
            "xori": SeqRegImmediateInst.from_str,
            "ori": SeqRegImmediateInst.from_str,
            "andi": SeqRegImmediateInst.from_str,
            "sra": SeqRegImmediateInst.from_str,
            "srl": SeqRegImmediateInst.from_str,
            # Reg-Reg instructions
            "add": SeqRegRegInst.from_str,
            "sub": SeqRegRegInst.from_str,
            "mul": SeqRegRegInst.from_str,
            "xor": SeqRegRegInst.from_str,
            "or": SeqRegRegInst.from_str,
            "and": SeqRegRegInst.from_str,
            # Branch instructions
            "beq": SeqBranch.from_str,
            "bne": SeqBranch.from_str,
            "blt": SeqBranch.from_str,
            "bge": SeqBranch.from_str,
            "bltu": SeqBranch.from_str,
            "bgeu": SeqBranch.from_str,
            # Jump instruction
            "j": SeqJump.from_str,
            # Load upper immediate
            "lui": SeqLoadUpperImm.from_str,
            # Wait instructions
            "wti": SeqWaitImm.from_str,
            "wtr": SeqWaitRegister.from_str,
            "twr": SeqTriggerWaitRegister.from_str,
            # Trigger instruction
            "tr": SeqTrigger.from_str,
            # Sync instructions
            "sync": SeqCellSync.from_str,
            "end": SeqEnd.from_str,
            # Wait qubit state
            "wtq": SeqAwaitQubitState.from_str,
            # Load instructions
            "lw": SeqLoad.from_str,
            "lh": SeqLoad.from_str,
            "lb": SeqLoad.from_str,
            "lhu": SeqLoad.from_str,
            "lbu": SeqLoad.from_str,
            # Store instructions
            "sb": SeqStore.from_str,
            "sh": SeqStore.from_str,
            "sw": SeqStore.from_str,
            "sbu": SeqStore.from_str,
            "shu": SeqStore.from_str,
            # Send/Receive
            "snd": SeqCellRegSend.from_str,
            "rcv": SeqCellRegReceive.from_str,
        }

        if op_name not in parsers:
            raise ValueError(f"Unknown instruction: {op_name}")

        return parsers[op_name](val)

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
        pass

    @staticmethod
    def nop() -> SequencerInstruction:
        """
        Returns a NOP instruction
        """
        return SeqRegImmediateInst(QiOp.PLUS, 0, 0, 0)


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

    def __eq__(self, value):
        if not isinstance(value, self.__class__):
            return False
        return (
            self.op == value.op
            and self.dst_reg == value.dst_reg
            and self.register == value.register
            and self.funct3 == value.funct3
            and self.immediate == value.immediate
            and self.funct7 == value.funct7
        )

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

    def __eq__(self, value):
        if not isinstance(value, self.__class__):
            return False
        return (
            self.op == value.op
            and self.dst_reg == value.dst_reg
            and self.reg1 == value.reg1
            and self.funct3 == value.funct3
            and self.reg2 == value.reg2
            and self.funct7 == value.funct7
        )

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

    def __eq__(self, value):
        if not isinstance(value, self.__class__):
            return False
        return (
            self.op == value.op
            and self.dst_reg == value.dst_reg
            and self._immediate == value._immediate
        )

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

    def __eq__(self, value):
        if not isinstance(value, self.__class__):
            return False
        return (
            self.op == value.op
            and self.funct3 == value.funct3
            and self.reg1 == value.reg1
            and self.reg2 == value.reg2
            and self.immediate == value.immediate
        )

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

    def __eq__(self, value):
        if not isinstance(value, self.__class__):
            return False
        return (
            self.op == value.op
            and self.funct3 == value.funct3
            and self.reg1 == value.reg1
            and self.reg2 == value.reg2
            and self.immediate == value.immediate
        )

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

    @classmethod
    def from_str(cls, val: str) -> SeqRegImmediateInst:
        """Parse a register-immediate instruction from its string representation."""
        # Format: <op> r<dst>, r<src>, <imm>
        match = re.match(r"(\w+)\s+r(\d+),\s*r(\d+),\s*(0x[0-9a-fA-F]+|-?\d+)", val)
        if not match:
            raise ValueError(f"Cannot parse register-immediate instruction: {val}")

        op_name, dst_str, src_str, imm_str = match.groups()
        op_name = op_name.lower()

        # Map op name to QiOp
        op_map = {
            "addi": QiOp.PLUS,
            "sll": QiOp.LSH,
            "xori": QiOp.XOR,
            "ori": QiOp.OR,
            "andi": QiOp.AND,
            "sra": QiOp.RSH,
            "srl": QiOp.RSH,
        }

        if op_name not in op_map:
            raise ValueError(f"Unknown register-immediate operation: {op_name}")

        operator = op_map[op_name]
        dst_reg = int(dst_str)
        src_reg = int(src_str)
        immediate = int(imm_str, 0)  # 0 base auto-detects hex/decimal

        return cls(operator, dst_reg, src_reg, immediate)


class SeqCellRegSend(SeqSTypeInst):
    def __init__(
        self, send_reg: int = 0, sync_cell: int = 0, sync_reg: int = 0
    ) -> None:
        if not sync_reg:
            funct3 = SeqRegSendFunct3.Single
        else:
            funct3 = SeqRegSendFunct3.Multi

        super().__init__(SeqOpCode.REG_SEND, funct3, send_reg, sync_reg, sync_cell)

    @classmethod
    def from_str(cls, val: str) -> SeqCellRegSend:
        raise NotImplementedError(cls.__name__)


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
        super().__init__(SeqOpCode.REG_RECEIVE, dst_reg, immediate)

    def __str__(self):
        return f"rcv r{self.dst_reg}, {self.immediate}"

    @classmethod
    def from_str(cls, val: str) -> SeqCellRegReceive:
        raise NotImplementedError(cls.__name__)


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

    @classmethod
    def from_str(cls, val: str) -> SeqRegRegInst:
        """Parse a register-register instruction from its string representation."""
        # Format: <op> r<dst>, r<reg1>, r<reg2>
        match = re.match(r"(\w+)\s+r(\d+),\s*r(\d+),\s*r(\d+)", val)
        if not match:
            raise ValueError(f"Cannot parse register-register instruction: {val}")

        op_name, dst_str, reg1_str, reg2_str = match.groups()
        op_name = op_name.lower()

        # Map op name to QiOp
        op_map = {
            "add": QiOp.PLUS,
            "sub": QiOp.MINUS,
            "mul": QiOp.MULT,
            "sll": QiOp.LSH,
            "xor": QiOp.XOR,
            "sra": QiOp.RSH,
            "srl": QiOp.RSH,
            "or": QiOp.OR,
            "and": QiOp.AND,
            "mulh": QiOp.MULT,
        }

        if op_name not in op_map:
            raise ValueError(f"Unknown register-register operation: {op_name}")

        operator = op_map[op_name]
        dst_reg = int(dst_str)
        reg1 = int(reg1_str)
        reg2 = int(reg2_str)

        return cls(operator, dst_reg, reg1, reg2)


class SeqLoadUpperImm(SeqUTypeInst):
    """
    Loads the immediate value into the upper part of a register
    """

    def __init__(self, dst_reg: int = 0, immediate: int = 0) -> None:
        super().__init__(SeqOpCode.LOAD_UPPER_IMM, dst_reg, immediate)

    def __str__(self):
        return f"lui r{self.dst_reg}, {hex(self.immediate)}"

    @classmethod
    def from_str(cls, val: str) -> SeqLoadUpperImm:
        """Parse a load upper immediate instruction from its string representation."""
        # Format: lui r<dst>, <imm>
        match = re.match(r"lui\s+r(\d+),\s*(0x[0-9a-fA-F]+|-?\d+)", val)
        if not match:
            raise ValueError(f"Cannot parse load upper immediate instruction: {val}")

        dst_str, imm_str = match.groups()
        dst_reg = int(dst_str)
        immediate = int(imm_str, 0)

        return cls(dst_reg, immediate)


class SeqBranch(SeqBTypeInst):
    """
    Branch instructions are used to conditionally jump over a sequence of code.
    """

    def __init__(
        self, operator: QiOpCond, reg1: int, reg2: int, rel_jump: int = 0
    ) -> None:
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

    @classmethod
    def from_str(cls, val: str) -> SeqBranch:
        """Parse a branch instruction from its string representation."""
        # Format: <op> r<reg1>, r<reg2>, <offset>
        match = re.match(r"(\w+)\s+r(\d+),\s*r(\d+),\s*(0x[0-9a-fA-F]+|-?\d+)", val)
        if not match:
            raise ValueError(f"Cannot parse branch instruction: {val}")

        op_name, reg1_str, reg2_str, offset_str = match.groups()
        op_name = op_name.lower()

        # Map op name to QiOpCond
        op_map = {
            "beq": QiOpCond.EQ,
            "bne": QiOpCond.NE,
            "blt": QiOpCond.LT,
            "bge": QiOpCond.GE,
            "bltu": QiOpCond.LT,
            "bgeu": QiOpCond.GE,
        }

        if op_name not in op_map:
            raise ValueError(f"Unknown branch operation: {op_name}")

        operator = op_map[op_name]
        reg1 = int(reg1_str)
        reg2 = int(reg2_str)
        offset = int(offset_str, 0)

        inst = cls(operator, reg1, reg2)
        inst.set_jump_value(offset)
        return inst


class SeqJump(SequencerInstruction):
    """Does not represent actual J-Type instruction, RISC-V only supports address sizes as multiples of 2"""

    def __init__(self, rel_jump: int = 0) -> None:
        super().__init__(SeqOpCode.JUMP)
        self.jump_val = rel_jump

    def __eq__(self, value):
        if not isinstance(value, self.__class__):
            return False
        return self.op == value.op and self.jump_val == value.jump_val

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

    @classmethod
    def from_str(cls, val: str) -> SeqJump:
        """Parse a jump instruction from its string representation."""
        # Format: j <offset>
        match = re.match(r"j\s+(-?0x[0-9a-fA-F]+|-?\d+)", val)
        if not match:
            raise ValueError(f"Cannot parse jump instruction: {val}")

        offset_str = match.group(1)
        offset = int(offset_str, 0)

        return cls(offset)


class SeqWaitImm(SeqUTypeInst):
    def __init__(self, duration: int = 0) -> None:
        super().__init__(opc=SeqOpCode.WAIT_IMM, immediate=((duration & 0xFFFFF) << 12))

    @property
    def immediate(self):
        return self._immediate >> 12

    def __str__(self):
        return f"wti {hex(self.immediate & 0x000FFFFF)}"

    @classmethod
    def from_str(cls, val: str) -> SeqWaitImm:
        """Parse a wait immediate instruction from its string representation."""
        # Format: wti <duration>
        match = re.match(r"wti\s+(0x[0-9a-fA-F]+|-?\d+)", val)
        if not match:
            raise ValueError(f"Cannot parse wait immediate instruction: {val}")

        duration_str = match.group(1)
        duration = int(duration_str, 0)

        return cls(duration)


class SeqWaitRegister(SeqUTypeInst):
    def __init__(self, reg: int) -> None:
        super().__init__(opc=SeqOpCode.WAIT_REG, dst_reg=reg)

    @classmethod
    def from_str(cls, val: str) -> SeqWaitRegister:
        """Parse a wait register instruction from its string representation."""
        # Format: wtr r<reg>, <imm>
        match = re.match(r"wtr\s+r(\d+),", val)
        if not match:
            raise ValueError(f"Cannot parse wait register instruction: {val}")

        reg_str = match.group(1)
        reg = int(reg_str)

        return cls(reg)


class SeqTriggerWaitRegister(SeqUTypeInst):
    def __init__(self, reg: int) -> None:
        super().__init__(opc=SeqOpCode.TRIG_WAIT_REG, dst_reg=reg)

    @classmethod
    def from_str(cls, val: str) -> SeqTriggerWaitRegister:
        """Parse a trigger wait register instruction from its string representation."""
        # Format: twr r<reg>, <imm>
        match = re.match(r"twr\s+r(\d+),", val)
        if not match:
            raise ValueError(f"Cannot parse trigger wait register instruction: {val}")

        reg_str = match.group(1)
        reg = int(reg_str)

        return cls(reg)


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

    @classmethod
    def from_str(cls, val: str) -> SeqTrigger:
        """Parse a trigger instruction from its string representation."""
        # Format: tr <0x...>, <0x...>, <0x...>, <0x...>, <0x...>, <0x...>
        match = re.match(
            r"tr\s+(0x[0-9a-fA-F]+|-?\d+),\s*(0x[0-9a-fA-F]+|-?\d+),\s*"
            r"(0x[0-9a-fA-F]+|-?\d+),\s*(0x[0-9a-fA-F]+|-?\d+),\s*"
            r"(0x[0-9a-fA-F]+|-?\d+),\s*(0x[0-9a-fA-F]+|-?\d+)",
            val,
        )
        if not match:
            raise ValueError(f"Cannot parse trigger instruction: {val}")

        modules = [int(m, 0) for m in match.groups()]
        # SeqTrigger signature: (module0, module1, module2, module3, module4, module5, sync=False, reset=False)
        return cls(*modules, sync=False, reset=False)


class SeqCellSync(SeqUTypeInst):
    def __init__(self, cells: list):
        assert 17 > len(cells) > 1, (
            "Number of cells to be synchronized is out of range."
        )
        immediate = 0
        for x in cells:
            immediate |= 1 << x
        immediate <<= 16
        super().__init__(opc=SeqOpCode.CELL_SYNC, immediate=immediate)

    @classmethod
    def from_str(cls, val: str) -> SeqCellSync:
        """Parse a cell sync instruction from its string representation."""
        # Format: sync r<dst>, <imm>
        match = re.match(r"sync\s+r(\d+),\s*(0x[0-9a-fA-F]+|-?\d+)", val)
        if not match:
            raise ValueError(f"Cannot parse cell sync instruction: {val}")

        # Extract cells from the immediate value
        imm_str = match.group(2)
        immediate = int(imm_str, 0)

        # The immediate is stored with cells shifted left 16 bits
        cell_bits = immediate >> 16
        cells = []
        for i in range(32):
            if cell_bits & (1 << i):
                cells.append(i)

        if not cells or len(cells) < 2:
            raise ValueError(f"Invalid cell sync instruction: {val}")

        return cls(cells)


class SeqEnd(SeqSTypeInst):
    def __init__(self) -> None:
        super().__init__(SeqOpCode.SYNCH, SeqExtSynchFunct3.START, 0, 0, 0)

    @classmethod
    def from_str(cls, val: str) -> SeqEnd:
        """Parse an end instruction from its string representation."""
        # Format: end
        if not re.match(r"end\s*$", val):
            raise ValueError(f"Cannot parse end instruction: {val}")
        return cls()


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

    @classmethod
    def from_str(cls, val: str) -> SeqAwaitQubitState:
        """Parse a wait qubit state instruction from its string representation."""
        # Format: wtq r<dst>, <cell>
        match = re.match(r"wtq\s+r(\d+),\s*(\d+|-?0x[0-9a-fA-F]+)", val)
        if not match:
            raise ValueError(f"Cannot parse wait qubit state instruction: {val}")

        dst_str, cell_str = match.groups()
        dst = int(dst_str)
        cell = int(cell_str, 0)

        return cls(cell, dst)


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
        assert SequencerInstruction.is_value_in_lower_immediate(offset), (
            "Invalid offset ({offset}) to store instruction."
        )

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

    @classmethod
    def from_str(cls, val: str) -> SeqStore:
        """Parse a store instruction from its string representation."""
        # Format: <op> r<src>, <offset>(r<base>)
        match = re.match(
            r"(sb|sh|sw|sbu|shu)\s+r(\d+),\s*(-?\d+|-?0x[0-9a-fA-F]+)\(r(\d+)\)", val
        )
        if not match:
            raise ValueError(f"Cannot parse store instruction: {val}")

        op_name, src_str, offset_str, base_str = match.groups()
        if op_name != "sw":
            raise NotImplementedError("Only store word implemented")
        src = int(src_str)
        offset = int(offset_str, 0)
        base = int(base_str)

        return cls(src, base, offset)


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
        assert SequencerInstruction.is_value_in_lower_immediate(offset), (
            "Invalid offset ({offset}) to load instruction."
        )

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

    @classmethod
    def from_str(cls, val: str) -> SeqLoad:
        """Parse a load instruction from its string representation."""
        # Format: <op> r<dst>, <offset>(r<base>)
        match = re.match(
            r"(lw|lh|lb|lhu|lbu)\s+r(\d+),\s*(-?\d+|-?0x[0-9a-fA-F]+)\(r(\d+)\)", val
        )
        if not match:
            raise ValueError(f"Cannot parse load instruction: {val}")

        _, dst_str, offset_str, base_str = match.groups()
        dst = int(dst_str)
        offset = int(offset_str, 0)
        base = int(base_str)

        return cls(dst, base, offset)
