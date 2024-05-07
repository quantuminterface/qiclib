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

from abc import abstractmethod
from typing import Tuple, Union
from enum import Enum
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
    The following are only applicable to load instructions and will sign extend the loaded value.
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


class SequencerInstruction:
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

    imm_type = Union[int]  # might include float in the future

    def __init__(self, OpCode: SeqOpCode) -> None:
        self.op = OpCode

    @staticmethod
    def is_value_in_lower_immediate(val: imm_type) -> bool:
        return (
            SequencerInstruction.LOWER_IMM_MIN
            <= val
            <= SequencerInstruction.LOWER_IMM_MAX
        )

    @staticmethod
    def is_value_in_unsigned_upper_immediate(val: imm_type) -> bool:
        return SequencerInstruction.UPPER_IMM_MAX_UNSIGNED >= abs(val)

    @abstractmethod
    def get_riscv_instruction(self) -> int:
        pass


class SeqITypeInst(SequencerInstruction):
    def __init__(
        self,
        OpCode: SeqOpCode,
        funct3: SeqRegImmFunct3,
        dst_reg=0,
        register=0,
        immediate=0,
        funct7: SeqRegImmFunct7 = SeqRegImmFunct7.SRL,
    ):
        super().__init__(OpCode)
        self.dst_reg = dst_reg
        self.register = register
        self.funct3 = funct3
        self.immediate = immediate
        self.funct7 = funct7

    @staticmethod
    def QiOpToFunct3(operator: QiOp):
        switcher = {
            QiOp.PLUS: SeqRegImmFunct3.ADD,
            QiOp.LSH: SeqRegImmFunct3.SLL,
            QiOp.XOR: SeqRegImmFunct3.XOR,
            QiOp.RSH: SeqRegImmFunct3.SR,
            QiOp.OR: SeqRegImmFunct3.OR,
            QiOp.AND: SeqRegImmFunct3.AND,
        }
        funct3 = switcher.get(operator)
        if funct3 is None:
            raise NotImplementedError(
                "Operator not defined for Register Immediate Instruction"
            )
        return funct3

    @staticmethod
    def QiOpToFunct7(operator: QiOp):
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

    def __str__(self):
        funct7 = ""
        if self.funct3 == SeqRegImmFunct3.SR:
            funct7 = ", funct7: " + self.funct7.name

        return (
            f"Op: {self.op.name}, dst: {str(self.dst_reg)}, funct3: {self.funct3.name}, rs1: {str(self.register)}"
            f", immediate: {hex(self.immediate & 0xFFF)} {funct7}\n"
        )


class SeqRTypeInst(SequencerInstruction):
    def __init__(
        self,
        OpCode: SeqOpCode,
        funct3: SeqRegRegFunct3,
        funct7: SeqRegRegFunct7,
        dst_reg=0,
        reg1=0,
        reg2=0,
    ):
        super().__init__(OpCode)
        self.dst_reg = dst_reg
        self.reg1 = reg1
        self.funct3 = funct3
        self.reg2 = reg2
        self.funct7 = funct7

    @staticmethod
    def QiOpToFunct3(operator: QiOp):
        switcher = {
            QiOp.PLUS: SeqRegRegFunct3.ADD_SUB_MUL,
            QiOp.MINUS: SeqRegRegFunct3.ADD_SUB_MUL,
            QiOp.MULT: SeqRegRegFunct3.ADD_SUB_MUL,
            QiOp.LSH: SeqRegRegFunct3.SLL_MULH,
            QiOp.XOR: SeqRegRegFunct3.XOR,
            QiOp.RSH: SeqRegRegFunct3.SRL_SRA,
            QiOp.OR: SeqRegRegFunct3.OR,
            QiOp.AND: SeqRegRegFunct3.AND,
        }
        funct3 = switcher.get(operator)
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

    def __str__(self):
        return (
            f"Op: {self.op.name}, dst: {str(self.dst_reg)}, funct3: {self.funct3.name}, rs1: {str(self.reg1)}"
            f", rs2: {str(self.reg2)}, funct7: {SeqRegRegFunct7.get_name(self.funct3, self.funct7)}\n"
        )


class SeqUTypeInst(SequencerInstruction):
    def __init__(
        self, OpCode: SeqOpCode, dst_reg=0, immediate: SequencerInstruction.imm_type = 0
    ):
        super().__init__(OpCode)
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
        return f"Op: {self.op.name}, dst: {str(self.dst_reg)}, immediate: {hex(self.immediate & 0xFFFFF000)}\n"


class SeqSTypeInst(SequencerInstruction):
    def __init__(
        self,
        OpCode: SeqOpCode,
        funct3,
        reg1,
        reg2,
        immediate: SequencerInstruction.imm_type = 0,
    ):
        super().__init__(OpCode)
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
        return (
            f"Op: {self.op.name}, funct3: {self.funct3.name}, rs1: {str(self.reg1)}, rs2: {str(self.reg2)}"
            f", immediate: {hex(self.immediate)}\n"
        )


class SeqBTypeInst(SequencerInstruction):
    def __init__(
        self,
        OpCode: SeqOpCode,
        funct3,
        reg1,
        reg2,
        immediate: SequencerInstruction.imm_type = 0,
    ):
        super().__init__(OpCode)
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
    ) -> Tuple[SeqBranchFunct3, int, int]:
        """> and <= not implemented in hardware, so just switch operands and instead use <, respective >="""
        if operator in (QiOpCond.GT, QiOpCond.LE):
            reg1, reg2 = reg2, reg1

        return (SeqBTypeInst.QiCondToFunct3(operator), reg1, reg2)

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

    def __str__(self) -> str:
        return (
            f"Op: {self.op.name}, funct3: {self.funct3.name}, rs1: {str(self.reg1)}, rs2: {str(self.reg2)}"
            f", immediate: {hex(self.immediate)}\n"
        )


class SeqRegImmediateInst(SeqITypeInst):
    def __init__(
        self,
        operator: QiOp,
        dst_reg: int = 0,
        register: int = 0,
        immediate: SequencerInstruction.imm_type = 0,
    ) -> None:
        funct3 = super().QiOpToFunct3(operator)
        funct7 = super().QiOpToFunct7(operator)
        super().__init__(
            SeqOpCode.REG_IMM, funct3, dst_reg, register, immediate, funct7
        )


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
        self, sender_cell: int = 0, dst_reg: int = 0, sync_cells: list = None
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


class SeqRegRegInst(SeqRTypeInst):
    def __init__(
        self, operator: QiOp, dst_reg: int = 0, reg_1: int = 0, reg_2: int = 0
    ) -> None:
        funct3 = super().QiOpToFunct3(operator)
        funct7 = super().QiOpToFunct7(operator)
        super().__init__(
            SeqOpCode.REGISTER_REGISTER, funct3, funct7, dst_reg, reg_1, reg_2
        )


class SeqLoadUpperImm(SeqUTypeInst):
    def __init__(
        self, dst_reg: int = 0, immediate: SequencerInstruction.imm_type = 0
    ) -> None:
        super().__init__(SeqOpCode.LOAD_UPPER_IMM, dst_reg, immediate)


class SeqBranch(SeqBTypeInst):
    def __init__(self, operator, reg1: int, reg2: int, rel_jump: int = 0) -> None:
        op_reg1_reg2 = super().get_register_operation_tuple(operator, reg1, reg2)
        super().__init__(
            SeqOpCode.BRANCH,
            op_reg1_reg2[0],
            op_reg1_reg2[1],
            op_reg1_reg2[2],
            rel_jump,
        )

    def set_jump_value(self, jump_val: int):
        self.immediate = jump_val


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
            ((self.jump_val & 0x400) >> 10)
            << SequencerInstruction.OPCODE_WIDTH
            + SequencerInstruction.REGISTER_WIDTH
            + 8
        )
        instruction |= (
            (self.jump_val & 0x3FF)
            << SequencerInstruction.OPCODE_WIDTH
            + SequencerInstruction.REGISTER_WIDTH
            + 9
        )
        instruction |= (
            ((self.jump_val & 0x80000) >> 19)
            << SequencerInstruction.OPCODE_WIDTH
            + SequencerInstruction.REGISTER_WIDTH
            + 19
        )

        return instruction

    def __str__(self) -> str:
        return f"Op: {self.op.name}, immediate: {hex(self.jump_val)}\n"


class SeqWaitImm(SeqUTypeInst):
    def __init__(self, duration: int = 0) -> None:
        super().__init__(
            OpCode=SeqOpCode.WAIT_IMM, immediate=((duration & 0xFFFFF) << 12)
        )

    @property
    def immediate(self):
        return self._immediate >> 12

    def __str__(self):
        return f"Op: {self.op.name}, dst: {str(self.dst_reg)}, immediate: {hex(self.immediate & 0x000FFFFF)}\n"


class SeqWaitRegister(SeqUTypeInst):
    def __init__(self, reg: int) -> None:
        super().__init__(OpCode=SeqOpCode.WAIT_REG, dst_reg=reg)


class SeqTriggerWaitRegister(SeqUTypeInst):
    def __init__(self, reg: int) -> None:
        super().__init__(OpCode=SeqOpCode.TRIG_WAIT_REG, dst_reg=reg)


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
        super().__init__(OpCode=SeqOpCode.TRIGGER, immediate=immediate)

    def __str__(self) -> str:
        return (
            f"Op: {self.op.name}, mod0: {hex(self._trig_indices[0])}, mod1: {hex(self._trig_indices[1])}"
            f", mod2: {hex(self._trig_indices[2])}, mod3: {hex(self._trig_indices[3])},  mod4: {hex(self._trig_indices[4])}\n"
        )


class SeqCellSync(SeqUTypeInst):
    def __init__(self, cells: list):
        assert (
            len(cells) < 17 and len(cells) > 1
        ), "Number of cells to be synchronized is out of range."
        immediate = 0
        for x in cells:
            immediate |= 1 << x
        immediate <<= 16
        super().__init__(OpCode=SeqOpCode.CELL_SYNC, immediate=immediate)


class SeqEnd(SeqSTypeInst):
    def __init__(self) -> None:
        super().__init__(SeqOpCode.SYNCH, SeqExtSynchFunct3.START, 0, 0, 0)


class SeqAwaitQubitState(SeqITypeInst):
    def __init__(
        self,
        cell: int = 0,
        dst: int = 0,
    ) -> None:
        super().__init__(
            SeqOpCode.SYNCH, SeqExtSynchFunct3.QUBIT_STATE, dst, 0, cell, 0
        )


class SeqStore(SeqSTypeInst):
    """Store Sequencer instruction.

    :param src: The register address which contains the value to be stored.
    :param base: The register address which contains the destination address.
    :param offset: Constant offset added to the destination address. Defaults to 0.
    :param width: Number of bits to be stored. Defaults to 32.
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


class SeqLoad(SeqITypeInst):
    def __init__(
        self,
        dst: int,
        base: int,
        offset: int = 0,
    ):
        """Load Sequencer instruction.

        :param dst: The register address which will contain the loaded value.
        :param base: The register address which contains the source address.
        :param offset: Constant offset added to the source address. Defaults to 0.
        :param width: Number of bits to be loaded. Defaults to 32.
        :param signed: Is the loaded value signed. Depending on this flag the loaded value is sign extended.
        """

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
