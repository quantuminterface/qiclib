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
from unittest import mock

import qiclib.packages.utility as util
from qiclib import QiController
from qiclib.code.qi_pulse import QiPulse
from qiclib.packages.constants import CONTROLLER_CYCLE_TIME
from qiclib.code.qi_sequencer import (
    Sequencer,
    _RecordingTrigger,
    _Register,
    _TriggerModules,
    ForRangeEntry,
)
from qiclib.code.qi_var_definitions import QiExpression, QiOp
from qiclib.code.qi_seq_instructions import (
    SeqTrigger,
    SeqAwaitQubitState,
    SequencerInstruction,
    SeqRegRegFunct3,
    SeqRegRegFunct7,
    SeqRegImmFunct3,
    SeqWaitImm,
    SeqRegImmediateInst,
    SeqRegRegInst,
    SeqLoadUpperImm,
    SeqWaitRegister,
    SeqEnd,
    SeqTriggerWaitRegister,
    SeqLoad,
    SeqStore,
)
from qiclib.code.qi_jobs import (
    QiStateVariable,
    QiVariable,
    QiIntVariable,
    QiTimeVariable,
    QiCell,
    ForRange,
    QiCells,
    Wait,
    cQiDigitalTrigger,
)
from qiclib.code.qi_jobs import (
    cQiPlay,
    cQiPlayReadout,
    cQiWait,
    cQiRecording,
    QiJob,
    _set_job_reference,
    _delete_job_reference,
)
import mocks
from mocks import *

import qiclib.packages.grpc.sequencer_pb2 as sequencer_protos
from mocks.sequencer import MockSequencer


class CalcToSeqCommandTest(unittest.TestCase):
    def setUp(self) -> None:
        self.test_sequencer = Sequencer()
        self.var1 = self.test_sequencer.request_register()
        # initialise var1
        self.var1.value = 0

    def test_add_lower_immediate(self):
        # also test commutative properties; addition with 3 should be possible with a single RegImmediate command
        register = self.test_sequencer.add_calculation(3, QiOp.PLUS, self.var1)

        self.assertIsInstance(
            self.test_sequencer.instruction_list[0], SeqRegImmediateInst
        )

        instr = self.test_sequencer.instruction_list[0]

        if isinstance(instr, SeqRegImmediateInst):
            self.assertEqual(instr.dst_reg, register.adr)

    def test_add_large_immediate(self):
        # large immediate values need to be written to a register first
        self.test_sequencer.add_calculation(
            SequencerInstruction.LOWER_IMM_MAX + 1, QiOp.PLUS, self.var1
        )

        instr = self.test_sequencer.instruction_list[0]
        self.assertIsInstance(instr, SeqLoadUpperImm)
        if isinstance(instr, SeqLoadUpperImm):
            # LOWER_IMM_MAX + 1 would be 0x800; ADDI sign extends it so LUI needs to set the register to 0x0000_1000 to account for that
            # 0x000_1000 + 0xFFFF_F800 = 0x1_0000_0800
            self.assertEqual(instr.immediate, 0x0000_1000)

        instr = self.test_sequencer.instruction_list[1]
        self.assertIsInstance(instr, SeqRegImmediateInst)
        if isinstance(instr, SeqRegImmediateInst):
            self.assertEqual(instr.immediate, 0x800)

        self.assertIsInstance(self.test_sequencer.instruction_list[2], SeqRegRegInst)

    def test_add_negative_large_immediate(self):
        self.test_sequencer.add_calculation(
            SequencerInstruction.LOWER_IMM_MIN - 1, QiOp.PLUS, self.var1
        )

        instr = self.test_sequencer.instruction_list[0]
        self.assertIsInstance(instr, SeqLoadUpperImm)
        if isinstance(instr, SeqLoadUpperImm):
            # LOWER_IMM_MIN - 1 would be 0xFFFFF7FF; LUI needs to set the register to 0xFFFF_F000
            self.assertEqual(instr.immediate, 0xFFFF_F000)

        instr = self.test_sequencer.instruction_list[1]
        self.assertIsInstance(instr, SeqRegImmediateInst)
        if isinstance(instr, SeqRegImmediateInst):
            self.assertEqual(instr.immediate & 0xFFF, 0x7FF)

        self.assertIsInstance(self.test_sequencer.instruction_list[2], SeqRegRegInst)

    def test_subtract_lower_immediate(self):
        self.test_sequencer.add_calculation(
            self.var1, QiOp.MINUS, 3
        )  # immediate instr does not support subtraction, but addition with negative numbers

        self.assertIsInstance(
            self.test_sequencer.instruction_list[0], SeqRegImmediateInst
        )
        instr = self.test_sequencer.instruction_list[0]

        if isinstance(instr, SeqRegImmediateInst):
            self.assertEqual(instr.immediate, -3)  # addition with -3

    def test_subtract_large_immediate(self):
        self.test_sequencer.add_calculation(
            self.var1, QiOp.MINUS, SequencerInstruction.LOWER_IMM_MAX + 1
        )

        self.assertIsInstance(self.test_sequencer.instruction_list[0], SeqLoadUpperImm)
        self.assertIsInstance(
            self.test_sequencer.instruction_list[1], SeqRegImmediateInst
        )
        self.assertIsInstance(self.test_sequencer.instruction_list[2], SeqRegRegInst)

    def test_non_commutative(self):
        self.test_sequencer.add_calculation(3, QiOp.LSH, self.var1)

        self.assertIsInstance(
            self.test_sequencer.instruction_list[0], SeqRegImmediateInst
        )  # 3 to register
        self.assertIsInstance(
            self.test_sequencer.instruction_list[1], SeqRegRegInst
        )  # left shift reg reg command

    def test_non_commutative_large_immediate(self):
        self.test_sequencer.add_calculation(
            SequencerInstruction.LOWER_IMM_MAX + 1, QiOp.LSH, self.var1
        )

        self.assertIsInstance(self.test_sequencer.instruction_list[0], SeqLoadUpperImm)
        self.assertIsInstance(
            self.test_sequencer.instruction_list[1], SeqRegImmediateInst
        )
        self.assertIsInstance(self.test_sequencer.instruction_list[2], SeqRegRegInst)

    def test_add_registers(self):
        var2 = self.test_sequencer.request_register()
        var2.value = 0

        self.test_sequencer.add_calculation(var2, QiOp.PLUS, self.var1)

        self.assertIsInstance(self.test_sequencer.instruction_list[0], SeqRegRegInst)

    def test_exception(self):
        with self.assertRaises(RuntimeError):
            self.test_sequencer.add_calculation(42, QiOp.PLUS, 1337)

    def test_variable_not_initialised(self):
        var2 = self.test_sequencer.request_register()

        with self.assertRaises(RuntimeError):
            self.test_sequencer.add_calculation(var2, QiOp.PLUS, self.var1)


class CellCommandToSeqTest(unittest.TestCase):
    def setUp(self) -> None:
        job = QiJob()
        _set_job_reference(job)
        self.sequencer = Sequencer()
        self.var1 = QiTimeVariable()
        self.var_state = QiStateVariable()
        self.sequencer.add_variable(self.var1)
        # initialise var1
        reg = self.sequencer.get_var_register(self.var1)
        reg.value = 0

        self.var2 = QiTimeVariable()
        self.sequencer.add_variable(self.var2)  # not initialised

        self.sequencer.add_variable(self.var_state)
        self.cell = QiCell(0)

    def tearDown(self) -> None:
        _delete_job_reference()
        return super().tearDown()

    def test_wait_small_immediate(self):
        wait_cmd = cQiWait(
            self.cell,
            util.conv_cycles_to_time(SequencerInstruction.UPPER_IMM_MAX_UNSIGNED),
        )
        self.sequencer.add_wait_cmd(wait_cmd)

        self.assertIsInstance(self.sequencer.instruction_list[0], SeqWaitImm)

    def test_wait_large_immediate(self):
        wait_cmd = cQiWait(
            self.cell,
            util.conv_cycles_to_time(SequencerInstruction.UPPER_IMM_MAX_UNSIGNED + 1),
        )
        self.sequencer.add_wait_cmd(wait_cmd)

        self.assertIsInstance(self.sequencer.instruction_list[0], SeqLoadUpperImm)
        self.assertIsInstance(self.sequencer.instruction_list[1], SeqRegImmediateInst)
        self.assertIsInstance(self.sequencer.instruction_list[2], SeqWaitRegister)

    def test_wait_variable(self):
        wait_cmd = cQiWait(self.cell, self.var1)
        self.sequencer.add_wait_cmd(wait_cmd)

        self.assertIsInstance(self.sequencer.instruction_list[0], SeqWaitRegister)

    def test_wait_QiCalc(self):
        wait_cmd = cQiWait(self.cell, self.var1 + 4e-9)

        # warns that timing might be impeded by using calculations in wait
        with self.assertWarnsRegex(
            UserWarning, "Calculations inside wait might impede timing"
        ):
            self.sequencer.add_wait_cmd(wait_cmd)

        self.assertIsInstance(self.sequencer.instruction_list[0], SeqRegImmediateInst)
        self.assertIsInstance(self.sequencer.instruction_list[1], SeqWaitRegister)

    def test_play_command_no_wait(self):
        play_cmd = cQiPlay(self.cell, QiPulse(length=CONTROLLER_CYCLE_TIME))

        self.sequencer.add_trigger_cmd(play_cmd)

        self.assertIsInstance(self.sequencer.instruction_list[0], SeqTrigger)
        self.assertEqual(len(self.sequencer.instruction_list), 1)

    def test_play_command_wait(self):
        play_cmd = cQiPlay(self.cell, QiPulse(length=CONTROLLER_CYCLE_TIME * 2))

        self.sequencer.add_trigger_cmd(play_cmd)

        self.assertIsInstance(self.sequencer.instruction_list[0], SeqTrigger)
        self.assertIsInstance(self.sequencer.instruction_list[1], SeqWaitImm)

    def test_digital_trigger(self):
        digital_trigger_cmd = cQiDigitalTrigger(self.cell, outputs=[3], length=12e-9)

        self.sequencer.add_trigger_cmd(digital=digital_trigger_cmd)

        self.assertIsInstance(self.sequencer.instruction_list[0], SeqTrigger)

    def test_play_commands_longest_wait(self):
        play_cmd = cQiPlay(self.cell, QiPulse(length=CONTROLLER_CYCLE_TIME * 2))
        readout_cmd = cQiPlayReadout(
            self.cell, QiPulse(length=CONTROLLER_CYCLE_TIME * 3)
        )

        self.sequencer.add_trigger_cmd(play_cmd, readout_cmd)

        self.assertIsInstance(self.sequencer.instruction_list[0], SeqTrigger)

        instr = self.sequencer.instruction_list[1]
        self.assertIsInstance(instr, SeqWaitImm)

        if isinstance(instr, SeqWaitImm):
            self.assertEqual(instr.immediate, 3)

    def test_play_commands_variable_wait_no_follow_up_end_of_body(self):
        # Pulse with variable length and no other pulse as follow up added to the sequencer.
        # end_of_command_body is called and should add a choke pulse to the sequencer
        play_cmd = cQiPlay(self.cell, QiPulse(length=self.var1))

        self.sequencer.add_trigger_cmd(play_cmd)

        self.assertIsInstance(self.sequencer.instruction_list[0], SeqTrigger)
        self.assertIsInstance(
            self.sequencer.instruction_list[1], SeqTriggerWaitRegister
        )
        self.assertTrue(
            self.sequencer._trigger_mods._trigger_modules_active[2]
        )  # variable pulse still active

        self.sequencer.end_of_command_body()

        self.assertIsInstance(
            self.sequencer.instruction_list[2], SeqTrigger
        )  # choke pulse
        self.assertFalse(
            self.sequencer._trigger_mods._trigger_modules_active[2]
        )  # choked so not active anymore

    def test_play_commands_variable_wait_no_follow_up_next_command(self):
        # Pulse with variable length and no other pulse as follow up added to the sequencer.
        # Another command is added, but a choke pulse should be added to the sequencer beforehand
        play_cmd = cQiPlay(self.cell, QiPulse(length=self.var1))

        self.sequencer.add_trigger_cmd(manipulation=play_cmd)

        self.assertIsInstance(self.sequencer.instruction_list[0], SeqTrigger)
        self.assertIsInstance(
            self.sequencer.instruction_list[1], SeqTriggerWaitRegister
        )
        self.assertTrue(
            self.sequencer._trigger_mods._trigger_modules_active[2]
        )  # variable pulse still active

        self.sequencer.add_wait_cmd(cQiWait(None, 50e-9))

        trigger_cmd = self.sequencer.instruction_list[2]  # choke pulse

        if isinstance(trigger_cmd, SeqTrigger):
            # trigger pulse triggers on readout, so choke pulse should be added at manipulation module
            self.assertEqual(
                trigger_cmd._trig_indices[_TriggerModules.MANIPULATION],
                Sequencer.CHOKE_PULSE_INDEX,
            )
        else:
            self.assertIsInstance(trigger_cmd, SeqTrigger)

        self.assertFalse(
            self.sequencer._trigger_mods._trigger_modules_active[2]
        )  # choked so not active anymore

        self.assertIsInstance(
            self.sequencer.instruction_list[3], SeqWaitImm
        )  # choke pulse

    def test_play_commands_variable_wait_follow_up(self):
        # Pulse with variable length and another pulse as follow up added to the sequencer.
        # Second Pulse should deactivate first pulse
        play_cmd1 = cQiPlay(self.cell, QiPulse(length=self.var1))
        play_cmd2 = cQiPlayReadout(
            self.cell, QiPulse(length=CONTROLLER_CYCLE_TIME)
        )  # pulse with no wait time

        self.sequencer.add_trigger_cmd(manipulation=play_cmd1)

        self.assertTrue(
            self.sequencer._trigger_mods._trigger_modules_active[2]
        )  # active pulse

        self.sequencer.add_trigger_cmd(readout=play_cmd2)

        self.assertFalse(
            self.sequencer._trigger_mods._trigger_modules_active[2]
        )  # choked

        self.assertIsInstance(self.sequencer.instruction_list[0], SeqTrigger)
        self.assertIsInstance(
            self.sequencer.instruction_list[1], SeqTriggerWaitRegister
        )

        trigger_cmd = self.sequencer.instruction_list[2]

        if isinstance(trigger_cmd, SeqTrigger):
            # trigger pulse triggers on readout, so choke pulse should be added at manipulation module
            self.assertEqual(
                trigger_cmd._trig_indices[_TriggerModules.MANIPULATION],
                Sequencer.CHOKE_PULSE_INDEX,
            )
        else:
            self.assertIsInstance(trigger_cmd, SeqTrigger)

        self.assertEqual(len(self.sequencer.instruction_list), 3)

    def test_recording_to_sequencer_one_cycle(self):
        rec_cmd = cQiRecording(self.cell, None, None, CONTROLLER_CYCLE_TIME, 0.0)

        self.sequencer.add_trigger_cmd(recording=rec_cmd)

        self.assertIsInstance(self.sequencer.instruction_list[0], SeqTrigger)
        self.assertIsInstance(
            self.sequencer.instruction_list[1], SeqWaitImm
        )  # RECORDING_MODULE_DELAY_CYCLES are added at the Sequencer
        self.assertEqual(len(self.sequencer.instruction_list), 2)

    def test_recording_to_sequencer_wait(self):
        rec_cmd = cQiRecording(
            self.cell, None, None, CONTROLLER_CYCLE_TIME + 20e-9, 20e-9
        )  # Offset should not lengthen wait period

        self.sequencer.add_trigger_cmd(recording=rec_cmd)

        self.assertIsInstance(self.sequencer.instruction_list[0], SeqTrigger)

        instr = self.sequencer.instruction_list[1]
        self.assertIsInstance(instr, SeqWaitImm)

        if isinstance(instr, SeqWaitImm):
            self.assertEqual(
                instr.immediate,
                util.conv_time_to_cycles(CONTROLLER_CYCLE_TIME + 20e-9)
                + self.sequencer.RECORDING_MODULE_DELAY_CYCLES
                - 1,
            )

        self.assertEqual(len(self.sequencer.instruction_list), 2)

    def test_recording_to_sequencer_different_wait_times(self):
        rec_cmd = cQiRecording(self.cell, None, None, CONTROLLER_CYCLE_TIME + 20e-9, 0)
        play_cmd = cQiPlay(self.cell, QiPulse(length=0))

        self.sequencer.add_trigger_cmd(manipulation=play_cmd, recording=rec_cmd)

        self.assertIsInstance(self.sequencer.instruction_list[0], SeqTrigger)
        self.assertIsInstance(self.sequencer.instruction_list[1], SeqWaitImm)
        self.assertEqual(len(self.sequencer.instruction_list), 2)

    def test_state_recording_to_sequencer(self):
        rec_cmd = cQiRecording(
            self.cell, None, self.var_state, CONTROLLER_CYCLE_TIME + 20e-9, 0
        )
        play_cmd = cQiPlay(self.cell, QiPulse(length=0))

        self.sequencer.add_trigger_cmd(manipulation=play_cmd, recording=rec_cmd)

        self.assertIsInstance(self.sequencer.instruction_list[0], SeqTrigger)
        self.assertIsInstance(self.sequencer.instruction_list[1], SeqAwaitQubitState)
        self.assertEqual(len(self.sequencer.instruction_list), 2)

    def test_state_recording_to_sequencer_variable_length(self):
        rec_cmd = cQiRecording(
            self.cell, None, self.var_state, CONTROLLER_CYCLE_TIME + 20e-9, 0
        )
        play_cmd = cQiPlay(self.cell, QiPulse(length=self.var1))

        self.sequencer.add_trigger_cmd(manipulation=play_cmd, recording=rec_cmd)

        self.assertIsInstance(self.sequencer.instruction_list[0], SeqTrigger)
        self.assertIsInstance(
            self.sequencer.instruction_list[1], SeqTriggerWaitRegister
        )
        self.assertIsInstance(self.sequencer.instruction_list[2], SeqTrigger)
        self.assertIsInstance(self.sequencer.instruction_list[3], SeqAwaitQubitState)
        self.assertEqual(len(self.sequencer.instruction_list), 4)

    def test_recording_start_continuous(self):
        rec_cmd = cQiRecording(self.cell, None, None, 80e-9, 0, toggleContinuous=True)
        self.sequencer.add_trigger_cmd(recording=rec_cmd)

        self.assertIsInstance(self.sequencer.instruction_list[0], SeqTrigger)
        self.assertEqual(
            self.sequencer.instruction_list[0]._trig_indices[_TriggerModules.RECORDING],
            _RecordingTrigger.CONTINUOUS.value,
        )
        self.assertEqual(len(self.sequencer.instruction_list), 1)  # No Wait

    def test_recording_stop_continuous(self):
        rec_cmd = cQiRecording(self.cell, None, None, 80e-9, 0, toggleContinuous=True)
        self.sequencer.add_trigger_cmd(recording=rec_cmd)

        self.assertIsInstance(self.sequencer.instruction_list[0], SeqTrigger)
        self.assertEqual(
            self.sequencer.instruction_list[0]._trig_indices[_TriggerModules.RECORDING],
            _RecordingTrigger.CONTINUOUS.value,
        )
        self.assertEqual(len(self.sequencer.instruction_list), 1)  # No Wait

    def test_end_command(self):
        wait_cmd = cQiWait(self.cell, self.var1)
        self.sequencer.add_wait_cmd(wait_cmd)

        self.sequencer.end_of_program()

        self.assertIsInstance(self.sequencer.instruction_list[1], SeqEnd)

    def test_wait_var_not_initialised(self):
        with self.assertRaises(RuntimeError):
            wait_cmd = cQiWait(self.cell, self.var2)
            self.sequencer.add_wait_cmd(wait_cmd)

    def test_pulse_var_not_initialised(self):
        with self.assertRaises(RuntimeError):
            play_cmd = cQiPlay(self.cell, QiPulse(length=self.var2))
            self.sequencer.add_trigger_cmd(play_cmd)


class ImmediateToRegisterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.sequencer = Sequencer()

    def testimmediate_to_register(self):
        dst_reg = self.sequencer.immediate_to_register(21)

        self.assertIsInstance(self.sequencer.instruction_list[0], SeqRegImmediateInst)

        tmp_cmd = self.sequencer.instruction_list[0]

        if isinstance(tmp_cmd, SeqRegImmediateInst):
            self.assertEqual(tmp_cmd.immediate, 21)
            self.assertEqual(tmp_cmd.dst_reg, dst_reg.adr)


class QiCalcToSeq(unittest.TestCase):
    # test if QiCalc-Objects are resolved correctly into separate sequencer commands
    def setUp(self) -> None:
        self.test_sequencer = Sequencer()
        _set_job_reference(QiJob())

    def tearDown(self) -> None:
        _delete_job_reference()
        return super().tearDown()

    def test_qi_calc_add_shift_to_seq(self):
        x = QiVariable(int)
        y = QiVariable(int)

        self.assertEqual(
            len(self.test_sequencer._register_stack), Sequencer.AVAILABLE_REGISTERS
        )

        self.test_sequencer.add_variable(x)
        # initialise x
        reg = self.test_sequencer.get_var_register(x)
        reg.value = 0

        self.test_sequencer.add_variable(y)
        # initialise y
        reg = self.test_sequencer.get_var_register(y)
        reg.value = 0

        qi_calc_test = x + 2 << y

        dst_reg = self.test_sequencer.add_qi_calc(qi_calc_test)

        self.assertIsInstance(
            self.test_sequencer.instruction_list[0], SeqRegImmediateInst
        )
        self.assertIsInstance(self.test_sequencer.instruction_list[1], SeqRegRegInst)

        instr = self.test_sequencer.instruction_list[1]

        if isinstance(instr, SeqRegRegInst):
            self.assertEqual(instr.funct3, SeqRegRegFunct3.SLL_MULH)
            self.assertEqual(instr.funct7, SeqRegRegFunct7.SLL)

            if isinstance(dst_reg, _Register):
                self.assertEqual(dst_reg.adr, instr.dst_reg)

        self.assertEqual(
            len(self.test_sequencer._register_stack), Sequencer.AVAILABLE_REGISTERS - 3
        )
        self.assertEqual(len(self.test_sequencer.instruction_list), 2)
        self.assertNotIn(dst_reg, self.test_sequencer._register_stack)

    def test_qi_calc_shift_add_to_seq(self):
        x = QiVariable(int)
        y = QiVariable(int)

        self.assertEqual(
            len(self.test_sequencer._register_stack), Sequencer.AVAILABLE_REGISTERS
        )

        self.test_sequencer.add_variable(x)
        reg = self.test_sequencer.get_var_register(x)  # initialise x
        reg.value = 0
        self.test_sequencer.add_variable(y)
        reg = self.test_sequencer.get_var_register(y)  # initialise y
        reg.value = 0

        qi_calc_test = x << y + 2

        dst_reg = self.test_sequencer.add_qi_calc(qi_calc_test)

        self.assertIsInstance(
            self.test_sequencer.instruction_list[0], SeqRegImmediateInst
        )
        self.assertIsInstance(self.test_sequencer.instruction_list[1], SeqRegRegInst)

        instr = self.test_sequencer.instruction_list[1]

        if isinstance(instr, SeqRegRegInst):
            self.assertEqual(instr.funct3, SeqRegRegFunct3.SLL_MULH)
            self.assertEqual(instr.funct7, SeqRegRegFunct7.SLL)

            if isinstance(dst_reg, _Register):
                self.assertEqual(dst_reg.adr, instr.dst_reg)

        self.assertEqual(
            len(self.test_sequencer._register_stack), Sequencer.AVAILABLE_REGISTERS - 3
        )
        self.assertEqual(len(self.test_sequencer.instruction_list), 2)
        self.assertNotIn(dst_reg, self.test_sequencer._register_stack)

    def test_qi_calc_add_shift_large_imm(self):
        x = QiVariable(int)
        y = QiVariable(int)

        self.test_sequencer.add_variable(x)
        # initialise x
        reg = self.test_sequencer.get_var_register(x)
        reg.value = 0

        self.test_sequencer.add_variable(y)
        # initialise y
        reg = self.test_sequencer.get_var_register(y)
        reg.value = 0

        qi_calc_test = x + (SequencerInstruction.LOWER_IMM_MAX + 1) << y

        dst_reg = self.test_sequencer.add_qi_calc(qi_calc_test)

        self.assertIsInstance(self.test_sequencer.instruction_list[0], SeqLoadUpperImm)
        self.assertIsInstance(
            self.test_sequencer.instruction_list[1], SeqRegImmediateInst
        )
        self.assertIsInstance(self.test_sequencer.instruction_list[2], SeqRegRegInst)
        self.assertIsInstance(self.test_sequencer.instruction_list[3], SeqRegRegInst)

        instr = self.test_sequencer.instruction_list[3]

        if isinstance(instr, SeqRegRegInst):
            self.assertEqual(instr.funct3, SeqRegRegFunct3.SLL_MULH)
            self.assertEqual(instr.funct7, SeqRegRegFunct7.SLL)

            if isinstance(dst_reg, _Register):
                self.assertEqual(dst_reg.adr, instr.dst_reg)

        self.assertEqual(
            len(self.test_sequencer._register_stack), Sequencer.AVAILABLE_REGISTERS - 3
        )
        self.assertEqual(len(self.test_sequencer.instruction_list), 4)
        self.assertNotIn(dst_reg, self.test_sequencer._register_stack)

    def test_qi_calc_multiply(self):
        x = QiVariable(int)

        self.test_sequencer.add_variable(x)
        # initialise x
        reg = self.test_sequencer.get_var_register(x)
        reg.value = 0

        qi_calc_test = x * (SequencerInstruction.LOWER_IMM_MAX + 1)

        dst_reg = self.test_sequencer.add_qi_calc(qi_calc_test)

        self.assertIsInstance(self.test_sequencer.instruction_list[0], SeqLoadUpperImm)
        self.assertIsInstance(
            self.test_sequencer.instruction_list[1], SeqRegImmediateInst
        )
        self.assertIsInstance(self.test_sequencer.instruction_list[2], SeqRegRegInst)

        instr = self.test_sequencer.instruction_list[2]

        if isinstance(instr, SeqRegRegInst):
            self.assertEqual(instr.funct3, SeqRegRegFunct3.ADD_SUB_MUL)
            self.assertEqual(instr.funct7, SeqRegRegFunct7.MUL)

            if isinstance(dst_reg, _Register):
                self.assertEqual(dst_reg.adr, instr.dst_reg)

        self.assertEqual(
            len(self.test_sequencer._register_stack), Sequencer.AVAILABLE_REGISTERS - 2
        )
        self.assertEqual(len(self.test_sequencer.instruction_list), 3)
        self.assertNotIn(dst_reg, self.test_sequencer._register_stack)

    def test_qi_calc_time_variables(self):
        x = QiTimeVariable()
        y = QiIntVariable()

        self.test_sequencer.add_variable(x)
        # initialise x
        reg = self.test_sequencer.get_var_register(x)
        reg.value = 0

        self.test_sequencer.add_variable(y)
        # initialise y
        reg = self.test_sequencer.get_var_register(y)
        reg.value = 0

        qi_calc_test = (x << y) + 20e-9

        dst_reg = self.test_sequencer.add_qi_calc(qi_calc_test)

        instr = self.test_sequencer.instruction_list

        self.assertIsInstance(instr[0], SeqRegRegInst)

        self.assertIsInstance(instr[1], SeqRegImmediateInst)

        if isinstance(instr[1], SeqRegImmediateInst):
            self.assertEqual(instr[1].funct3, SeqRegImmFunct3.ADD)
            self.assertEqual(instr[1].immediate, util.conv_time_to_cycles(20e-9))

        self.assertEqual(len(self.test_sequencer.instruction_list), 2)
        self.assertNotIn(dst_reg, self.test_sequencer._register_stack)

    def test_qi_calc_length_variables_Error(self):
        x = QiTimeVariable()
        y = QiVariable(float)

        self.test_sequencer.add_variable(x)
        # initialise x
        reg = self.test_sequencer.get_var_register(x)
        reg.value = 0

        self.test_sequencer.add_variable(y)
        # initialise y
        reg = self.test_sequencer.get_var_register(y)
        reg.value = 0

        with self.assertRaises(TypeError):
            qi_calc_test = x << y + 20e-9

    def test_qi_calc_var_not_initialised(self):
        x = QiVariable(int)
        y = QiVariable(int)

        self.test_sequencer.add_variable(x)
        self.test_sequencer.add_variable(y)

        qi_calc_test = x << y + 20

        with self.assertRaises(RuntimeError):
            dst_reg = self.test_sequencer.add_qi_calc(qi_calc_test)

    def test_qi_calc_invalid_registers(self):
        x = QiVariable(int)
        y = QiVariable(int)

        self.assertEqual(
            len(self.test_sequencer._register_stack), Sequencer.AVAILABLE_REGISTERS
        )

        self.test_sequencer.add_variable(x)
        reg_x = self.test_sequencer.get_var_register(x)
        reg_x.value = 0
        reg_x.valid = False

        self.test_sequencer.add_variable(y)
        reg_y = self.test_sequencer.get_var_register(y)
        reg_y.value = 0

        qi_calc_test = x + 2 << y

        dst_reg = self.test_sequencer.add_qi_calc(qi_calc_test)

        self.assertFalse(dst_reg.valid)
        self.assertTrue(reg_y.valid)  # reg_y should not be affected

        self.test_sequencer.release_register(dst_reg)

        self.assertTrue(
            dst_reg.valid
        )  # after releasing register, return to initial valid state


class MemToSeqCommandTest(unittest.TestCase):
    def setUp(self) -> None:
        self.test_sequencer = Sequencer()
        self.var1 = self.test_sequencer.request_register()
        self.base = self.test_sequencer.request_register()

    def test_register_small_offset_load(self):
        self.test_sequencer.add_load_cmd(self.var1, self.base, offset=42)

        instructions = self.test_sequencer.instruction_list

        self.assertIsInstance(instructions[0], SeqLoad)
        self.assertEqual(instructions[0].immediate, 42)
        self.assertEqual(instructions[0].dst_reg, self.var1.adr)
        self.assertEqual(instructions[0].register, self.base.adr)

    def test_load_small_absolute_address(self):
        self.test_sequencer.add_load_cmd(self.var1, None, offset=42)

        instructions = self.test_sequencer.instruction_list

        self.assertIsInstance(instructions[0], SeqLoad)
        self.assertEqual(instructions[0].immediate, 42)
        self.assertEqual(instructions[0].dst_reg, self.var1.adr)
        self.assertEqual(instructions[0].register, self.test_sequencer.reg0.adr)

    def test_load_large_absolute_address(self):
        self.test_sequencer.add_load_cmd(self.var1, None, offset=0xAFFE)

        instructions = self.test_sequencer.instruction_list

        self.assertIsInstance(instructions[0], SeqLoadUpperImm)
        self.assertIsInstance(instructions[1], SeqRegImmediateInst)
        self.assertIsInstance(instructions[2], SeqLoad)
        self.assertEqual(instructions[2].immediate, 0)
        self.assertEqual(instructions[2].dst_reg, self.var1.adr)

    def test_store_constant(self):
        self.test_sequencer.add_store_cmd(QiExpression._from(42), self.base)

        instructions = self.test_sequencer.instruction_list

        self.assertIsInstance(instructions[0], SeqRegImmediateInst)
        self.assertEqual(instructions[0].immediate, 42)
        self.assertIsInstance(instructions[1], SeqStore)
        self.assertEqual(instructions[1].base_reg, self.base.adr)
        self.assertEqual(instructions[1].immediate, 0)
        self.assertEqual(instructions[0].dst_reg, instructions[1].src_reg)

    def test_store_to_offset(self):
        self.test_sequencer.add_store_cmd(QiExpression._from(42), self.base, offset=123)

        instructions = self.test_sequencer.instruction_list

        self.assertIsInstance(instructions[0], SeqRegImmediateInst)
        self.assertEqual(instructions[0].immediate, 42)
        self.assertIsInstance(instructions[1], SeqStore)
        self.assertEqual(instructions[1].base_reg, self.base.adr)
        self.assertEqual(instructions[1].immediate, 123)
        self.assertEqual(instructions[0].dst_reg, instructions[1].src_reg)

    def test_store_calc(self):
        with QiJob() as job:
            var = QiVariable(int, value=0, name="foo")
            self.test_sequencer.add_variable(var)
            calc = var & 0xFFFF0000

        self.test_sequencer.add_store_cmd(calc, self.base, offset=123)

        instructions = self.test_sequencer.instruction_list

        self.assertIsInstance(instructions[-1], SeqStore)
        self.assertEqual(instructions[-1].immediate, 123)
        self.assertEqual(instructions[-1].base_reg, self.base.adr)
        self.assertEqual(instructions[-2].dst_reg, instructions[-1].src_reg)


@mocks.patch(
    pimc, rfdc, unit_cell, servicehub_control, recording, pulse_gen, taskrunner
)
class ForLoopEntryTests(unittest.TestCase):
    def test_get_iteration(self):
        entry = ForRangeEntry(0, 0, 100, 2)
        self.assertEqual(entry.get_iteration(0), 0)
        self.assertEqual(entry.get_iteration(100), 50)
        self.assertEqual(entry.get_iteration(50), 25)

    def test_get_current_running_loop(self):

        with QiJob() as job_int_var:
            q = QiCells(1)
            idx = QiVariable()
            with ForRange(idx, 0, 200):
                Wait(
                    q[0], delay=0
                )  # need a statement or else the loop might be optimized away

        with QiJob() as job_time_var:
            q = QiCells(1)
            idx = QiTimeVariable()
            with ForRange(idx, start=0, step=20e-9, end=2.4e-6):
                Wait(q[0], delay=0)

        class CustomMockSequencer(MockSequencer):
            """
            Class inheriting from `MockSequencer` to enable register modification.
            Note that since __init__ is never called from the mock framework,
            properties will have to be set at a later time.
            """

            def GetAllRegisters(self, _):
                return sequencer_protos.RegisterList(list=self.registers)

            def GetProgramCounter(self, _):
                return sequencer_protos.ProgramCounter(value=self.pc)

        with mock.patch(CustomMockSequencer.module_path, new=CustomMockSequencer) as s:
            qic = QiController("IP")
            exp = job_int_var.create_experiment(qic, use_taskrunner=True)
            # Register 1 contains the current loop index, Register 2 contains the max value
            s.registers = [0, 50, 200] + [0] * 28
            # PC needs to be smaller than the end address of the for loop entry (5)
            s.pc = 0
            curr_loop = exp.get_current_loop()
            self.assertEqual(50, curr_loop)

            exp = job_time_var.create_experiment(qic, use_taskrunner=False)
            # 600 = t_max / 4 ns (== 2.4e-6 / 4e-9)
            # steps of 5 = t_step / 4 ns; 50 = 10
            s.registers = [0, 50, 600] + [0] * 28
            curr_loop = exp.get_current_loop()
            self.assertEqual(10, curr_loop)
