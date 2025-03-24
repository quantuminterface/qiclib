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
from unittest import mock

import mocks
import pytest
from mocks import *
from mocks.sequencer import MockSequencer

import qiclib.packages.grpc.sequencer_pb2 as sequencer_protos
import qiclib.packages.utility as util
from qiclib import QiController
from qiclib.code.qi_command import (
    PlayCommand,
    PlayReadoutCommand,
    RecordingCommand,
    WaitCommand,
)
from qiclib.code.qi_jobs import (
    DigitalTriggerCommand,
    ForRange,
    QiCells,
    QiIntVariable,
    QiJob,
    QiStateVariable,
    QiTimeVariable,
    QiVariable,
    Wait,
)
from qiclib.code.qi_pulse import QiPulse
from qiclib.code.qi_seq_instructions import (
    SeqAwaitQubitState,
    SeqEnd,
    SeqLoad,
    SeqLoadUpperImm,
    SeqRegImmediateInst,
    SeqRegImmFunct3,
    SeqRegRegFunct3,
    SeqRegRegFunct7,
    SeqRegRegInst,
    SeqStore,
    SeqTrigger,
    SeqTriggerWaitRegister,
    SequencerInstruction,
    SeqWaitImm,
    SeqWaitRegister,
)
from qiclib.code.qi_sequencer import (
    ForRangeEntry,
    Sequencer,
    _RecordingTrigger,
    _TriggerModules,
)
from qiclib.code.qi_var_definitions import QiExpression, QiOp
from qiclib.packages.constants import CONTROLLER_CYCLE_TIME


@pytest.fixture
def test_sequencer():
    return Sequencer()


@pytest.fixture
def var1(test_sequencer):
    var1 = test_sequencer.request_register()
    var1.value = 0
    return var1


def test_add_lower_immediate(test_sequencer, var1):
    # also test commutative properties; addition with 3 should be possible with a single RegImmediate command
    register = test_sequencer.add_calculation(3, QiOp.PLUS, var1)
    instr = test_sequencer.instruction_list[0]

    assert isinstance(instr, SeqRegImmediateInst)

    assert instr.dst_reg == register.adr


def test_add_immediate(test_sequencer: Sequencer, var1):
    # also test commutative properties; addition with 3 should be possible with a single RegImmediate command
    test_sequencer.immediate_to_register(0x5FF000)
    assert len(test_sequencer.instruction_list) == 1


def test_add_large_immediate(test_sequencer, var1):
    # large immediate values need to be written to a register first
    test_sequencer.add_calculation(
        SequencerInstruction.LOWER_IMM_MAX + 1, QiOp.PLUS, var1
    )

    instr = test_sequencer.instruction_list[0]
    assert isinstance(instr, SeqLoadUpperImm)
    assert instr.immediate == 0x0000_1000

    instr = test_sequencer.instruction_list[1]
    assert isinstance(instr, SeqRegImmediateInst)
    assert instr.immediate == 0x800

    assert isinstance(test_sequencer.instruction_list[2], SeqRegRegInst)


def test_add_negative_large_immediate(test_sequencer, var1):
    test_sequencer.add_calculation(
        SequencerInstruction.LOWER_IMM_MIN - 1, QiOp.PLUS, var1
    )

    instr = test_sequencer.instruction_list[0]
    assert isinstance(instr, SeqLoadUpperImm)
    assert instr.immediate == 0xFFFF_F000

    instr = test_sequencer.instruction_list[1]
    assert isinstance(instr, SeqRegImmediateInst)
    assert instr.immediate & 0xFFF == 0x7FF

    assert isinstance(test_sequencer.instruction_list[2], SeqRegRegInst)


def test_subtract_lower_immediate(test_sequencer, var1):
    # immediate instr does not support subtraction, but addition with negative numbers
    test_sequencer.add_calculation(var1, QiOp.MINUS, 3)

    instr = test_sequencer.instruction_list[0]
    assert isinstance(instr, SeqRegImmediateInst)
    assert instr.immediate == -3  # addition with -3


def test_subtract_large_immediate(test_sequencer, var1):
    test_sequencer.add_calculation(
        var1, QiOp.MINUS, SequencerInstruction.LOWER_IMM_MAX + 1
    )

    assert isinstance(test_sequencer.instruction_list[0], SeqLoadUpperImm)
    assert isinstance(test_sequencer.instruction_list[1], SeqRegImmediateInst)
    assert isinstance(test_sequencer.instruction_list[2], SeqRegRegInst)


def test_non_commutative(test_sequencer, var1):
    test_sequencer.add_calculation(3, QiOp.LSH, var1)

    assert isinstance(
        test_sequencer.instruction_list[0], SeqRegImmediateInst
    )  # 3 to register
    assert isinstance(
        test_sequencer.instruction_list[1], SeqRegRegInst
    )  # left shift reg reg command


def test_non_commutative_large_immediate(test_sequencer, var1):
    test_sequencer.add_calculation(
        SequencerInstruction.LOWER_IMM_MAX + 1, QiOp.LSH, var1
    )

    assert isinstance(test_sequencer.instruction_list[0], SeqLoadUpperImm)
    assert isinstance(test_sequencer.instruction_list[1], SeqRegImmediateInst)
    assert isinstance(test_sequencer.instruction_list[2], SeqRegRegInst)


def test_add_registers(test_sequencer, var1):
    var2 = test_sequencer.request_register()
    var2.value = 0

    test_sequencer.add_calculation(var2, QiOp.PLUS, var1)

    assert isinstance(test_sequencer.instruction_list[0], SeqRegRegInst)


def test_exception(test_sequencer):
    with pytest.raises(RuntimeError):
        test_sequencer.add_calculation(42, QiOp.PLUS, 1337)


def test_variable_not_initialised(test_sequencer, var1):
    var2 = test_sequencer.request_register()

    with pytest.raises(RuntimeError):
        test_sequencer.add_calculation(var2, QiOp.PLUS, var1)


class TestCellCommandToSeq:
    @pytest.fixture
    def test_job(self):
        with QiJob() as job:
            QiCells(1)
            yield job

    @pytest.fixture
    def test_cell(self, test_job):
        return test_job.cells[0]

    @pytest.fixture
    def test_variable(self, test_sequencer):
        var = QiTimeVariable()
        test_sequencer.add_variable(var)
        # initialise var1
        reg = test_sequencer.get_var_register(var)
        reg.value = 0
        return var

    @pytest.fixture
    def test_state_variable(self, test_sequencer):
        var = QiStateVariable()
        test_sequencer.add_variable(var)
        return var

    @pytest.fixture
    def test_uninitialized_variable(self, test_sequencer):
        var = QiTimeVariable()
        test_sequencer.add_variable(var)
        # not initialised
        return var

    def test_wait_small_immediate(self, test_cell, test_sequencer):
        wait_cmd = WaitCommand(
            test_cell,
            util.conv_cycles_to_time(SequencerInstruction.UPPER_IMM_MAX_UNSIGNED),
        )
        test_sequencer.add_wait_cmd(wait_cmd)

        assert isinstance(test_sequencer.instruction_list[0], SeqWaitImm)

    def test_wait_large_immediate(self, test_cell, test_sequencer):
        wait_cmd = WaitCommand(
            test_cell,
            util.conv_cycles_to_time(SequencerInstruction.UPPER_IMM_MAX_UNSIGNED + 1),
        )
        test_sequencer.add_wait_cmd(wait_cmd)

        assert isinstance(test_sequencer.instruction_list[0], SeqLoadUpperImm)
        assert isinstance(test_sequencer.instruction_list[1], SeqRegImmediateInst)
        assert isinstance(test_sequencer.instruction_list[2], SeqWaitRegister)

    def test_wait_variable(self, test_cell, test_sequencer, test_variable):
        wait_cmd = WaitCommand(test_cell, test_variable)
        test_sequencer.add_wait_cmd(wait_cmd)

        assert isinstance(test_sequencer.instruction_list[0], SeqWaitRegister)

    def test_wait_QiCalc(self, test_cell, test_sequencer, test_variable):
        wait_cmd = WaitCommand(test_cell, test_variable + 4e-9)

        # warns that timing might be impeded by using calculations in wait
        with pytest.warns(
            UserWarning, match="Calculations inside wait might impede timing"
        ):
            test_sequencer.add_wait_cmd(wait_cmd)

        assert isinstance(test_sequencer.instruction_list[0], SeqRegImmediateInst)
        assert isinstance(test_sequencer.instruction_list[1], SeqWaitRegister)

    def test_play_command_no_wait(self, test_cell, test_sequencer):
        play_cmd = PlayCommand(test_cell, QiPulse(length=CONTROLLER_CYCLE_TIME))

        test_sequencer.add_trigger_cmd(play_cmd)

        assert isinstance(test_sequencer.instruction_list[0], SeqTrigger)
        assert len(test_sequencer.instruction_list) == 1

    def test_play_command_wait(self, test_cell, test_sequencer):
        play_cmd = PlayCommand(test_cell, QiPulse(length=CONTROLLER_CYCLE_TIME * 2))

        test_sequencer.add_trigger_cmd(play_cmd)

        assert isinstance(test_sequencer.instruction_list[0], SeqTrigger)
        assert isinstance(test_sequencer.instruction_list[1], SeqWaitImm)

    def test_digital_trigger(self, test_cell, test_sequencer):
        digital_trigger_cmd = DigitalTriggerCommand(
            test_cell, outputs=[3], length=12e-9
        )

        test_sequencer.add_trigger_cmd(digital=digital_trigger_cmd)

        assert isinstance(test_sequencer.instruction_list[0], SeqTrigger)

    def test_play_commands_longest_wait(self, test_cell, test_sequencer):
        play_cmd = PlayCommand(test_cell, QiPulse(length=CONTROLLER_CYCLE_TIME * 2))
        readout_cmd = PlayReadoutCommand(
            test_cell, QiPulse(length=CONTROLLER_CYCLE_TIME * 3)
        )

        test_sequencer.add_trigger_cmd(play_cmd, readout_cmd)

        assert isinstance(test_sequencer.instruction_list[0], SeqTrigger)

        instr = test_sequencer.instruction_list[1]
        assert isinstance(instr, SeqWaitImm)

        if isinstance(instr, SeqWaitImm):
            assert instr.immediate == 3

    def test_play_commands_variable_wait_no_follow_up_end_of_body(
        self, test_cell, test_sequencer, test_variable
    ):
        # Pulse with variable length and no other pulse as follow up added to the sequencer.
        # end_of_command_body is called and should add a choke pulse to the sequencer
        play_cmd = PlayCommand(test_cell, QiPulse(length=test_variable))

        test_sequencer.add_trigger_cmd(play_cmd)

        assert isinstance(test_sequencer.instruction_list[0], SeqTrigger)
        assert isinstance(test_sequencer.instruction_list[1], SeqTriggerWaitRegister)
        assert test_sequencer._trigger_mods._trigger_modules_active[
            2
        ]  # variable pulse still active

        test_sequencer.end_of_command_body()

        assert isinstance(test_sequencer.instruction_list[2], SeqTrigger)  # choke pulse
        assert not test_sequencer._trigger_mods._trigger_modules_active[
            2
        ]  # choked so not active anymore

    def test_play_commands_variable_wait_no_follow_up_next_command(
        self, test_cell, test_sequencer, test_variable
    ):
        # Pulse with variable length and no other pulse as follow up added to the sequencer.
        # Another command is added, but a choke pulse should be added to the sequencer beforehand
        play_cmd = PlayCommand(test_cell, QiPulse(length=test_variable))

        test_sequencer.add_trigger_cmd(manipulation=play_cmd)

        assert isinstance(test_sequencer.instruction_list[0], SeqTrigger)
        assert isinstance(test_sequencer.instruction_list[1], SeqTriggerWaitRegister)
        assert test_sequencer._trigger_mods._trigger_modules_active[
            2
        ]  # variable pulse still active

        test_sequencer.add_wait_cmd(WaitCommand(None, 50e-9))

        trigger_cmd = test_sequencer.instruction_list[2]  # choke pulse

        if isinstance(trigger_cmd, SeqTrigger):
            # trigger pulse triggers on readout, so choke pulse should be added at manipulation module
            assert (
                trigger_cmd._trig_indices[_TriggerModules.MANIPULATION]
                == Sequencer.CHOKE_PULSE_INDEX
            )
        else:
            assert isinstance(trigger_cmd, SeqTrigger)

        assert not test_sequencer._trigger_mods._trigger_modules_active[
            2
        ]  # choked so not active anymore

        assert isinstance(test_sequencer.instruction_list[3], SeqWaitImm)  # choke pulse

    def test_play_commands_variable_wait_follow_up(
        self, test_cell, test_sequencer, test_variable
    ):
        # Pulse with variable length and another pulse as follow up added to the sequencer.
        # Second Pulse should deactivate first pulse
        play_cmd1 = PlayCommand(test_cell, QiPulse(length=test_variable))
        play_cmd2 = PlayReadoutCommand(
            test_cell, QiPulse(length=CONTROLLER_CYCLE_TIME)
        )  # pulse with no wait time

        test_sequencer.add_trigger_cmd(manipulation=play_cmd1)

        assert test_sequencer._trigger_mods._trigger_modules_active[2]  # active pulse

        test_sequencer.add_trigger_cmd(readout=play_cmd2)

        assert not test_sequencer._trigger_mods._trigger_modules_active[2]  # choked

        assert isinstance(test_sequencer.instruction_list[0], SeqTrigger)
        assert isinstance(test_sequencer.instruction_list[1], SeqTriggerWaitRegister)

        trigger_cmd = test_sequencer.instruction_list[2]

        if isinstance(trigger_cmd, SeqTrigger):
            # trigger pulse triggers on readout, so choke pulse should be added at manipulation module
            assert (
                trigger_cmd._trig_indices[_TriggerModules.MANIPULATION]
                == Sequencer.CHOKE_PULSE_INDEX
            )
        else:
            assert isinstance(trigger_cmd, SeqTrigger)

        assert len(test_sequencer.instruction_list) == 3

    def test_recording_to_sequencer_one_cycle(self, test_cell, test_sequencer):
        rec_cmd = RecordingCommand(test_cell, None, None, CONTROLLER_CYCLE_TIME, 0.0)

        test_sequencer.add_trigger_cmd(recording=rec_cmd)

        assert isinstance(test_sequencer.instruction_list[0], SeqTrigger)
        assert isinstance(
            test_sequencer.instruction_list[1], SeqWaitImm
        )  # RECORDING_MODULE_DELAY_CYCLES are added at the Sequencer
        assert len(test_sequencer.instruction_list) == 2

    def test_recording_to_sequencer_wait(self, test_cell, test_sequencer):
        rec_cmd = RecordingCommand(
            test_cell, None, None, CONTROLLER_CYCLE_TIME + 20e-9, 20e-9
        )  # Offset should not lengthen wait period

        test_sequencer.add_trigger_cmd(recording=rec_cmd)

        assert isinstance(test_sequencer.instruction_list[0], SeqTrigger)

        instr = test_sequencer.instruction_list[1]
        assert isinstance(instr, SeqWaitImm)

        if isinstance(instr, SeqWaitImm):
            assert instr.immediate == (
                util.conv_time_to_cycles(CONTROLLER_CYCLE_TIME + 20e-9)
                + test_sequencer.RECORDING_MODULE_DELAY_CYCLES
                - 1
            )

        assert len(test_sequencer.instruction_list) == 2

    def test_recording_to_sequencer_different_wait_times(
        self, test_cell, test_sequencer
    ):
        rec_cmd = RecordingCommand(
            test_cell, None, None, CONTROLLER_CYCLE_TIME + 20e-9, 0
        )
        play_cmd = PlayCommand(test_cell, QiPulse(length=0))

        test_sequencer.add_trigger_cmd(manipulation=play_cmd, recording=rec_cmd)

        assert isinstance(test_sequencer.instruction_list[0], SeqTrigger)
        assert isinstance(test_sequencer.instruction_list[1], SeqWaitImm)
        assert len(test_sequencer.instruction_list) == 2

    def test_state_recording_to_sequencer(
        self, test_cell, test_sequencer, test_state_variable
    ):
        rec_cmd = RecordingCommand(
            test_cell, None, test_state_variable, CONTROLLER_CYCLE_TIME + 20e-9, 0
        )
        play_cmd = PlayCommand(test_cell, QiPulse(length=0))

        test_sequencer.add_trigger_cmd(manipulation=play_cmd, recording=rec_cmd)

        assert isinstance(test_sequencer.instruction_list[0], SeqTrigger)
        assert isinstance(test_sequencer.instruction_list[1], SeqAwaitQubitState)
        assert len(test_sequencer.instruction_list) == 2

    def test_state_recording_to_sequencer_variable_length(
        self, test_cell, test_sequencer, test_variable, test_state_variable
    ):
        rec_cmd = RecordingCommand(
            test_cell, None, test_state_variable, CONTROLLER_CYCLE_TIME + 20e-9, 0
        )
        play_cmd = PlayCommand(test_cell, QiPulse(length=test_variable))

        test_sequencer.add_trigger_cmd(manipulation=play_cmd, recording=rec_cmd)

        assert isinstance(test_sequencer.instruction_list[0], SeqTrigger)
        assert isinstance(test_sequencer.instruction_list[1], SeqTriggerWaitRegister)
        assert isinstance(test_sequencer.instruction_list[2], SeqTrigger)
        assert isinstance(test_sequencer.instruction_list[3], SeqAwaitQubitState)
        assert len(test_sequencer.instruction_list) == 4

    def test_recording_start_continuous(self, test_cell, test_sequencer):
        rec_cmd = RecordingCommand(
            test_cell, None, None, 80e-9, 0, toggle_continuous=True
        )
        test_sequencer.add_trigger_cmd(recording=rec_cmd)

        assert isinstance(test_sequencer.instruction_list[0], SeqTrigger)
        assert (
            test_sequencer.instruction_list[0]._trig_indices[_TriggerModules.RECORDING]
            == _RecordingTrigger.CONTINUOUS.value
        )
        assert len(test_sequencer.instruction_list) == 1  # No Wait

    def test_recording_stop_continuous(self, test_cell, test_sequencer):
        rec_cmd = RecordingCommand(
            test_cell, None, None, 80e-9, 0, toggle_continuous=True
        )
        test_sequencer.add_trigger_cmd(recording=rec_cmd)

        assert isinstance(test_sequencer.instruction_list[0], SeqTrigger)
        assert (
            test_sequencer.instruction_list[0]._trig_indices[_TriggerModules.RECORDING]
            == _RecordingTrigger.CONTINUOUS.value
        )
        assert len(test_sequencer.instruction_list) == 1  # No Wait

    def test_end_command(self, test_cell, test_sequencer, test_variable):
        wait_cmd = WaitCommand(test_cell, test_variable)
        test_sequencer.add_wait_cmd(wait_cmd)

        test_sequencer.end_of_program()

        assert isinstance(test_sequencer.instruction_list[1], SeqEnd)

    def test_wait_var_not_initialised(
        self, test_cell, test_sequencer, test_uninitialized_variable
    ):
        with pytest.raises(RuntimeError):
            wait_cmd = WaitCommand(test_cell, test_uninitialized_variable)
            test_sequencer.add_wait_cmd(wait_cmd)

    def test_pulse_var_not_initialised(
        self, test_cell, test_sequencer, test_uninitialized_variable
    ):
        with pytest.raises(RuntimeError):
            play_cmd = PlayCommand(
                test_cell, QiPulse(length=test_uninitialized_variable)
            )
            test_sequencer.add_trigger_cmd(play_cmd)


def testimmediate_to_register(test_sequencer):
    dst_reg = test_sequencer.immediate_to_register(21)

    tmp_cmd = test_sequencer.instruction_list[0]

    assert isinstance(tmp_cmd, SeqRegImmediateInst)
    assert tmp_cmd.immediate == 21
    assert tmp_cmd.dst_reg == dst_reg.adr


class TestQiCalcToSeq:
    """
    Test if QiCalc-Objects are resolved correctly into separate sequencer commands
    """

    @pytest.fixture(autouse=True)
    def qi_job(self):
        with QiJob() as job:
            yield job

    @pytest.fixture
    def qi_variables(self, test_sequencer):
        x = QiVariable(int)
        y = QiVariable(int)
        test_sequencer.add_variable(x)
        reg_x = test_sequencer.get_var_register(x)
        reg_x.value = 0
        test_sequencer.add_variable(y)
        reg_y = test_sequencer.get_var_register(y)
        reg_y.value = 0
        return x, y

    @pytest.fixture
    def qi_time_variables(self, test_sequencer):
        x = QiTimeVariable()
        y = QiIntVariable()
        test_sequencer.add_variable(x)
        reg_x = test_sequencer.get_var_register(x)
        reg_x.value = 0
        test_sequencer.add_variable(y)
        reg_y = test_sequencer.get_var_register(y)
        reg_y.value = 0
        return x, y

    def test_qi_calc_add_shift_to_seq(self, test_sequencer, qi_variables):
        x, y = qi_variables

        qi_calc_test = x + 2 << y
        dst_reg = test_sequencer.add_qi_calc(qi_calc_test)

        assert isinstance(test_sequencer.instruction_list[0], SeqRegImmediateInst)
        assert isinstance(test_sequencer.instruction_list[1], SeqRegRegInst)

        instr = test_sequencer.instruction_list[1]
        assert instr.funct3 == SeqRegRegFunct3.SLL_MULH
        assert instr.funct7 == SeqRegRegFunct7.SLL
        assert dst_reg.adr == instr.dst_reg

        assert len(test_sequencer._register_stack) == Sequencer.AVAILABLE_REGISTERS - 3
        assert len(test_sequencer.instruction_list) == 2
        assert dst_reg not in test_sequencer._register_stack

    def test_qi_calc_shift_add_to_seq(self, test_sequencer, qi_variables):
        x, y = qi_variables

        qi_calc_test = x << y + 2
        dst_reg = test_sequencer.add_qi_calc(qi_calc_test)

        assert isinstance(test_sequencer.instruction_list[0], SeqRegImmediateInst)
        assert isinstance(test_sequencer.instruction_list[1], SeqRegRegInst)

        instr = test_sequencer.instruction_list[1]
        assert instr.funct3 == SeqRegRegFunct3.SLL_MULH
        assert instr.funct7 == SeqRegRegFunct7.SLL
        assert dst_reg.adr == instr.dst_reg

        assert len(test_sequencer._register_stack) == Sequencer.AVAILABLE_REGISTERS - 3
        assert len(test_sequencer.instruction_list) == 2
        assert dst_reg not in test_sequencer._register_stack

    def test_qi_calc_add_shift_large_imm(self, test_sequencer, qi_variables):
        x, y = qi_variables

        qi_calc_test = x + (SequencerInstruction.LOWER_IMM_MAX + 1) << y
        dst_reg = test_sequencer.add_qi_calc(qi_calc_test)

        assert isinstance(test_sequencer.instruction_list[0], SeqLoadUpperImm)
        assert isinstance(test_sequencer.instruction_list[1], SeqRegImmediateInst)
        assert isinstance(test_sequencer.instruction_list[2], SeqRegRegInst)
        assert isinstance(test_sequencer.instruction_list[3], SeqRegRegInst)

        instr = test_sequencer.instruction_list[3]
        assert instr.funct3 == SeqRegRegFunct3.SLL_MULH
        assert instr.funct7 == SeqRegRegFunct7.SLL
        assert dst_reg.adr == instr.dst_reg

        assert len(test_sequencer._register_stack) == Sequencer.AVAILABLE_REGISTERS - 3
        assert len(test_sequencer.instruction_list) == 4
        assert dst_reg not in test_sequencer._register_stack

    def test_qi_calc_multiply(self, test_sequencer):
        x = QiVariable(int)
        test_sequencer.add_variable(x)
        reg = test_sequencer.get_var_register(x)
        reg.value = 0

        qi_calc_test = x * (SequencerInstruction.LOWER_IMM_MAX + 1)
        dst_reg = test_sequencer.add_qi_calc(qi_calc_test)

        assert isinstance(test_sequencer.instruction_list[0], SeqLoadUpperImm)
        assert isinstance(test_sequencer.instruction_list[1], SeqRegImmediateInst)
        assert isinstance(test_sequencer.instruction_list[2], SeqRegRegInst)

        instr = test_sequencer.instruction_list[2]
        assert instr.funct3 == SeqRegRegFunct3.ADD_SUB_MUL
        assert instr.funct7 == SeqRegRegFunct7.MUL
        assert dst_reg.adr == instr.dst_reg

        assert len(test_sequencer._register_stack) == Sequencer.AVAILABLE_REGISTERS - 2
        assert len(test_sequencer.instruction_list) == 3
        assert dst_reg not in test_sequencer._register_stack

    def test_qi_calc_time_variables(self, test_sequencer, qi_time_variables):
        x, y = qi_time_variables

        qi_calc_test = (x << y) + 20e-9
        dst_reg = test_sequencer.add_qi_calc(qi_calc_test)

        instr = test_sequencer.instruction_list
        assert isinstance(instr[0], SeqRegRegInst)
        assert isinstance(instr[1], SeqRegImmediateInst)
        assert instr[1].funct3 == SeqRegImmFunct3.ADD
        assert instr[1].immediate == util.conv_time_to_cycles(20e-9)

        assert len(test_sequencer.instruction_list) == 2
        assert dst_reg not in test_sequencer._register_stack

    def test_qi_calc_length_variables_Error(self, test_sequencer):
        x = QiTimeVariable()
        y = QiVariable(float)
        test_sequencer.add_variable(x)
        reg = test_sequencer.get_var_register(x)
        reg.value = 0
        test_sequencer.add_variable(y)
        reg = test_sequencer.get_var_register(y)
        reg.value = 0

        with pytest.raises(TypeError):
            _qi_calc_test = x << y + 20e-9

    def test_qi_calc_var_not_initialised(self, test_sequencer):
        x = QiVariable(int)
        y = QiVariable(int)
        test_sequencer.add_variable(x)
        test_sequencer.add_variable(y)

        qi_calc_test = x << y + 20

        with pytest.raises(RuntimeError):
            _dst_reg = test_sequencer.add_qi_calc(qi_calc_test)

    def test_qi_calc_invalid_registers(self, test_sequencer):
        x = QiVariable(int)
        y = QiVariable(int)
        test_sequencer.add_variable(x)
        reg_x = test_sequencer.get_var_register(x)
        reg_x.value = 0
        reg_x.valid = False
        test_sequencer.add_variable(y)
        reg_y = test_sequencer.get_var_register(y)
        reg_y.value = 0

        qi_calc_test = x + 2 << y
        dst_reg = test_sequencer.add_qi_calc(qi_calc_test)

        assert not dst_reg.valid
        assert reg_y.valid

        test_sequencer.release_register(dst_reg)
        assert dst_reg.valid


class TestMemToSeqCommand:
    @pytest.fixture
    def base(self, test_sequencer):
        return test_sequencer.request_register()

    @pytest.fixture
    def var(self, test_sequencer):
        var1 = test_sequencer.request_register()
        var1.value = 0
        return var1

    def test_register_small_offset_load(self, test_sequencer, var, base):
        test_sequencer.add_load_cmd(var, base, offset=42)

        instructions = test_sequencer.instruction_list

        assert isinstance(instructions[0], SeqLoad)
        assert instructions[0].immediate == 42
        assert instructions[0].dst_reg == var.adr
        assert instructions[0].register == base.adr

    def test_load_small_absolute_address(self, test_sequencer, var):
        test_sequencer.add_load_cmd(var, None, offset=42)

        instructions = test_sequencer.instruction_list

        assert isinstance(instructions[0], SeqLoad)
        assert instructions[0].immediate == 42
        assert instructions[0].dst_reg == var.adr
        assert instructions[0].register == test_sequencer.reg0.adr

    def test_load_large_absolute_address(self, test_sequencer, var):
        test_sequencer.add_load_cmd(var, None, offset=0xAFFE)

        instructions = test_sequencer.instruction_list

        assert isinstance(instructions[0], SeqLoadUpperImm)
        assert isinstance(instructions[1], SeqRegImmediateInst)
        assert isinstance(instructions[2], SeqLoad)
        assert instructions[2].immediate == 0
        assert instructions[2].dst_reg == var.adr

    def test_store_constant(self, test_sequencer, base):
        test_sequencer.add_store_cmd(QiExpression._from(42), base)

        instructions = test_sequencer.instruction_list

        assert isinstance(instructions[0], SeqRegImmediateInst)
        assert instructions[0].immediate == 42
        assert isinstance(instructions[1], SeqStore)
        assert instructions[1].base_reg == base.adr
        assert instructions[1].immediate == 0
        assert instructions[0].dst_reg == instructions[1].src_reg

    def test_store_to_offset(self, test_sequencer, base):
        test_sequencer.add_store_cmd(QiExpression._from(42), base, offset=123)

        instructions = test_sequencer.instruction_list

        assert isinstance(instructions[0], SeqRegImmediateInst)
        assert instructions[0].immediate == 42
        assert isinstance(instructions[1], SeqStore)
        assert instructions[1].base_reg == base.adr
        assert instructions[1].immediate == 123
        assert instructions[0].dst_reg == instructions[1].src_reg

    def test_store_calc(self, test_sequencer, base):
        with QiJob():
            var = QiVariable(int, value=0, name="foo")
            test_sequencer.add_variable(var)
            calc = var & 0xFFFF0000

        test_sequencer.add_store_cmd(calc, base, offset=123)

        instructions = test_sequencer.instruction_list

        assert isinstance(instructions[-1], SeqStore)
        assert instructions[-1].immediate == 123
        assert instructions[-1].base_reg == base.adr
        assert instructions[-2].dst_reg == instructions[-1].src_reg


@mocks.patch(
    pimc, rfdc, unit_cell, servicehub_control, recording, pulse_gen, taskrunner
)
class TestsForLoopEntries:
    def test_get_iteration(self):
        entry = ForRangeEntry(0, 0, 100, 2)
        assert entry.get_iteration(0) == 0
        assert entry.get_iteration(100) == 50
        assert entry.get_iteration(50) == 25

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
            assert curr_loop == 50

            exp = job_time_var.create_experiment(qic, use_taskrunner=False)
            # 600 = t_max / 4 ns (== 2.4e-6 / 4e-9)
            # steps of 5 = t_step / 4 ns; 50 = 10
            s.registers = [0, 50, 600] + [0] * 28
            curr_loop = exp.get_current_loop()
            assert curr_loop == 10
