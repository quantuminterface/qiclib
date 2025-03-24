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
"""This script provides a class to easily generate code for the QiController sequencer."""

from __future__ import annotations

import binascii
import struct

import qiclib.packages.utility as util


class SequencerCodeBase:
    """Class to easily generate code for the QiController sequencer in an object-oriented manner.
    This base class provides hardware centric commands. If you want to just program the device,
    better use more high-level class SequencerCode.

    Return a SequencerCode object to program the QiController sequencer.

    :param pc_dict: An empty dictionary which will be populated with the references defined in
        this class, e.g. multiple experiments following after each other.
        These are key value pairs with the reference name and belonging program counter.
        This can be used to store different experiments inside the same SequencerCodeBase object.
    """

    def __init__(self, pc_dict: dict[str, int] | None = None) -> None:
        self.assembler: list[str] = []
        self.binary = bytearray()
        self._instruction_values: list[int] = []
        self.program_counter = 0
        self.pc_dict = pc_dict

    def tr(
        self, mod0=0, mod1=0, mod2=0, mod3=0, mod4=0, mod5=0, reset=False, sync=False
    ):
        """
        Triggers the modules with the given codes.
        Additionally, global triggers can be issued (reset and sync).

        TR = Trigger
        """

        self._check_trigger(mod0, "mod0")
        self._check_trigger(mod1, "mod1")
        self._check_trigger(mod2, "mod2")
        self._check_trigger(mod3, "mod3")
        self._check_trigger(mod4, "mod4")
        self._check_trigger(mod5, "mod5")

        if not isinstance(reset, bool) or not isinstance(sync, bool):
            raise ValueError("reset and sync parameter need to be boolean.")

        # Assembler: TR mod0, mod1, mod2, mod3, mod4, mod5, reset, sync
        self.assembler.append(
            f"tr {mod0}, {mod1}, {mod2}, {mod3}, {mod4}, {mod5}, {reset*1}, {sync*1}\n"
        )

        # Binary:
        #   0-6 OpCode (TRIGGER = 0x2)
        #   7-11 Rd (Unused)
        #   12-15 Global Trigger
        #       12 Reset
        #       13 Start Marker (Will only be issued by the sequencer itself)
        #       14 Sync
        #       15 (Unused)
        #   16-19 Mod0 Trigger
        #   20-21 Mod1 Trigger
        #   22-25 Mod2 Trigger
        #   26-27 Mod3 Trigger
        #   28-29 Mod4 Trigger
        #   30-31 Mod5 Trigger
        self._add_command_value(
            0b0000010  # opcode TRIGGER
            + (reset << 12)
            + (sync << 14)
            + (mod0 << 16)
            + (mod1 << 20)
            + (mod2 << 22)
            + (mod3 << 26)
            + (mod4 << 28)
            + (mod5 << 30)
        )

        return self

    def wti(self, clock_cycles=0):
        """
        Waits the given number of `clock_cycles` before continuing.

        WTI = Wait Immediate
        """

        if not isinstance(clock_cycles, int) or clock_cycles < 0:
            raise ValueError("Clock cycles to wait need to be a non-negative integer!")
        if clock_cycles >= 2**20:
            raise ValueError(
                "Cannot wait more than 2^20 clock cycles. Try WTR instead."
            )

        if clock_cycles == 0:
            # Skip the wait command (would take 1 clock cycle to execute)
            return self

        # Assembler: WTI cycles
        self.assembler.append(f"wti 0x{clock_cycles:03x}\n")

        # Binary:
        #   0-6 OpCode (WAIT_IMM = 0x4)
        #   7-11 Rd (Unused)
        #   12-31 Wait Cycles
        self._add_command_value(0b0000100 + (clock_cycles << 12))  # opcode WAIT_IMM

        return self

    def wtr(self, register=1, user_reg=True):
        """
        Waits the number of `clock_cycles` as defined in the given `register`.

        WTR = Wait Register
        """

        self._check_register(register, user=user_reg, no_zero=True)

        # Assembler: WTR register
        self.assembler.append(f"wtr {register}\n")

        # Binary:
        #   0-6 OpCode (WAIT_REG = 0x6)
        #   7-11 Rd: Register Address
        self._add_command_value(0b0000110 + (register << 7))  # opcode WAIT_REG

        return self

    def twr(self, register=1):
        """
        Waits the number of `clock_cycles` as defined in the given `register` decremented by 1,
        to account for Trigger instruction duration.

        TWR = Trigger Wait Register
        """

        self._check_register(register, user=True, no_zero=True)

        # Assembler: TWR register
        self.assembler.append(f"twr {register}\n")

        # Binary:
        #   0-6 OpCode (TRIG_WAIT_REG = 0xA)
        #   7-11 Rd: Register Address
        self._add_command_value(0b0001010 + (register << 7))  # opcode TRIG_WAIT_REG

        return self

    def tri(self, clock_cycles=1, mod0=0, mod1=0, mod2=0, mod3=0, mod4=0, mod5=0):
        """Triggers the modules with the given codes.
        Then waits the given number of `clock_cycles`.

        .. deprecated:: 0.0.2
            New sequencer has two separate commands for trigger (TR) and wait (WTI/WTR).
        """
        self.tr(mod0, mod1, mod2, mod3, mod4, mod5)
        if clock_cycles > 1:
            self.wti(clock_cycles - 1)
        return self

    def trr(self, reg=1, mod0=0, mod1=0, mod2=0, mod3=0, mod4=0, mod5=0):
        """Triggers the modules with the given codes.
        Then waits as long as the delay in the specified register `reg` states, decremented by 1,
        to account for trigger instruction duration.

        .. deprecated:: 0.0.2
            New sequencer has two separate commands for trigger (TR) and wait (WTI/WTR).
        """
        self.tr(mod0, mod1, mod2, mod3, mod4, mod5)
        self.twr(reg)
        return self

    def sts(self, save_register, mod0=False, mod1=False, mod2=False, mod3=False):
        """
        Waits for a trigger response from the triggerbus of the specified modules
        and stores it into the register `save_register`.

        STS = Synch Trigger and Store
        """

        self._check_register(save_register, no_zero=True)

        # Assembler STS register, mod0, mod1, mod2, mod3
        self.assembler.append(
            f"sts {save_register}, {mod0 * 1}, {mod1 * 1}, {mod2 * 1}, {mod3 * 1}\n"
        )

        self._add_command_value(
            0b0001000  # Opcode Synch
            + (save_register << 7)  # save in reg
            + (0b010 << 12)  # trigger response
            + (0b00000 << 15)  # rs1
            + (0b00000 << 20)  # rs2
            + (mod0 << 21)
            + (mod1 << 22)
            + (mod2 << 23)
            + (mod3 << 24)
        )

        return self

    def lui(self, register, value):
        """Loads the given value into the upper 20 bits of the given register.

        LUI = Load Upper Immediate
        """

        self._check_register(register, no_zero=True)

        if not isinstance(value, int) or value < 0 or value >= (1 << 20):
            raise ValueError("Value needs to be 20bit compatible.")

        # Assembler: LUI register, value
        self.assembler.append(f"lui {register}, 0x{value:05x}\n")

        self._add_command_value(
            0b0110111 + (register << 7) + (value << 12)  # Opcode LUI  # save in reg
        )

    def addi(self, save_register, register, value):
        """Adds the given value to the specified `register` and stores the result
        int the register `save_register`.

        ADDI = Add Immediate
        """

        self._check_register(save_register, no_zero=True)
        self._check_register(register)

        if not isinstance(value, int) or value < 0 or value >= (1 << 12):
            raise ValueError("Value needs to be 12bit compatible.")

        # Assembler: addi save_register, register, value
        self.assembler.append(f"addi {save_register}, {register}, 0x{value:05x}\n")

        self._add_command_value(
            0b0010011  # Opcode RegImm
            + (save_register << 7)  # save in reg
            + (0b000 << 12)  # add
            + (register << 15)  # reg
            + (value << 20)
        )

    def seti(self, reg, value, user_reg=True):
        """Pseudo instruction to load a 32bit `value` to register `reg`.

        If register 30 or 31 need to be used, set `user_reg` to False.
        """

        self._check_register(reg, user=user_reg, no_zero=True)

        upper_imm = self.get_upper_immediate(value)

        # Set upper 20 bit of register
        self.lui(reg, (upper_imm >> 12) & 0x000FFFFF)

        # Set lower 12 bit of register
        self.addi(reg, reg, value & 0x00000FFF)

    def beq(self, register1, register2, jump_offset):
        """
        Compares the content in the two registers and if they are equal the execution
        jumps to the instructions with the given offset.

        BEQ = Branch (if) Equal
        """

        self._check_register(register1)
        self._check_register(register2)

        if (
            not isinstance(jump_offset, int)
            or jump_offset < -1 * (1 << 11)
            or jump_offset >= (1 << 11)
        ):
            raise ValueError(
                f"Jump offset needs to be between -2048 and 2047, but was {jump_offset}"
            )

        # Assembler: BEQ register1, register2, jump_offset
        self.assembler.append(f"beq {register1}, {register2}, {jump_offset}\n")

        self._add_command_value(
            0b1100011  # Opcode Branch
            + (((jump_offset & 0x400) >> 10) << 7)
            + ((jump_offset & 0xF) << 8)
            + (0b000 << 12)  # equals
            + (register1 << 15)  # reg
            + (register2 << 20)  # reg
            + (((jump_offset & 0x3F0) >> 4) << 25)
            + (((jump_offset & 0x800) >> 11) << 31)
        )

    def bra(self, addr=0, mod0=None, mod1=None, mod2=None, mod3=None):
        """
        Branch command jumps to `addr` if given values match return values from the modules.

        .. deprecated:: 0.0.2
            New sequencer has different commands for comparison (BEQ) and awaiting responses (STS).
        """

        # Generate mask and values
        mod0_msk = 1 * (mod0 is not None)
        mod1_msk = 1 * (mod1 is not None)
        mod2_msk = 1 * (mod2 is not None)
        mod3_msk = 1 * (mod3 is not None)
        mod0 = mod0 or 0
        mod1 = mod1 or 0
        mod2 = mod2 or 0
        mod3 = mod3 or 0

        self._check_address(addr)
        self._check_branch_value(mod0, "mod0")
        self._check_branch_value(mod1, "mod1")
        self._check_branch_value(mod2, "mod2")
        self._check_branch_value(mod3, "mod3")

        register1 = 30  # reg1-29 are written to by DelayRegister
        register2 = 31

        # Load the values to compare to into register 1
        load_value = (mod3 << 12) + (mod2 << 8) + (mod1 << 4) + mod0
        self.seti(register1, load_value, user_reg=False)

        # Wait for Response from modules and store it in register2
        self.sts(
            save_register=register2,
            mod0=mod0_msk,
            mod1=mod1_msk,
            mod2=mod2_msk,
            mod3=mod3_msk,
        )

        # Compare the two registers in order to decide if to jump
        self.beq(register1, register2, addr - self.program_counter)

        return self

    def end(self, clock_cycles=0):
        """Last command of the experiment telling the QiController to wait until the qubit is relaxed.

        :param clock_cycles: Number of clock cycles to wait for the qubit to relax in the ground state.
        """

        if clock_cycles >= (1 << 32):
            raise ValueError("Number of clock_cycles must be smaller than 2^32.")

        reg2 = 31  # reg1-29 are written to by DelayRegister

        if clock_cycles >= (1 << 12):
            # Write clock_cycles to reg2
            self.seti(reg2, clock_cycles, user_reg=False)

            self.wtr(reg2, user_reg=False)
        else:
            self.wti(clock_cycles)

        # Assembler: end clock_cycles
        self.assembler.append("end \n")

        # End and wait for value saved in immediate
        self._add_command_value(
            0b0001000 + (0b00000 << 7) + (0b000 << 12)  # Opcode synch  # End
        )
        return self

    def get_next_program_counter(self):
        """Returns the program counter of the next command."""
        return self.program_counter

    def reference(self, name):
        """Creates an entry in the reference dictionary you can pass to the constructor
        with key *name* and the next program counter.
        """
        if self.pc_dict is None:
            raise ReferenceError(
                "You have to pass a reference dictionary on instantiation "
                + "if you want to use this feature!"
            )

        if name in self.pc_dict:
            raise ValueError(
                f'Dictionary key "{name}" already used. Please specify unique reference names'
            )

        self.pc_dict[name] = self.get_next_program_counter()

        return self

    def get_upper_immediate(self, value):
        """If bit 11 of lower value is 1, ADDI command sign extends the value.
        To account for that, sign extend lower 12 bits
        and subtract from upper 20 bits."""
        sign_extended_lower = (
            value | 0xFFFFF000 if value & 0x00000800 != 0 else value & 0x00000FFF
        )
        return (value - sign_extended_lower) & 0xFFFFF000

    def to_assembler(self):
        """Returns the sequencer program as assembler code."""
        return "".join(self.assembler)

    def to_binary(self):
        """Generates and returns binary code for the sequencer."""
        return self.binary

    def to_command_values(self):
        """Generates an array of command values to load onto the Platform."""
        return self._instruction_values

    def to_hex_code(self):
        """Generates and returns hex representation of the code to be loaded on the QiController."""
        code_hex = binascii.hexlify(self.binary)
        return SequencerCodeBase._rearrange_hex_code(code_hex)

    def query_command(self, program_counter, command):
        # type: (int, str) -> bool
        """This method checks if `command` is at instruction with number `program_counter`.

        :param program_counter: The program counter of the command to compare.
        :param command: The command that should be compared with.
        """
        return self.assembler[program_counter].split(" ", 1)[0] == command.lower()

    def _add_command_value(self, value):
        binary = SequencerCodeBase._value_to_binary(value)
        self._instruction_values.append(value)
        self.binary.extend(binary)
        self.program_counter += 1

    @staticmethod
    def _check_trigger(trigger, name=""):
        if not isinstance(trigger, int) or trigger < 0 or trigger >= (1 << 4):
            raise ValueError(
                f"Trigger {name} has to be between 0 and 15, but was {trigger}."
            )

    @staticmethod
    def _check_register(register, user=False, no_zero=False):
        """Checks if the register is a valid one. When user=True, 0, 30 and 31 are excluded."""
        if (
            not isinstance(register, int)
            or register < (1 * no_zero)
            or register >= ((1 << 5) - 2 * user)
        ):
            # Register 30 and 31 are reserved for internal use, and 0 is always zero
            raise ValueError(
                f"Register has to be between {1*no_zero} and {31 - 2*user}, but was {register}."
            )

    @staticmethod
    def _check_branch_value(value, name=""):
        if not isinstance(value, int) or value < 0 or value >= (1 << 3):
            raise ValueError(
                f"Value {name} has to be between 0 and 7, but was {value}."
            )

    @staticmethod
    def _check_address(address):
        if not isinstance(address, int) or address < 0 or address >= (1 << 12):
            raise ValueError(
                f"Address has to be between 0 and 4095, but was {address}."
            )

    @staticmethod
    def _value_to_binary(value, bytecount=4):
        """Converts an integer *value* to binary representation using *bytecount* bytes."""
        shifted_data = value
        data_array = [0] * bytecount
        for i in range(bytecount):
            if shifted_data == 0:
                break
            # mask 1 byte (0xFF) of data to be put in each data_array field
            data_array[i] = 0xFF & shifted_data
            # select next larger byte
            shifted_data >>= 8
        return struct.pack("B" * bytecount, *data_array)

    @staticmethod
    def _rearrange_hex_code(hex_code) -> str:
        """Sorts the machine code in the right order for loading the QiController.

        :param hex_code: The original hex code to modify.abs
        :return: Rearranged hex code that can be used for loading on the QiController.
        """
        code_result = ""
        for i in range(len(hex_code) // 8):
            byte1 = hex_code[i * 8 : i * 8 + 2]
            byte2 = hex_code[i * 8 + 2 : i * 8 + 4]
            byte3 = hex_code[i * 8 + 4 : i * 8 + 6]
            byte4 = hex_code[i * 8 + 6 : i * 8 + 8]
            code_result += byte4 + byte3 + byte2 + byte1
        return code_result

    @staticmethod
    def _number_to_asm_hex(number):
        """Converts *number* to hexadecimal representation as used in the assembler.

        :param number: The number to be converted.
        :return: *number* in hex representation..
        """
        return str(hex(number))[2:] + "h"


class SequencerCode(SequencerCodeBase):
    """Class to easily generate code for the QiController sequencer in an object-oriented manner."""

    def trigger_immediate(
        self,
        delay=0,
        manipulation=0,
        readout=0,
        recording=0,
        coupling0=0,
        coupling1=0,
        digital=0,
    ):
        """Triggers the modules with the given codes. Then waits for *delay* seconds.

        :param delay: The delay in seconds to wait before the next command is executed.
        :param manipulation: The code passed to the manipulation pulse generation module.
        :param readout: The code passed to the readout pulse generation module.
        :param recording: The code passed to the recording module.
        :param coupling0: The code triggering the associated first coupling module.
        :param coupling1: The code triggering the associated second coupling module.
        :param digital: The code for digital output triggers.
        """
        # We always ceil so we get no accidental overlap
        clock_cycles_to_wait = util.conv_time_to_cycles(delay, "ceil")

        if clock_cycles_to_wait >= (1 << 12):
            raise ValueError(
                "delay must be smaller than 2^12 clock cycles. Try TRR instead."
            )
        if manipulation < 0 or manipulation >= (1 << 4):
            raise ValueError("manipulation has to be between 0 and 15.")
        if readout < 0 or readout >= (1 << 4):
            raise ValueError("readout has to be between 0 and 15.")
        if recording < 0 or recording >= (1 << 4):
            raise ValueError("recording has to be between 0 and 15.")
        if coupling0 < 0 or coupling0 >= (1 << 2):
            raise ValueError("external has to be between 0 and 3.")
        if coupling1 < 0 or coupling1 >= (1 << 2):
            raise ValueError("external has to be between 0 and 3.")
        if digital < 0 or digital >= (1 << 2):
            raise ValueError("external has to be between 0 and 3.")

        return self.tri(
            clock_cycles_to_wait, readout, recording, manipulation, coupling0, coupling1
        )

    def trigger_registered(
        self,
        register,
        manipulation=0,
        readout=0,
        recording=0,
        coupling0=0,
        coupling1=0,
        digital=0,
    ):
        """Triggers the modules with the given codes.
        Then waits as long as the delay in the specified *register* states.

        :param register: The register containing the delay to wait before continuing with the next command.
        :param manipulation: The code passed to the manipulation pulse generation module.
        :param readout: The code passed to the readout pulse generation module.
        :param recording: The code passed to the recording module.
        :param coupling0: The code triggering the associated first coupling module.
        :param coupling1: The code triggering the associated second coupling module.
        :param digital: The code for digital output triggers.
        """
        if register < 0 or register >= (1 << 4):
            raise ValueError("register has to be between 0 and 15.")
        if manipulation < 0 or manipulation >= (1 << 4):
            raise ValueError("manipulation has to be between 0 and 15.")
        if readout < 0 or readout >= (1 << 4):
            raise ValueError("readout has to be between 0 and 15.")
        if recording < 0 or recording >= (1 << 4):
            raise ValueError("recording has to be between 0 and 15.")
        if coupling0 < 0 or coupling0 >= (1 << 2):
            raise ValueError("external has to be between 0 and 3.")
        if coupling1 < 0 or coupling1 >= (1 << 2):
            raise ValueError("external has to be between 0 and 3.")
        if digital < 0 or digital >= (1 << 2):
            raise ValueError("external has to be between 0 and 3.")

        return self.trr(
            register, readout, recording, manipulation, coupling0, coupling1, digital
        )

    def trigger(
        self,
        manipulation=0,
        readout=0,
        recording=0,
        coupling0=0,
        coupling1=0,
        digital=0,
    ):
        """Triggers the modules with the given codes.
        Then immediately continues with the next instruction (no delay / only 1 cycle).

        :param manipulation: The code passed to the manipulation pulse generation module.
        :param readout: The code passed to the readout pulse generation module.
        :param recording: The code passed to the recording module.
        :param coupling0: The code triggering the associated first coupling module.
        :param coupling1: The code triggering the associated second coupling module.
        :param digital: The code for digital output triggers.
        """
        if manipulation < 0 or manipulation >= (1 << 4):
            raise ValueError("manipulation has to be between 0 and 15.")
        if readout < 0 or readout >= (1 << 4):
            raise ValueError("readout has to be between 0 and 15.")
        if recording < 0 or recording >= (1 << 4):
            raise ValueError("recording has to be between 0 and 15.")
        if coupling0 < 0 or coupling0 >= (1 << 2):
            raise ValueError("external has to be between 0 and 3.")
        if coupling1 < 0 or coupling1 >= (1 << 2):
            raise ValueError("external has to be between 0 and 3.")
        if digital < 0 or digital >= (1 << 2):
            raise ValueError("external has to be between 0 and 3.")

        return self.tr(readout, recording, manipulation, coupling0, coupling1, digital)

    def conditional_jump(self, address, state=None):
        """Waits for a previous readout to return its result.
        Then jumps to the given *address* if the determined state is *state*,
        otherwise program continues with the next command.

        If no *state* is given, the jump will always be performed.

        :param address: Where to jump if the condition is met.
        :param state: The state which a previous readout needs to result in for the jump.
        """

        if address < 0 or address >= (1 << 12):
            raise ValueError("address has to be between 0 and 2**12 - 1.")
        if state is not None and state != 0 and state != 1:
            raise ValueError("state has to be either 0 or 1 or None.")

        # Triggerbus return has only mod0 connected to recording module.
        return self.bra(address, mod0=state)

    def end_of_experiment(self, decay_time=0):
        """Last command of the experiment telling the QiController to wait until the qubit is relaxed.

        :param decay_time: Time to wait for the qubit to relax in the ground state.
        """
        clock_cycles_to_wait = util.conv_time_to_cycles(decay_time, "ceil")

        if clock_cycles_to_wait < 0:
            raise ValueError("decay_time cannot be less than 0.")
        if clock_cycles_to_wait >= (1 << 32):
            raise ValueError("decay_time must be smaller than 2^32 clock cycles.")

        return self.end(clock_cycles_to_wait)

    def trigger_nco_sync(self):
        """Triggers a NCO sync for all modules."""
        return self.tr(sync=True)

    def trigger_readout(self, delay=0, readout=1, recording=1, manipulation=0):
        """Triggers a readout including recording. Then waits until * delay * has passed.

        :param delay: The delay in seconds to wait before the next command is executed.
        :param readout: The code passed to the readout pulse generation module.
        :param recording: The code passed to the recording module.
          1 : For recording that will be used for averaging
          2 : For a single shot recording without averaging
        :param manipulation: The code passed to the manipulation pulse generator.
        """
        # Second Recording Module is connected to "external"
        return self.trigger_immediate(
            delay, manipulation, readout, recording, recording
        )

    def trigger_active_reset(self, pi_trigger, pi_length, state=0, readout=1):
        # type: (int, float, int, int) -> SequencerCode
        """Triggers an active reset operation including all necessary peripheral steps.
        Execution will continue with the next instruction after the conditional reset was performed.

        :param pi_trigger: The manipulation trigger to start the (conditional) pi pulse.
        :param pi_length: The duration of the (conditional) pi pulse.
        :param state: The state in which the qubit should be reset
        :param readout: The readout trigger to start the state-determining readout pulse
        """

        # Perform first readout to determine qubit state (recording is single-shot without averaging)
        self.trigger_readout(readout=readout, recording=2)

        # We jump to the next instruction and skip pi pulse if qubit is already in state *state*
        # +1 (pi pulse) +1 (next instruction)
        jump_address = self.get_next_program_counter() + 2
        self.conditional_jump(address=jump_address, state=state)

        # Performing the pi pulse (if state = 1)
        self.trigger_immediate(pi_length, manipulation=pi_trigger)  # pi

        # Next address: BRA + 2
        return self
