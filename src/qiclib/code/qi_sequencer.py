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
The lower level logic of the code generation.
This module tracks the sequencer state at the current point (e.g. register values, variable to register mapping, etc.),
provides helper functions to generate code for expressions and more.
"""

from __future__ import annotations

import warnings
from enum import Enum
from typing import Any

import qiclib.packages.utility as util
from qiclib.code.qi_command import (
    DigitalTriggerCommand,
    ForRangeCommand,
    IfCommand,
    ParallelCommand,
    PlayCommand,
    PlayFluxCommand,
    PlayReadoutCommand,
    QiTriggerCommand,
    RecordingCommand,
    SyncCommand,
)
from qiclib.code.qi_seq_instructions import (
    SeqAwaitQubitState,
    SeqBranch,
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
from qiclib.code.qi_util import _get_for_range_iterations
from qiclib.code.qi_var_definitions import (
    QiCellProperty,
    QiCondition,
    QiExpression,
    QiOp,
    QiOpCond,
    QiVariableSet,
    _QiCalcBase,
    _QiConstValue,
    _QiVariableBase,
)


class _Register:
    """Class of Sequencer representing registers.
    Keeps track of values in register. Values are used for program length. Program length is invalidated by use of If/Else.
    TODO load commands invalidate value"""

    def __init__(self, address) -> None:
        self.adr = address
        self.value = None
        self.valid = True

    def addition(self, val1, val2):
        self.value = val1 + val2

    def subtraction(self, val1, val2):
        self.value = val1 - val2

    def multiplication(self, val1, val2):
        self.value = val1 * val2

    def and_values(self, val1, val2):
        self.value = val1 & val2

    def or_values(self, val1, val2):
        self.value = val1 | val2

    def xor_values(self, val1, val2):
        self.value = val1 ^ val2

    def lshift(self, val1, val2):
        self.value = val1 << val2

    def rshift(self, val1, val2):
        self.value = val1 >> val2

    def inversion(self, val1, val2):
        self.value = ~val1

    # Dictionary used to receive function from input QiOp
    eval_operation = {  # noqa: RUF012
        QiOp.PLUS: addition,
        QiOp.MINUS: subtraction,
        QiOp.MULT: multiplication,
        QiOp.AND: and_values,
        QiOp.OR: or_values,
        QiOp.XOR: xor_values,
        QiOp.LSH: lshift,
        QiOp.RSH: rshift,
        QiOp.NOT: inversion,
    }

    def get_value(self):
        if self.valid:
            return self.value

        return None

    def update_register_value(self, val1, op, val2):
        """Register Values are updated to allow implicit synchronisations through wait when variable Wait/Pulse is used.
        When a calculation is done using a invalid variable value, the ensuing value is also invalidated.
        """
        if self.adr == 0:
            self.value = 0  # reg0 always contains 0
            return

        if isinstance(val1, _Register):
            if val1.value is None:
                raise RuntimeError(
                    f"Variable at Register {val1.adr} has not been properly initialised"
                )
            if not val1.valid:
                self.valid = False
            val1 = val1.value
        if isinstance(val2, _Register):
            if val2.value is None:
                raise RuntimeError(
                    f"Variable at Register {val2.adr} has not been properly initialised"
                )
            if not val2.valid:
                self.valid = False
            val2 = val2.value

        self.eval_operation[op](self, val1, val2)


class ForRangeEntry:
    def __init__(self, reg_addr, start_val, end_val, step_val) -> None:
        self.reg_addr = reg_addr
        self.start = start_val
        self.end = end_val
        self.step = step_val
        self.end_addr = 0
        self.iterations = 0
        self.aggregate_iterations = 0
        self.contained_entries: list[ForRangeEntry] = []

    def _calc_aggregate(self):
        """Calculates the number of loops contained inside, considering nested entries, for later use at progress bar."""
        self.iterations = _get_for_range_iterations(self.start, self.end, self.step)

        if len(self.contained_entries) == 0 or self.iterations is None:
            if self.iterations is None:
                self.aggregate_iterations = 0
                warnings.warn(
                    "A loop with variable start/end could not be counted towards total loop count. Progress bar might be inaccurate."
                )
            else:
                self.aggregate_iterations = self.iterations
        else:
            nested = 0
            for entry in self.contained_entries:
                if entry.aggregate_iterations == 0:
                    warnings.warn(
                        "A loop with variable start/end could not be counted towards total loop count. Progress bar might be inaccurate."
                    )
                    continue
                nested += entry.aggregate_iterations

            self.aggregate_iterations = self.iterations * (nested if nested != 0 else 1)

    def get_iteration(self, value: int) -> int:
        """Returns the current iteration depending on the parameter value"""
        if isinstance(self.start, _QiVariableBase):
            return 0

        _step = self.step if isinstance(self.step, int) else self.step.value

        iterations = 0
        for _ in range(self.start, value, _step):
            iterations += 1

        return iterations

    @staticmethod
    def get_total_loops(entry_list):
        if len(entry_list) == 0:
            return 1

        iterations = 0

        for entry in entry_list:
            iterations += entry.aggregate_iterations

        return iterations if iterations > 0 else 1

    @staticmethod
    def calculate_current_loop(entry_list, register_list, prog_counter):
        loop = 0

        for entry in entry_list:
            if entry.end_addr < prog_counter:
                loop += entry.aggregate_iterations
            else:
                iteration = entry.get_iteration(register_list[entry.reg_addr])

                if len(entry.contained_entries) == 0:
                    loop += iteration
                else:
                    loop += iteration * ForRangeEntry.get_total_loops(
                        entry.contained_entries
                    ) + ForRangeEntry.calculate_current_loop(
                        entry.contained_entries, register_list, prog_counter
                    )

                return loop

        return loop


class Sequencer:
    AVAILABLE_REGISTERS = 31
    MULTIPLICATION_LENGTH = 6
    JUMP_EXECUTION_CYCLES = 2
    LOAD_STORE_LENGTH = 8
    # Additional delay to prevent ignored trigger for consecutive readouts
    RECORDING_MODULE_DELAY_CYCLES = 1
    CHOKE_PULSE_INDEX = 14

    def __init__(self, cell_index: int | None = None):
        self.alu = _ALU(self)
        self.reset()
        self.cell_index = cell_index

    def reset(self) -> None:
        self._register_stack: list[_Register] = []
        self.instruction_list: list[SequencerInstruction] = []
        self._prog_cycles = _ProgramCycles()
        self._var_reg_dict: dict[Any, _Register] = {}
        self._trigger_mods = _TriggerModules()
        self._for_range_list: list[ForRangeEntry] = []
        self._for_range_stack: list[ForRangeEntry] = []

        # register 0 always contains 0, so is not in stack
        self.reg0 = _Register(0)
        for x in range(Sequencer.AVAILABLE_REGISTERS, 0, -1):
            self._register_stack.append(_Register(x))

    def print_assembler(self):
        for pc, instruction in enumerate(self.instruction_list):
            print(f"{pc}# {instruction}")

    @property
    def prog_cycles(self):
        """Program length is used for implicit synchs with Wait-Commands. If a program contains variable If/Else or loads to wait registers
        prog_length can not be determined. Invalid prog_cycles are some value less than 0.
        """
        if self._prog_cycles.valid:
            return self._prog_cycles.cycles

        return _ProgramCycles.INVALID

    @prog_cycles.setter
    def prog_cycles(self, x):
        """Set externally when ForRange is used."""
        self._prog_cycles.cycles = x

    @property
    def recording_delay(self):
        return util.conv_cycles_to_time(self.RECORDING_MODULE_DELAY_CYCLES)

    def add_variable(self, var):
        """Adds variable to sequencer, reserving a register for it"""
        reg = self.request_register()
        self._var_reg_dict[var.id] = reg
        # Named variables can be initialized externally
        if var.name is not None:
            reg.valid = False
            reg.value = 0

    def release_variable(self, var):
        self.release_register(self.get_var_register(var))

    def get_var_register(self, var) -> _Register:
        """Returns _Register of QiVariable var"""
        reg = self._var_reg_dict.get(var.id)

        if reg is None:
            raise RuntimeError(
                f"Variable not defined for Sequencer, var.id:{var.id}, {self._var_reg_dict}"
            )

        return reg

    def get_var_value(self, var) -> int | float | None:
        return self.get_var_register(var).get_value()

    def request_register(self) -> _Register:
        """Returns register from stack, raises exception, if no registers are on stack anymore"""
        try:
            return self._register_stack.pop()
        except IndexError as e:
            print(f"Not enough registers available, sequencer {self} error {e}")
            raise

    def get_cycles_from_length(self, length) -> _Register | int:
        """If length is QiVariable, return _Register, else return numbers of cycles ceiled"""
        from .qi_var_definitions import _QiVariableBase

        if isinstance(length, _QiVariableBase):
            return self.get_var_register(length)
        elif isinstance(length, int):
            length = float(length)

        return util.conv_time_to_cycles(length, mode="ceil")

    def release_register(self, reg: _Register):
        """Returns register to stack; Raises exception when register is already in stack, or addressing is faulty.
        Releasing register 0 does nothing"""
        if reg in self._register_stack:
            raise IndexError("Release Register: Already released register")
        if (reg.adr > Sequencer.AVAILABLE_REGISTERS) or (reg.adr < 0):
            raise IndexError("Release Register: Address out of Range")
        if reg == self.reg0:
            return
        reg.valid = True  # if register was invalidated and is released again, return it to initial valid state
        self._register_stack.append(reg)

    def add_instruction_to_list(
        self,
        instruction: SequencerInstruction,
        length_in_cycles: int = 1,
        length_valid=True,
    ):
        """Adds instruction to list. If pulses are still running, adds choke instruction before adding the current command to the list"""
        if self._trigger_mods.is_pulse_active:
            self.trigger_choke_pulse()
        if length_in_cycles == 0:
            length_in_cycles = 1  # length is always at least 1 per instruction

        self.instruction_list.append(instruction)
        self._prog_cycles.add(
            length_in_cycles, length_valid
        )  # Will be deprecated when external sync is possible.

    def get_prog_size(self) -> int:
        return len(self.instruction_list)

    def add_mov_command(self, dst_reg: _Register, src_reg: _Register):
        """Copies value of src_reg to dst_reg."""
        self.add_calculation(src_reg, QiOp.PLUS, 0, dst_reg)

    def get_upper_immediate_value(self, value: int):
        """If bit 11 of lower value is 1, ADDI command sign extends the value. To account for that, sign extend lower 12 bits
        and subtract from upper 20 bits."""
        sign_extended_lower = (
            value | 0xFFFFF000 if value & 0x00000800 != 0 else value & 0x00000FFF
        )
        return (value - sign_extended_lower) & 0xFFFFF000

    def immediate_to_register(
        self, val: int, dst_reg: _Register | None = None
    ) -> _Register:
        """Loads immediate to dst_reg.
        If dst_reg is not defined a new register is used to save val to.
        If value == 0 and no register is specified, reg0 is returned, which always contains 0.
        dst_reg.value is updated to reflect changes."""
        if val == 0 and dst_reg is None:
            return self.reg0
        elif dst_reg is None:
            dst_reg = self.request_register()

        if isinstance(val, float):
            raise NotImplementedError("float not implemented yet")

        if SequencerInstruction.is_value_in_lower_immediate(val):
            self.add_instruction_to_list(
                SeqRegImmediateInst(QiOp.PLUS, dst_reg.adr, 0, val)
            )  # register_0 always contains 0
        else:
            upper_immediate = self.get_upper_immediate_value(val)
            self.add_instruction_to_list(SeqLoadUpperImm(dst_reg.adr, upper_immediate))
            if val & 0xFFF != 0:
                self.add_instruction_to_list(
                    SeqRegImmediateInst(QiOp.PLUS, dst_reg.adr, dst_reg.adr, val)
                )

        dst_reg.update_register_value(val, QiOp.PLUS, 0)
        return dst_reg

    def add_calculation(
        self,
        val1: _Register | int | float,
        operator: QiOp,
        val2: _Register | int | float,
        dst_reg: _Register | None = None,
    ) -> _Register:
        """Adds calculation command to sequencer. Depending on the values and the operation different commands are added.
        dst_reg.value is updated to reflect changes."""
        if (not isinstance(val1, _Register)) and (not isinstance(val2, _Register)):
            raise RuntimeError("QiCalc should not contain two int/float")

        if dst_reg is None:
            dst_reg = self.request_register()

        self.alu.calculate(dst_reg, val1, operator, val2)

        dst_reg.update_register_value(val1, operator, val2)

        return dst_reg

    def add_condition(
        self, reg1: _Register, operator: QiOpCond, reg2: _Register, jmp_val=0
    ):
        """Adds condition command to the sequence and returns its reference, to define the jump value at a later point"""

        cmd = SeqBranch(operator, reg1.adr, reg2.adr, jmp_val)
        self.add_instruction_to_list(cmd)
        return cmd

    def add_jump(self, jmp_val=0) -> SeqJump:
        """Adds jump command to the sequence and returns its reference, to define the jump value at a later point"""
        cmd = SeqJump(jmp_val)
        self.add_instruction_to_list(
            cmd, length_in_cycles=Sequencer.JUMP_EXECUTION_CYCLES
        )
        return cmd

    def __evaluate_qicalc_val(self, value: QiExpression) -> _Register | int:
        """Return value of QiCalc-Value.
        If another QiCalc node is found, evaluate node first, then return target register of evaluated node.
        Return _Register if QiVariable is found.
        Else return constant register value as int. (Can represent cycles)"""

        if isinstance(value, _QiCalcBase):
            return self.add_qi_calc(value)
        elif isinstance(value, _QiVariableBase):
            return self.get_var_register(value)
        elif isinstance(value, (_QiConstValue, QiCellProperty)):
            return value.value
        else:
            raise TypeError("Unknown type in QiCalc")

    def add_qi_calc(self, qi_calc) -> _Register:
        """QiCalc is traversed and for each node a calculation is added to the sequencer. After the calculation is added,
        _Registers are released, if leafs are also QiCalc nodes. If leafs are QiVariable they are not released
        """

        value1 = self.__evaluate_qicalc_val(qi_calc.val1)

        value2 = self.__evaluate_qicalc_val(qi_calc.val2)

        dst_reg = self.add_calculation(value1, qi_calc.op, value2)

        if isinstance(qi_calc.val1, _QiCalcBase):
            if isinstance(value1, _Register):
                self.release_register(value1)
            else:
                raise TypeError("value1 should be Register")

        if isinstance(qi_calc.val2, _QiCalcBase):
            if isinstance(value2, _Register):
                self.release_register(value2)
            else:
                raise TypeError("value2 should be Register")

        return dst_reg

    def __evaluate_if_cond_val(self, value: QiExpression) -> _Register:
        if isinstance(value, _QiCalcBase):
            reg = self.add_qi_calc(value)
        elif isinstance(value, _QiVariableBase):
            reg = self.get_var_register(value)
        elif isinstance(value, _QiConstValue):
            reg = self.immediate_to_register(value.value)
        else:
            raise TypeError("Unknown type in QiCalc")

        return reg

    def add_if_condition(self, qi_condition: QiCondition) -> SeqBranch:
        """Evaluates QiCondition and inverts condition operation to add to the sequencer."""
        reg1 = self.__evaluate_if_cond_val(qi_condition.val1)

        reg2 = self.__evaluate_if_cond_val(qi_condition.val2)

        # invert QiCondition --> if(x == 3) --> jump over if-body when (x!=3)
        cmd = self.add_condition(reg1, qi_condition.op.invert(), reg2)

        if not isinstance(qi_condition.val1, _QiVariableBase):
            self.release_register(reg1)

        if not isinstance(qi_condition.val2, _QiVariableBase):
            self.release_register(reg2)

        return cmd

    def add_for_range_head(
        self,
        var: _QiVariableBase,
        start: _QiVariableBase | int,
        end_val: _Register,
        step: _QiConstValue,
    ) -> SeqBranch:
        """Loads start value to variable register (1-2 commands depending on start value) and adds branch command to compare variable register with end_val register"""
        reg1 = self.get_var_register(var)
        if isinstance(start, _QiVariableBase):
            self.add_mov_command(reg1, self.get_var_register(start))
        else:
            assert isinstance(start, int)
            self.immediate_to_register(val=start, dst_reg=reg1)

        if step.value > 0:
            return self.add_condition(reg1, QiOpCond.GE, end_val)
        else:
            return self.add_condition(reg1, QiOpCond.LE, end_val)

    def set_variable_value(self, var, value):
        dst = self.get_var_register(var)

        if isinstance(value, _QiVariableBase):
            src = self.get_var_register(value)
            self.add_mov_command(dst, src)
            return

        if isinstance(value, (_QiConstValue, QiCellProperty)):
            value = value.value

        self.immediate_to_register(val=value, dst_reg=dst)

    def _wait_cycles(self, cycles: int):
        """Adds SeqWaitImmediate command to sequencer if cycles is smaller than upper immediate max value,
        else loads cycles to register and adds SeqWaitRegister command"""
        if not (0 < cycles <= 2**32 - 1):
            raise ValueError(
                f"Wait cycles not in valid range, should be between 0 and 2^32-1 but was {cycles}!"
            )

        if SequencerInstruction.is_value_in_unsigned_upper_immediate(cycles):
            self.add_instruction_to_list(
                SeqWaitImm(cycles), length_in_cycles=cycles if cycles > 0 else 1
            )
        else:
            register = self.immediate_to_register(
                cycles - 2
            )  # shorten by 2 because writing large numbers to reg takes 2 cycles
            self.add_instruction_to_list(
                SeqWaitRegister(register.adr), length_in_cycles=cycles - 2
            )
            self.release_register(register)

    def add_wait_cmd(self, qi_wait):
        """Evaluates QiWait
        If length attribute is int/float, calls _wait_cycles to add wait commands.
        If length attribute is _QiVariable, it's register is used for wait command.
        If attribute length is _QiCalcBase, QiCalc is evaluated and its final Register is used as wait time, after which the register is released again
        """
        from .qi_var_definitions import _QiCalcBase

        if isinstance(qi_wait.length, _QiCalcBase):
            length = self.add_qi_calc(qi_wait.length)
            warnings.warn("Calculations inside wait might impede timing")
            # TODO decrease wait time depending on amount of calculations for length
        else:
            length = self.get_cycles_from_length(qi_wait.length)

        if isinstance(length, _Register):
            if length.value is None:
                raise RuntimeError(
                    f"Variable at Register {length.adr} has not been properly initialised"
                )

            self.add_instruction_to_list(
                SeqWaitRegister(length.adr), length.value, length.valid
            )

            if isinstance(qi_wait.length, _QiCalcBase):
                self.release_register(length)
        else:
            try:
                self._wait_cycles(length)
            except ValueError as e:
                maxtime = util.conv_cycles_to_time((1 << 32) - 1)
                raise ValueError(
                    f"Wait length needs to be between 0 and {maxtime:.3f}s, but was {qi_wait.length}s."
                ) from e

    def _get_length_of_trigger(self, *pulses, recording_delay) -> _Register | int:
        """Compares length of pulses and returns longest.
        If variable length is used, returns variable's register.
        If multiple different variable lengths are used raises RuntimeError
        TODO check register value, if it is smaller than other pulses play other lengths
        """
        from .qi_command import AnyPlayCommand
        from .qi_var_definitions import _QiVariableBase

        var_set = QiVariableSet()
        for pulse_cmd in pulses:
            if hasattr(pulse_cmd, "length"):
                if isinstance(pulse_cmd.length, _QiVariableBase):
                    var_set.add(pulse_cmd.length)

        if len(var_set) > 1:
            raise RuntimeError(
                "Concurrent pulses with different variable length not supported"
            )

        wait = 0
        for pulse_cmd in pulses:
            if isinstance(pulse_cmd, AnyPlayCommand):
                if isinstance(pulse_cmd.length, _QiVariableBase):
                    return self.get_var_register(pulse_cmd.length)
                else:
                    wait = max(wait, pulse_cmd.length)
            elif isinstance(pulse_cmd, RecordingCommand):
                length = pulse_cmd.length
                if recording_delay:
                    length += util.conv_cycles_to_time(
                        self.RECORDING_MODULE_DELAY_CYCLES
                    )
                if not isinstance(
                    wait, _QiVariableBase
                ):  # if wait is already variable, take variable as wait time
                    wait = max(wait, length)

        return self.get_cycles_from_length(wait)

    def add_nco_sync(self, delay: float):
        """Adds NCO Sync Trigger to sequencer"""
        self.add_instruction_to_list(SeqTrigger(sync=True))

        length = util.conv_time_to_cycles(delay, "ceil")

        if length > 1:
            self._wait_cycles(
                length - 1
            )  # -1 cycle, because trigger already takes up one cycle

    def trigger_choke_pulse(self):
        """Adds trigger command choking still running pulse generators."""
        trigger_values = self._trigger_mods.get_trigger_val()
        choke_pulse = SeqTrigger(*trigger_values)

        self.add_instruction_to_list(choke_pulse)

    def _check_recording_state(self, recording=None) -> bool:
        """If recording saves to state variable, add command to save to the defined variable.
        Returns True if saving to state, else returns False"""
        if recording is not None and recording.uses_state:
            reg = self.get_var_register(recording.var)
            self.add_instruction_to_list(
                SeqAwaitQubitState(dst=reg.adr, cell=self.cell_index)
            )

            self._prog_cycles.valid = False  # cannot determine length of Synch therefore _prog_cycles is invalid

            return True

        return False

    def add_trigger_cmd(
        self,
        manipulation: PlayCommand | None = None,
        readout: PlayReadoutCommand | None = None,
        recording: RecordingCommand | None = None,
        coupling0: PlayFluxCommand | None = None,
        coupling1: PlayFluxCommand | None = None,
        digital: DigitalTriggerCommand | None = None,
        recording_delay: bool = True,
        var_single_cycle: bool = False,
    ):
        """Adds trigger command to sequencer, depending on the specified pulses.
        The sequencer keeps track of still running pulse generators. If a pulse generator is not choked yet,
        the index of the choke pulse or the index of the new pulse to be played is used to choke the running pulse.
        Recording_delay defines, if the delay cycles of the recording module are added to the trigger length, this can be turned
        off, because Parallel bodies already implement this duration in the sequence generation.
        """
        trigger_values = self._trigger_mods.get_trigger_val(
            readout, recording, manipulation, coupling0, coupling1, digital
        )

        self.add_instruction_to_list(SeqTrigger(*trigger_values))

        length = self._get_length_of_trigger(
            manipulation, readout, recording, digital, recording_delay=recording_delay
        )

        if isinstance(length, _Register) or var_single_cycle:  # is any pulse variable?
            if var_single_cycle is False:
                if length.value is None:
                    raise RuntimeError(
                        f"Variable at Register {length.adr} has not been properly initialised"
                    )

                self.add_instruction_to_list(
                    SeqTriggerWaitRegister(length.adr), length.value - 1, length.valid
                )
            self._trigger_mods.set_active(readout, None, manipulation, None)

            self._check_recording_state(
                recording
            )  # add possible state save; var pulse is stopped before saving operation

        elif (
            length > 1
            and (recording is None or recording.toggle_continuous is None)
            and not self._check_recording_state(recording)
        ):
            self._wait_cycles(
                length - 1
            )  # -1 cycle, because trigger already takes up one cycle

    def end_of_command_body(self):
        """Called when body of commands ended; adds choke command for active pulses"""
        if self._trigger_mods.is_pulse_active:
            self.trigger_choke_pulse()

    def register_for_range(self, variable, start, stop, step):
        """Generates a list of ForRange Entries, saves start, stop and step values, as well as the used register and
        current program counter. This data can later be retrieved to generate progress information of the program.
        """

        if isinstance(start, _QiVariableBase):
            start = self.get_var_value(start)
        elif isinstance(start, (_QiConstValue, QiCellProperty)):
            start = start.value

        if isinstance(stop, _QiVariableBase):
            stop = self.get_var_value(stop)
        elif isinstance(stop, (_QiConstValue, QiCellProperty)):
            stop = stop.value

        entry = ForRangeEntry(self.get_var_register(variable).adr, start, stop, step)

        if len(self._for_range_stack) == 0:
            self._for_range_list.append(entry)
            self._for_range_stack.append(entry)
        else:
            self._for_range_stack[-1].contained_entries.append(entry)
            self._for_range_stack.append(entry)

    def exit_for_range(self):
        """Signals end of ForRange, so next ForRange will not be regarded as nested inside previous ForRangeEntry.
        Saves end PC at ForRangeEntry and calculates number of loops for this ForRangeEntry.
        """
        current_fr = self._for_range_stack.pop()
        current_fr.end_addr = len(self.instruction_list) - 1
        current_fr._calc_aggregate()

    def _normalise_base_offset(
        self, base: _Register | None, offset: int
    ) -> tuple[
        _Register, int, bool
    ]:  # base register, offset, whether this function requested the register and it needs to be released.
        """If an instruction (i.e. load, store) requires a base (address) register with a constant offset
        this function checks if the provided arguments are suitable or it generates instructions and returns
        possibly different register and offset.
        """

        free = False

        if base is None:
            # Caller wants to access an absolute address.

            if SequencerInstruction.is_value_in_lower_immediate(offset):
                base_register = self.reg0
            else:
                base_register = self.request_register()
                free = True
                self.immediate_to_register(offset, base_register)
                offset = 0
        else:
            base_register = base

            if not SequencerInstruction.is_value_in_lower_immediate(offset):
                # We could support larger offsets by loading the offset into a new register,
                # adding the content from the base register to this new register and loading the value.
                # We should avoid changing the base register contents as this is would be unexpected behaviour
                # and it is common to use the same base register with multiple different offsets.
                # However, so far we don't consider this functionality necessary.
                raise RuntimeError("Offset is too large.")

        return base_register, offset, free

    def add_store_cmd(
        self,
        value: QiExpression,
        base: _Register | None,
        offset: int = 0,
    ):
        """Adds store command to instruction list. If necessary it will generate additional instructions needed to perform the store.
        If offset does not fit into 12 bits an additional Add instruction is generated.

        :param value: The value to be stored.
        :param base: Contains the destination address.
        :param offset: Offset added to base address.
            If no base address is provided this is the absolute address. Defaults to 0.
        :param width: Number of bits to be stored. Can be 32, 16 or 8. Defaults to 32.
        """

        requested_registers = []

        if isinstance(value, _QiCalcBase):
            value_register = self.add_qi_calc(value)
        elif isinstance(value, _QiVariableBase):
            value_register = self.get_var_register(value)
        elif isinstance(value, (_QiConstValue, QiCellProperty)):
            value_register = self.request_register()
            requested_registers.append(value_register)
            self.immediate_to_register(value.value, value_register)

        base_register, offset, free = self._normalise_base_offset(base, offset)

        if free:
            requested_registers.append(base_register)

        self.add_instruction_to_list(
            SeqStore(value_register.adr, base_register.adr, offset),
            length_in_cycles=Sequencer.LOAD_STORE_LENGTH,
            length_valid=True,
        )

        for r in requested_registers:
            self.release_register(r)

    def add_load_cmd(
        self,
        dst: _QiVariableBase | _Register,
        base: _Register | None,
        offset: int = 0,
    ):
        """Adds load command to instruction list. If necessary it will generate additional instructions needed to perform the load.
        If offset does not fit into 12 bits an additional Add instruction is generated.

        :param dst: The register which will contain the loaded value.
        :param base: Contains the source address.
        :param offset: Offset added to source address.
            If no base address is provided this is the absolute address. Defaults to 0.
        :param width: Number of bits to be loaded. Can be 32, 16 or 8. Defaults to 32.
            Depending on sign, the remaining bits will be sign extended.
        :param signed: Is the loaded value signed or unsigned.
        """

        if isinstance(dst, _QiVariableBase):
            dst_register = self.get_var_register(dst)
        else:
            dst_register = dst

        base_register, offset, free = self._normalise_base_offset(base, offset)

        self.add_instruction_to_list(
            SeqLoad(
                dst_register.adr,
                base_register.adr,
                offset,
            ),
            length_in_cycles=Sequencer.LOAD_STORE_LENGTH,
            length_valid=True,
        )
        print(f"{self.add_instruction_to_list}")

        if free:
            self.release_register(base_register)

    def end_of_program(self):
        """Add End instruction to instruction list"""
        self.add_instruction_to_list(SeqEnd())


class _ALU:
    def __init__(self, Sequencer: Sequencer) -> None:
        self.seq = Sequencer

    def _large_immediate_operation(
        self,
        operation,
        dst_reg: _Register,
        reg: _Register,
        immediate: int,
        length_in_cycles=1,
    ):
        """Used by commutative_operation/non_commutative_operation to load large immediate values to a Register before performing the operation.
        Is not called from outside, so a update to dst_reg is not necessary."""
        tmp_reg = self.seq.immediate_to_register(immediate)
        self.seq.add_instruction_to_list(
            SeqRegRegInst(operation, dst_reg.adr, reg.adr, tmp_reg.adr),
            length_in_cycles,
        )
        self.seq.release_register(tmp_reg)

    def commutative_operation(
        self,
        operation,
        dst_reg: _Register,
        val1: _Register | int | float,
        val2: _Register | int | float,
    ):
        """Checks if val1 is of type _Register, if not it switches val1 and val2.
        After switching, val2 is int/float or _Register. In the case of int/float it is checked if an immediate command can be
        used, else val2 is loaded to a register."""
        if isinstance(val1, _Register):
            if isinstance(val2, _Register):
                self.seq.add_instruction_to_list(
                    SeqRegRegInst(operation, dst_reg.adr, val1.adr, val2.adr)
                )
            elif isinstance(val2, int):
                if SequencerInstruction.is_value_in_lower_immediate(val2):
                    self.seq.add_instruction_to_list(
                        SeqRegImmediateInst(operation, dst_reg.adr, val1.adr, val2)
                    )
                else:
                    self._large_immediate_operation(operation, dst_reg, val1, val2)
            elif isinstance(val2, float):
                raise NotImplementedError("Float not implemented")
        else:
            self.commutative_operation(operation, dst_reg, val2, val1)

    def non_commutative_operation(
        self,
        operation,
        dst_reg: _Register,
        val1: _Register | int | float,
        val2: _Register | int | float,
    ):
        """Checks if val1 is of type _Register and tries to use immediate command, else register command is used."""
        if isinstance(val1, _Register):
            if isinstance(val2, _Register):
                self.seq.add_instruction_to_list(
                    SeqRegRegInst(operation, dst_reg.adr, val1.adr, val2.adr)
                )
            elif isinstance(val2, int):
                if SequencerInstruction.is_value_in_lower_immediate(val2):
                    self.seq.add_instruction_to_list(
                        SeqRegImmediateInst(operation, dst_reg.adr, val1.adr, val2)
                    )
                else:
                    self._large_immediate_operation(operation, dst_reg, val1, val2)
            elif isinstance(val2, float):
                raise NotImplementedError("Float not implemented")
        elif isinstance(val2, _Register):
            # if val1 is not a reg, val2 must be one
            tmp_reg = self.seq.immediate_to_register(val1)
            self.seq.add_instruction_to_list(
                SeqRegRegInst(operation, dst_reg.adr, tmp_reg.adr, val2.adr)
            )
            self.seq.release_register(tmp_reg)
        else:
            raise RuntimeError("One of the variables must be of type _Register")

    def addition(self, dst_reg, val1, val2):
        self.commutative_operation(QiOp.PLUS, dst_reg, val1, val2)

    def subtraction(self, dst_reg, val1, val2):
        """Special case. Immediate commands do not support substraction, instead tries addition with negative number."""
        if (
            isinstance(val1, _Register)
            and isinstance(val2, int)
            and SequencerInstruction.is_value_in_lower_immediate(val2)
        ):
            self.seq.add_instruction_to_list(
                SeqRegImmediateInst(QiOp.PLUS, dst_reg, val1.adr, -val2)
            )
        else:
            self.non_commutative_operation(QiOp.MINUS, dst_reg, val1, val2)

    def multiplication(self, dst_reg, val1, val2):
        """Multiplication is not supported as immediate commands and has longer execution time."""
        if isinstance(val1, _Register):
            if isinstance(val2, _Register):
                self.seq.add_instruction_to_list(
                    SeqRegRegInst(QiOp.MULT, dst_reg, val1.adr, val2.adr),
                    length_in_cycles=Sequencer.MULTIPLICATION_LENGTH,
                )
            elif isinstance(val2, int):
                self._large_immediate_operation(
                    QiOp.MULT,
                    dst_reg,
                    val1,
                    val2,
                    length_in_cycles=Sequencer.MULTIPLICATION_LENGTH,
                )
            elif isinstance(val2, float):
                raise NotImplementedError("Float not implemented")
        else:
            self.multiplication(dst_reg, val2, val1)

    def and_values(self, dst_reg, val1, val2):
        self.commutative_operation(QiOp.AND, dst_reg, val1, val2)

    def or_values(self, dst_reg, val1, val2):
        self.commutative_operation(QiOp.OR, dst_reg, val1, val2)

    def xor_values(self, dst_reg, val1, val2):
        self.commutative_operation(QiOp.XOR, dst_reg, val1, val2)

    def lshift(self, dst_reg, val1, val2):
        self.non_commutative_operation(QiOp.LSH, dst_reg, val1, val2)

    def rshift(self, dst_reg, val1, val2):
        self.non_commutative_operation(QiOp.RSH, dst_reg, val1, val2)

    def inversion(self, dst_reg, val1, val2):
        self.commutative_operation(QiOp.XOR, dst_reg, val1, -1)

    # Dictionary used to receive function from input QiOp
    eval_operation = {  # noqa: RUF012
        QiOp.PLUS: addition,
        QiOp.MINUS: subtraction,
        QiOp.MULT: multiplication,
        QiOp.AND: and_values,
        QiOp.OR: or_values,
        QiOp.XOR: xor_values,
        QiOp.LSH: lshift,
        QiOp.RSH: rshift,
        QiOp.NOT: inversion,
    }

    def calculate(self, dst_reg, val1, op, val2):
        self.eval_operation[op](self, dst_reg=dst_reg, val1=val1, val2=val2)


class _ProgramCycles:
    """Class of Sequencer to keep track of cycles since some synchronization point.
    Synchronization points can be the program start or anywhere different sequencers are synchronized,
    like an explicit Sync command, before if-else or ForRanges.
    (If we call try_sync, its a synchronization point)
    If if/else are used, valid is set to False."""

    INVALID = -1

    class SyncPointType(Enum):
        PROGRAM_START = 0
        SYNC_COMMAND = 1
        BEFORE_IF_ELSE = 2
        BEFORE_FOR_RANGE = 3
        AFTER_FOR_RANGE_ITERATION = 4
        BEFORE_PARALLEL = 5
        LOOP_UNROLL0 = 6
        LOOP_UNROLL1 = 7

    class SyncPoint:
        def __init__(self, cmd=None, type=None):
            _SyncPointType = _ProgramCycles.SyncPointType

            if type is None:
                assert cmd is not None

                if isinstance(cmd, IfCommand):
                    type = _SyncPointType.BEFORE_IF_ELSE
                elif isinstance(cmd, ParallelCommand):
                    type = _SyncPointType.BEFORE_PARALLEL
                elif isinstance(cmd, SyncCommand):
                    type = _SyncPointType.SYNC_COMMAND
                else:
                    raise RuntimeError("Can not infer _SyncPointType from command.")
            elif cmd is None:
                assert type == _SyncPointType.PROGRAM_START
            elif isinstance(cmd, ForRangeCommand):
                assert type is not None and type in [
                    _SyncPointType.BEFORE_FOR_RANGE,
                    _SyncPointType.AFTER_FOR_RANGE_ITERATION,
                    _SyncPointType.LOOP_UNROLL0,
                    _SyncPointType.LOOP_UNROLL1,
                ]
            else:
                raise RuntimeError("Missing arguments")

            self.type = type
            self.command = cmd

        def __eq__(self, other):
            if not isinstance(other, _ProgramCycles.SyncPoint):
                return False
            else:
                return self.type == other.type and self.command is other.command

        def __hash__(self):
            return hash(self.type) + hash(self.command)

    def __init__(self) -> None:
        self.last_sync_point = _ProgramCycles.SyncPoint(
            None, _ProgramCycles.SyncPointType.PROGRAM_START
        )
        self.cycles = 0
        self.valid = True

    def set_synchronized(self, sync_point: _ProgramCycles.SyncPoint):
        self.last_sync_point = sync_point
        self.cycles = 0
        self.valid = True

    def add(self, cycles, valid: bool):
        if valid is False:
            self.valid = False

        self.cycles += cycles


class _RecordingTrigger(Enum):
    NONE = 0
    SINGLE = 1
    ONESHOT = 2
    CONTINUOUS = 3

    @staticmethod
    def from_recording(recording: RecordingCommand | None):
        if recording is None:
            return _RecordingTrigger.NONE.value
        if recording.toggle_continuous is True:
            # CONTINUOUS toggles (second trigger turns continuous recoding off)
            return _RecordingTrigger.CONTINUOUS.value
        if recording.save_to is None:
            return _RecordingTrigger.ONESHOT.value
        return _RecordingTrigger.SINGLE.value


def _get_trigger_index(
    pulse: QiTriggerCommand | None, active_trigger: bool | int
) -> int:
    if pulse is None and active_trigger is False:
        return 0
    elif pulse is None and active_trigger:
        return Sequencer.CHOKE_PULSE_INDEX
    else:
        return pulse.trigger_index


class _TriggerModules:
    """Class of Sequencer to keep track of running pulse generators."""

    READOUT = 0
    RECORDING = 1
    MANIPULATION = 2
    COUPLING0 = 3
    COUPLING1 = 4
    DIGITAL = 5

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self._trigger_modules_active: list[bool | int] = [False] * 6

    @property
    def is_pulse_active(self) -> bool:
        """Return True if any pulse generator is active/running"""
        return any(self._trigger_modules_active)

    def set_active(
        self,
        readout: Any | None = None,
        rec: Any | None = None,
        manipulation: Any | None = None,
        coupling0: Any | None = None,
        coupling1: Any | None = None,
        digital: Any | None = None,
    ):
        """Marks pulse generators of defined pulses as active/running"""
        self._trigger_modules_active[_TriggerModules.READOUT] = readout is not None
        self._trigger_modules_active[_TriggerModules.RECORDING] = rec is not None
        self._trigger_modules_active[_TriggerModules.MANIPULATION] = (
            manipulation is not None
        )
        self._trigger_modules_active[_TriggerModules.COUPLING0] = coupling0 is not None
        self._trigger_modules_active[_TriggerModules.COUPLING0] = coupling1 is not None
        self._trigger_modules_active[_TriggerModules.DIGITAL] = digital is not None

    def get_trigger_val(
        self,
        readout: PlayReadoutCommand | None = None,
        rec: RecordingCommand | None = None,
        manipulation: PlayCommand | None = None,
        coupling0: PlayCommand | None = None,
        coupling1: PlayCommand | None = None,
        digital: DigitalTriggerCommand | None = None,
    ) -> list[int]:
        """Returns trigger values for defined pulses.
        If a pulse is not defined, but its module is marked active/running,
        the index of the choke pulse is returned.
        After calling the function, all pulse generators are marked as inactive/off."""
        pulse_values = [0] * 6
        pulse_values[_TriggerModules.READOUT] = _get_trigger_index(
            readout, self._trigger_modules_active[_TriggerModules.READOUT]
        )
        pulse_values[_TriggerModules.RECORDING] = _RecordingTrigger.from_recording(rec)
        pulse_values[_TriggerModules.MANIPULATION] = _get_trigger_index(
            manipulation, self._trigger_modules_active[_TriggerModules.MANIPULATION]
        )
        pulse_values[_TriggerModules.COUPLING0] = _get_trigger_index(
            coupling0, self._trigger_modules_active[_TriggerModules.COUPLING0]
        )
        pulse_values[_TriggerModules.COUPLING1] = _get_trigger_index(
            coupling1, self._trigger_modules_active[_TriggerModules.COUPLING1]
        )
        pulse_values[_TriggerModules.DIGITAL] = _get_trigger_index(
            digital, self._trigger_modules_active[_TriggerModules.DIGITAL]
        )

        self.reset()  # active pulses are now choked
        return pulse_values
