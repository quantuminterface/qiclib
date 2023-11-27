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
import qiclib.packages.utility as util
import qiclib.code.qi_visitor as qv
from qiclib.code.qi_prog_builder import QiCmdExcludeVar, ProgramBuilderVisitor
from qiclib.code.qi_pulse import QiPulse
from qiclib.code.qi_jobs import (
    Else,
    QiVariable,
    QiTimeVariable,
    Play,
    PlayReadout,
    QiJob,
    Recording,
    Wait,
    Assign,
    If,
    ForRange,
    Parallel,
    QiCell,
    QiCells,
    ASM,
)
from qiclib.code.qi_jobs import Sync, cQiWait, _set_job_reference, _delete_job_reference
from qiclib.code.qi_sequencer import Sequencer, _TriggerModules
from qiclib.code.qi_seq_instructions import (
    SeqCellSync,
    SeqLoadUpperImm,
    SeqTriggerWaitRegister,
    SeqEnd,
    SeqTrigger,
    SeqBranchFunct3,
    SeqWaitRegister,
    SeqBranch,
    SeqJump,
    SeqRegImmediateInst,
    SeqWaitImm,
    SeqRegImmFunct3,
    SeqStore,
    SeqLoad,
)


class UnrollLoopTest(unittest.TestCase):
    def setUp(self) -> None:
        self.rec_length = 200e-9
        with QiJob(skip_nco_sync=True) as self.job1:
            q = QiCells(2)
            var1 = QiTimeVariable()
            with ForRange(var1, 0, 24e-9, 4e-9):
                Play(q[0], QiPulse(length=var1))
                Play(q[0], QiPulse(length=24e-9))
                Play(q[1], QiPulse(length=var1))
                Play(q[1], QiPulse(length=24e-9))

        with QiJob(skip_nco_sync=True) as self.job2:
            q = QiCells(1)
            var2 = QiTimeVariable()
            with ForRange(var2, 0, 24e-9, 4e-9):
                Play(q[0], QiPulse(length=24e-9))
                PlayReadout(q[0], QiPulse(length=var2))
                Recording(q[0], self.rec_length, save_to="result")

    def test_unroll_start(self):
        self.job1._build_program()

        sequencer = self.job1.cell_seq_dict[self.job1.cells[0]]

        # unrolled loop 0
        # set variable to 0
        self.assertIsInstance(sequencer.instruction_list[0], SeqRegImmediateInst)
        # trigger 24e-9 unrolled loop
        self.assertIsInstance(sequencer.instruction_list[1], SeqTrigger)
        # Wait 24e-9
        self.assertIsInstance(sequencer.instruction_list[2], SeqWaitImm)

        # unrolled loop 1
        # set variable to 1
        self.assertIsInstance(sequencer.instruction_list[3], SeqRegImmediateInst)
        # trigger var1 = 1
        self.assertIsInstance(sequencer.instruction_list[4], SeqTrigger)
        # trigger 24e-9 unrolled loop
        self.assertIsInstance(sequencer.instruction_list[5], SeqTrigger)
        # Wait 24e-9
        self.assertIsInstance(sequencer.instruction_list[6], SeqWaitImm)

        # actual loop
        # end_val to register
        self.assertIsInstance(sequencer.instruction_list[7], SeqRegImmediateInst)
        # load new start value 4e-9
        self.assertIsInstance(sequencer.instruction_list[8], SeqRegImmediateInst)
        # Branch loop value check
        self.assertIsInstance(sequencer.instruction_list[9], SeqBranch)
        # trigger var
        self.assertIsInstance(sequencer.instruction_list[10], SeqTrigger)
        # Wait var
        self.assertIsInstance(sequencer.instruction_list[11], SeqTriggerWaitRegister)
        # trigger 24e-9
        self.assertIsInstance(sequencer.instruction_list[12], SeqTrigger)
        # Wait 24e-9
        self.assertIsInstance(sequencer.instruction_list[13], SeqWaitImm)
        # add step to variable
        self.assertIsInstance(sequencer.instruction_list[14], SeqRegImmediateInst)
        # Jump to Branch
        self.assertIsInstance(sequencer.instruction_list[15], SeqJump)

        # End
        self.assertIsInstance(sequencer.instruction_list[16], SeqEnd)

        sequencer = self.job1.cell_seq_dict[self.job1.cells[1]]

        # unrolled loop 0
        # set variable to 0
        self.assertIsInstance(sequencer.instruction_list[0], SeqRegImmediateInst)
        # trigger 24e-9 unrolled loop
        self.assertIsInstance(sequencer.instruction_list[1], SeqTrigger)
        # Wait 24e-9
        self.assertIsInstance(sequencer.instruction_list[2], SeqWaitImm)

        # unrolled loop 1
        # set variable to 1
        self.assertIsInstance(sequencer.instruction_list[3], SeqRegImmediateInst)
        # trigger var1 = 1
        self.assertIsInstance(sequencer.instruction_list[4], SeqTrigger)
        # trigger 24e-9 unrolled loop
        self.assertIsInstance(sequencer.instruction_list[5], SeqTrigger)
        # Wait 24e-9
        self.assertIsInstance(sequencer.instruction_list[6], SeqWaitImm)

        # actual loop
        # end_val to register
        self.assertIsInstance(sequencer.instruction_list[7], SeqRegImmediateInst)
        # load new start value 4e-9
        self.assertIsInstance(sequencer.instruction_list[8], SeqRegImmediateInst)
        # Branch loop value check
        self.assertIsInstance(sequencer.instruction_list[9], SeqBranch)
        # trigger var
        self.assertIsInstance(sequencer.instruction_list[10], SeqTrigger)
        # Wait var
        self.assertIsInstance(sequencer.instruction_list[11], SeqTriggerWaitRegister)
        # trigger 24e-9
        self.assertIsInstance(sequencer.instruction_list[12], SeqTrigger)
        # Wait 24e-9
        self.assertIsInstance(sequencer.instruction_list[13], SeqWaitImm)
        # add step to variable
        self.assertIsInstance(sequencer.instruction_list[14], SeqRegImmediateInst)
        # Jump to Branch
        self.assertIsInstance(sequencer.instruction_list[15], SeqJump)

        # End
        self.assertIsInstance(sequencer.instruction_list[16], SeqEnd)

    def test_unroll_var_start(self):
        with QiJob(skip_nco_sync=True) as var_start_test:
            q = QiCells(2)
            var1 = QiTimeVariable()
            var2 = QiTimeVariable(0.0)
            with ForRange(var1, var2, 24e-9, 4e-9):
                Play(q[0], QiPulse(length=var1))
                Play(q[0], QiPulse(length=24e-9))
                Play(q[1], QiPulse(length=var1))
                Play(q[1], QiPulse(length=24e-9))

        var_start_test._build_program()

        sequencer = var_start_test.cell_seq_dict[var_start_test.cells[0]]

        # set var2 to 0
        self.assertIsInstance(sequencer.instruction_list[0], SeqRegImmediateInst)

        #####
        # unrolled loop 0
        #####
        # set var1 = var2
        cmd = sequencer.instruction_list[1]
        self.assertIsInstance(cmd, SeqRegImmediateInst)

        if isinstance(cmd, SeqRegImmediateInst):
            self.assertEqual(cmd.dst_reg, sequencer.get_var_register(var1).adr)
            self.assertEqual(cmd.register, sequencer.get_var_register(var2).adr)
            self.assertEqual(cmd.immediate, 0)

        # if var1 == 0
        self.assertIsInstance(sequencer.instruction_list[2], SeqBranch)

        # trigger 24e-9 unrolled loop
        self.assertIsInstance(sequencer.instruction_list[3], SeqTrigger)

        # Wait 24e-9
        self.assertIsInstance(sequencer.instruction_list[4], SeqWaitImm)

        # set var1 += step
        self.assertIsInstance(sequencer.instruction_list[5], SeqRegImmediateInst)

        #####
        # unrolled loop 1
        #####

        # load "1" to register for next command
        self.assertIsInstance(sequencer.instruction_list[6], SeqRegImmediateInst)

        # if var1 == 1
        self.assertIsInstance(sequencer.instruction_list[7], SeqBranch)

        # trigger for 1 cycle
        self.assertIsInstance(sequencer.instruction_list[8], SeqTrigger)

        # trigger 24e-9
        self.assertIsInstance(sequencer.instruction_list[9], SeqTrigger)
        # Wait 20e-9
        self.assertIsInstance(sequencer.instruction_list[10], SeqWaitImm)
        # set var1 += step
        self.assertIsInstance(sequencer.instruction_list[11], SeqRegImmediateInst)

        #####
        # actual loop
        #####
        # load "1" to register for next command
        self.assertIsInstance(sequencer.instruction_list[12], SeqRegImmediateInst)

        # if var1 > 1
        self.assertIsInstance(sequencer.instruction_list[13], SeqBranch)

        # end_val to register
        self.assertIsInstance(sequencer.instruction_list[14], SeqRegImmediateInst)
        # var1 = var2
        cmd = sequencer.instruction_list[15]
        self.assertIsInstance(cmd, SeqRegImmediateInst)

        if isinstance(cmd, SeqRegImmediateInst):
            self.assertEqual(cmd.dst_reg, sequencer.get_var_register(var1).adr)
            self.assertEqual(cmd.register, sequencer.get_var_register(var1).adr)
            self.assertEqual(cmd.immediate, 0)

        # Branch loop value check
        self.assertIsInstance(sequencer.instruction_list[16], SeqBranch)
        # trigger var
        self.assertIsInstance(sequencer.instruction_list[17], SeqTrigger)
        # Wait var
        self.assertIsInstance(sequencer.instruction_list[18], SeqTriggerWaitRegister)
        # trigger 24e-9
        self.assertIsInstance(sequencer.instruction_list[19], SeqTrigger)
        # Wait 24e-9
        self.assertIsInstance(sequencer.instruction_list[20], SeqWaitImm)
        # Explicit sync because of variable start value.
        self.assertIsInstance(sequencer.instruction_list[21], SeqCellSync)
        # add step to variable
        self.assertIsInstance(sequencer.instruction_list[22], SeqRegImmediateInst)
        # Jump to Branch
        self.assertIsInstance(sequencer.instruction_list[23], SeqJump)
        # End
        self.assertIsInstance(sequencer.instruction_list[24], SeqEnd)

        sequencer = var_start_test.cell_seq_dict[var_start_test.cells[1]]

        # set var2 to 0
        self.assertIsInstance(sequencer.instruction_list[0], SeqRegImmediateInst)

        #####
        # unrolled loop 0
        #####
        # set var1 = var2
        cmd = sequencer.instruction_list[1]
        self.assertIsInstance(cmd, SeqRegImmediateInst)

        if isinstance(cmd, SeqRegImmediateInst):
            self.assertEqual(cmd.dst_reg, sequencer.get_var_register(var1).adr)
            self.assertEqual(cmd.register, sequencer.get_var_register(var2).adr)
            self.assertEqual(cmd.immediate, 0)

        # if var1 == 0
        self.assertIsInstance(sequencer.instruction_list[2], SeqBranch)

        # trigger 24e-9 unrolled loop
        self.assertIsInstance(sequencer.instruction_list[3], SeqTrigger)

        # Wait 24e-9
        self.assertIsInstance(sequencer.instruction_list[4], SeqWaitImm)

        # set var1 += step
        self.assertIsInstance(sequencer.instruction_list[5], SeqRegImmediateInst)

        #####
        # unrolled loop 1
        #####

        # load "1" to register for next command
        self.assertIsInstance(sequencer.instruction_list[6], SeqRegImmediateInst)

        # if var1 == 1
        self.assertIsInstance(sequencer.instruction_list[7], SeqBranch)

        # trigger for 1 cycle
        self.assertIsInstance(sequencer.instruction_list[8], SeqTrigger)

        # trigger 24e-9
        self.assertIsInstance(sequencer.instruction_list[9], SeqTrigger)
        # Wait 20e-9
        self.assertIsInstance(sequencer.instruction_list[10], SeqWaitImm)
        # set var1 += step
        self.assertIsInstance(sequencer.instruction_list[11], SeqRegImmediateInst)

        #####
        # actual loop
        #####
        # load "1" to register for next command
        self.assertIsInstance(sequencer.instruction_list[12], SeqRegImmediateInst)

        # if var1 > 1
        self.assertIsInstance(sequencer.instruction_list[13], SeqBranch)

        # end_val to register
        self.assertIsInstance(sequencer.instruction_list[14], SeqRegImmediateInst)
        # var1 = var2
        cmd = sequencer.instruction_list[15]
        self.assertIsInstance(cmd, SeqRegImmediateInst)

        if isinstance(cmd, SeqRegImmediateInst):
            self.assertEqual(cmd.dst_reg, sequencer.get_var_register(var1).adr)
            self.assertEqual(cmd.register, sequencer.get_var_register(var1).adr)
            self.assertEqual(cmd.immediate, 0)

        # Branch loop value check
        self.assertIsInstance(sequencer.instruction_list[16], SeqBranch)
        # trigger var
        self.assertIsInstance(sequencer.instruction_list[17], SeqTrigger)
        # Wait var
        self.assertIsInstance(sequencer.instruction_list[18], SeqTriggerWaitRegister)
        # trigger 24e-9
        self.assertIsInstance(sequencer.instruction_list[19], SeqTrigger)
        # Wait 24e-9
        self.assertIsInstance(sequencer.instruction_list[20], SeqWaitImm)
        # Explicit sync because of variable start value.
        self.assertIsInstance(sequencer.instruction_list[21], SeqCellSync)
        # add step to variable
        self.assertIsInstance(sequencer.instruction_list[22], SeqRegImmediateInst)
        # Jump to Branch
        self.assertIsInstance(sequencer.instruction_list[23], SeqJump)
        # End
        self.assertIsInstance(sequencer.instruction_list[24], SeqEnd)

    def test_unroll_recording(self):
        self.job2._build_program()

        sequencer = self.job2.cell_seq_dict[self.job2.cells[0]]

        # unroll loop 0
        # set variable to 0
        self.assertIsInstance(sequencer.instruction_list[0], SeqRegImmediateInst)
        # trigger 24e-9 unrolled loop
        self.assertIsInstance(sequencer.instruction_list[1], SeqTrigger)
        # Wait 24e-9
        self.assertIsInstance(sequencer.instruction_list[2], SeqWaitImm)
        # trigger recording
        self.assertIsInstance(sequencer.instruction_list[3], SeqTrigger)

        # wait recording length
        tmp_cmd = sequencer.instruction_list[4]
        self.assertIsInstance(tmp_cmd, SeqWaitImm)

        if isinstance(tmp_cmd, SeqWaitImm):
            self.assertEqual(
                tmp_cmd.immediate, util.conv_time_to_cycles(self.rec_length)
            )

        # unroll loop 1
        # set variable to 1
        self.assertIsInstance(sequencer.instruction_list[5], SeqRegImmediateInst)
        # trigger 24e-9 unrolled loop
        self.assertIsInstance(sequencer.instruction_list[6], SeqTrigger)
        # Wait 24e-9
        self.assertIsInstance(sequencer.instruction_list[7], SeqWaitImm)
        # trigger readout var = 1
        self.assertIsInstance(sequencer.instruction_list[8], SeqTrigger)
        # end trigger
        self.assertIsInstance(sequencer.instruction_list[9], SeqTrigger)

        # actual loop
        # end_val to register
        self.assertIsInstance(sequencer.instruction_list[10], SeqRegImmediateInst)

        # load new start value 8e-9
        tmp_cmd = sequencer.instruction_list[11]
        self.assertIsInstance(tmp_cmd, SeqRegImmediateInst)
        if isinstance(tmp_cmd, SeqRegImmediateInst):
            self.assertEqual(tmp_cmd.immediate, util.conv_time_to_cycles(8e-9))

        # Branch loop value check
        self.assertIsInstance(sequencer.instruction_list[12], SeqBranch)
        # trigger 24e-9
        self.assertIsInstance(sequencer.instruction_list[13], SeqTrigger)
        # Wait trigger
        self.assertIsInstance(sequencer.instruction_list[14], SeqWaitImm)
        # trigger readout var
        self.assertIsInstance(sequencer.instruction_list[15], SeqTrigger)
        # Wait var
        self.assertIsInstance(sequencer.instruction_list[16], SeqTriggerWaitRegister)
        # end variable trigger
        self.assertIsInstance(sequencer.instruction_list[17], SeqTrigger)
        # add step to variable
        self.assertIsInstance(sequencer.instruction_list[18], SeqRegImmediateInst)
        # Jump to Branch
        self.assertIsInstance(sequencer.instruction_list[19], SeqJump)

        # End
        self.assertIsInstance(sequencer.instruction_list[20], SeqEnd)

    def test_unrolling_decrement(self):
        with QiJob(skip_nco_sync=True) as dec_job:
            q = QiCells(1)
            var2 = QiTimeVariable()
            with ForRange(var2, 24e-9, 0, -4e-9):
                Play(q[0], QiPulse(length=24e-9))
                PlayReadout(q[0], QiPulse(length=var2))
                Recording(q[0], 200e-9, save_to="result")

        dec_job._build_program()

        sequencer = dec_job.cell_seq_dict[dec_job.cells[0]]

        # actual loop
        # end_val==1 to register
        self.assertIsInstance(sequencer.instruction_list[0], SeqRegImmediateInst)
        # start value 24e-9
        self.assertIsInstance(sequencer.instruction_list[1], SeqRegImmediateInst)
        # Branch loop value check
        self.assertIsInstance(sequencer.instruction_list[2], SeqBranch)
        # trigger 24e-9
        self.assertIsInstance(sequencer.instruction_list[3], SeqTrigger)
        # Wait trigger
        self.assertIsInstance(sequencer.instruction_list[4], SeqWaitImm)
        # trigger readout var
        self.assertIsInstance(sequencer.instruction_list[5], SeqTrigger)
        # Wait var
        self.assertIsInstance(sequencer.instruction_list[6], SeqTriggerWaitRegister)
        # end variable trigger
        self.assertIsInstance(sequencer.instruction_list[7], SeqTrigger)
        # add step to variable
        self.assertIsInstance(sequencer.instruction_list[8], SeqRegImmediateInst)
        self.assertIsInstance(sequencer.instruction_list[9], SeqJump)  # Jump to Branch

        # unroll loop 1
        # trigger 24e-9 unrolled loop
        self.assertIsInstance(sequencer.instruction_list[10], SeqTrigger)
        # Wait 24e-9
        self.assertIsInstance(sequencer.instruction_list[11], SeqWaitImm)
        # trigger readout var = 1
        self.assertIsInstance(sequencer.instruction_list[12], SeqTrigger)
        # end variable trigger
        self.assertIsInstance(sequencer.instruction_list[13], SeqTrigger)

        # End
        self.assertIsInstance(sequencer.instruction_list[14], SeqEnd)

    def test_unrolling_decrement_var_end(self):
        with QiJob(skip_nco_sync=True) as dec_job:
            q = QiCells(1)
            var = QiTimeVariable(0.0)
            var2 = QiTimeVariable()
            with ForRange(var2, 24e-9, var, -4e-9):
                Play(q[0], QiPulse(length=24e-9))
                PlayReadout(q[0], QiPulse(length=var2))

        dec_job._build_program()

        sequencer = dec_job.cell_seq_dict[dec_job.cells[0]]

        # var = 0
        self.assertIsInstance(sequencer.instruction_list[0], SeqRegImmediateInst)

        # var2 = var
        self.assertIsInstance(sequencer.instruction_list[1], SeqRegImmediateInst)

        # load "1" to register for next command
        self.assertIsInstance(sequencer.instruction_list[2], SeqRegImmediateInst)

        # if var2 > 1
        self.assertIsInstance(sequencer.instruction_list[3], SeqBranch)

        # actual loop
        # start value var2 = 24e-9
        self.assertIsInstance(sequencer.instruction_list[4], SeqRegImmediateInst)
        # Branch loop value check
        self.assertIsInstance(sequencer.instruction_list[5], SeqBranch)
        # trigger 24e-9
        self.assertIsInstance(sequencer.instruction_list[6], SeqTrigger)
        # Wait trigger
        self.assertIsInstance(sequencer.instruction_list[7], SeqWaitImm)
        # trigger readout var
        self.assertIsInstance(sequencer.instruction_list[8], SeqTrigger)
        # Wait var
        self.assertIsInstance(sequencer.instruction_list[9], SeqTriggerWaitRegister)
        # end variable trigger
        self.assertIsInstance(sequencer.instruction_list[10], SeqTrigger)
        # add step to variable
        self.assertIsInstance(sequencer.instruction_list[11], SeqRegImmediateInst)
        # set "1" in register for if command
        self.assertIsInstance(sequencer.instruction_list[12], SeqRegImmediateInst)
        # if var2 == 1 jump over jump command
        self.assertIsInstance(sequencer.instruction_list[13], SeqBranch)
        # Jump to Branch
        self.assertIsInstance(sequencer.instruction_list[14], SeqJump)

        # unroll loop 1
        # set "1" in register for if command
        self.assertIsInstance(sequencer.instruction_list[15], SeqRegImmediateInst)
        # if var2 == 1
        self.assertIsInstance(sequencer.instruction_list[16], SeqBranch)
        # if var2 > var
        self.assertIsInstance(sequencer.instruction_list[17], SeqBranch)

        # trigger 24e-9
        self.assertIsInstance(sequencer.instruction_list[18], SeqTrigger)
        # Wait 20e-9
        self.assertIsInstance(sequencer.instruction_list[19], SeqWaitImm)
        # trigger readout var = 1
        self.assertIsInstance(sequencer.instruction_list[20], SeqTrigger)
        # end variable trigger
        self.assertIsInstance(sequencer.instruction_list[21], SeqTrigger)

        self.assertIsInstance(sequencer.instruction_list[22], SeqEnd)  # End

    def test_unrolling_decrement_var_end_not_valid(self):
        with QiJob(skip_nco_sync=True) as dec_job:
            q = QiCells(1)
            var = QiTimeVariable(0.0)
            var2 = QiTimeVariable()
            with If(var2 == 0):
                Assign(var, 4e-9)
            with ForRange(var2, 24e-9, var, -4e-9):
                Play(q[0], QiPulse(length=24e-9))
                PlayReadout(q[0], QiPulse(length=var2))

        dec_job._build_program()

        sequencer = dec_job.cell_seq_dict[dec_job.cells[0]]

        # var = 0
        self.assertIsInstance(sequencer.instruction_list[0], SeqRegImmediateInst)
        # compare var and reg0
        self.assertIsInstance(sequencer.instruction_list[1], SeqBranch)
        # var = 1
        self.assertIsInstance(sequencer.instruction_list[2], SeqRegImmediateInst)

        # var2 = var
        self.assertIsInstance(sequencer.instruction_list[3], SeqRegImmediateInst)

        # load "1" to register for next command
        self.assertIsInstance(sequencer.instruction_list[4], SeqRegImmediateInst)

        # if var2 > 1
        self.assertIsInstance(sequencer.instruction_list[5], SeqBranch)

        # actual loop
        # start value var2 = 24e-9
        self.assertIsInstance(sequencer.instruction_list[6], SeqRegImmediateInst)
        # Branch loop value check
        self.assertIsInstance(sequencer.instruction_list[7], SeqBranch)
        # trigger 24e-9
        self.assertIsInstance(sequencer.instruction_list[8], SeqTrigger)
        # Wait trigger
        self.assertIsInstance(sequencer.instruction_list[9], SeqWaitImm)
        # trigger readout var
        self.assertIsInstance(sequencer.instruction_list[10], SeqTrigger)
        # Wait var
        self.assertIsInstance(sequencer.instruction_list[11], SeqTriggerWaitRegister)
        # end variable trigger
        self.assertIsInstance(sequencer.instruction_list[12], SeqTrigger)
        # add step to variable
        self.assertIsInstance(sequencer.instruction_list[13], SeqRegImmediateInst)
        # set "1" in register for if command
        self.assertIsInstance(sequencer.instruction_list[14], SeqRegImmediateInst)
        # if var2 == 1 jump over jump command
        self.assertIsInstance(sequencer.instruction_list[15], SeqBranch)
        # Jump to Branch
        self.assertIsInstance(sequencer.instruction_list[16], SeqJump)

        # unroll loop 1
        # set "1" in register for if command
        self.assertIsInstance(sequencer.instruction_list[17], SeqRegImmediateInst)
        # if var2 == 1
        self.assertIsInstance(sequencer.instruction_list[18], SeqBranch)
        # if var2 > var
        self.assertIsInstance(sequencer.instruction_list[19], SeqBranch)

        # trigger 24e-9
        self.assertIsInstance(sequencer.instruction_list[20], SeqTrigger)
        # Wait 20e-9
        self.assertIsInstance(sequencer.instruction_list[21], SeqWaitImm)
        # trigger readout var = 1
        self.assertIsInstance(sequencer.instruction_list[22], SeqTrigger)
        # end variable trigger
        self.assertIsInstance(sequencer.instruction_list[23], SeqTrigger)

        self.assertIsInstance(sequencer.instruction_list[24], SeqEnd)  # End

    def test_unroll_nested_var_end(self):
        with QiJob(skip_nco_sync=True) as test_fr:
            q = QiCells(1)
            var1 = QiTimeVariable()
            var2 = QiTimeVariable()

            with ForRange(var2, 0, 24e-9, 4e-9):
                with ForRange(var1, 0, var2, 4e-9):
                    Play(q[0], QiPulse(var1))
                    Wait(q[0], 4e-9)

        test_fr._build_program()

        sequencer = test_fr.cell_seq_dict[test_fr.cells[0]]

        # unroll var2 == 0
        self.assertIsInstance(
            sequencer.instruction_list[0], SeqRegImmediateInst
        )  # var2 = 0 ForRange should be skipped

        # unroll var2 == 1
        self.assertIsInstance(
            sequencer.instruction_list[1], SeqRegImmediateInst
        )  # var2 = 1

        # unroll var1==0
        self.assertIsInstance(
            sequencer.instruction_list[2], SeqRegImmediateInst
        )  # var1 = 0
        self.assertIsInstance(sequencer.instruction_list[3], SeqWaitImm)

        # outer loop
        self.assertIsInstance(
            sequencer.instruction_list[4], SeqRegImmediateInst
        )  # var2 = 8e-9
        self.assertIsInstance(
            sequencer.instruction_list[5], SeqRegImmediateInst
        )  # end outer loop = 24e-9
        self.assertIsInstance(sequencer.instruction_list[6], SeqBranch)

        # unroll var1==0
        self.assertIsInstance(
            sequencer.instruction_list[7], SeqRegImmediateInst
        )  # var1 = 0
        self.assertIsInstance(sequencer.instruction_list[8], SeqWaitImm)

        # unroll var1==1
        self.assertIsInstance(
            sequencer.instruction_list[9], SeqRegImmediateInst
        )  # var1 = 4e-9
        self.assertIsInstance(sequencer.instruction_list[10], SeqTrigger)  # Trigger
        self.assertIsInstance(sequencer.instruction_list[11], SeqTrigger)  # Trigger end
        self.assertIsInstance(sequencer.instruction_list[12], SeqWaitImm)

        # inner loop
        self.assertIsInstance(
            sequencer.instruction_list[13], SeqRegImmediateInst
        )  # var1 = 8e-9
        self.assertIsInstance(sequencer.instruction_list[14], SeqBranch)

        self.assertIsInstance(sequencer.instruction_list[15], SeqTrigger)  # Trigger
        self.assertIsInstance(
            sequencer.instruction_list[16], SeqTriggerWaitRegister
        )  # Trigger wait
        self.assertIsInstance(sequencer.instruction_list[17], SeqTrigger)  # Trigger end
        self.assertIsInstance(sequencer.instruction_list[18], SeqWaitImm)
        self.assertIsInstance(
            sequencer.instruction_list[19], SeqRegImmediateInst
        )  # add to var1
        self.assertIsInstance(sequencer.instruction_list[20], SeqJump)

        self.assertIsInstance(
            sequencer.instruction_list[21], SeqRegImmediateInst
        )  # add to var2
        self.assertIsInstance(sequencer.instruction_list[22], SeqJump)

        self.assertIsInstance(sequencer.instruction_list[23], SeqEnd)

    def test_skip_after_unroll_0(self):
        with QiJob(skip_nco_sync=True) as test:
            q = QiCells(1)
            var2 = QiTimeVariable()
            with ForRange(var2, 0, 4e-9, 4e-9):
                Play(q[0], QiPulse(length=24e-9))
                PlayReadout(q[0], QiPulse(length=var2))
                Recording(q[0], 200e-9, save_to="result")

        test._build_program()

        sequencer = test.cell_seq_dict[test.cells[0]]

        # unroll loop 0
        self.assertIsInstance(
            sequencer.instruction_list[0], SeqRegImmediateInst
        )  # set variable to 0
        self.assertIsInstance(
            sequencer.instruction_list[1], SeqTrigger
        )  # trigger 24e-9 unrolled loop
        self.assertIsInstance(sequencer.instruction_list[2], SeqWaitImm)  # Wait 24e-9
        self.assertIsInstance(
            sequencer.instruction_list[3], SeqTrigger
        )  # trigger recording
        self.assertIsInstance(
            sequencer.instruction_list[4], SeqWaitImm
        )  # Wait recording

        self.assertIsInstance(sequencer.instruction_list[5], SeqEnd)  # End

    def test_skip_after_unroll_1(self):
        with QiJob(skip_nco_sync=True) as test:
            q = QiCells(1)
            var2 = QiTimeVariable()
            with ForRange(var2, 0, 8e-9, 4e-9):
                Play(q[0], QiPulse(length=24e-9))
                PlayReadout(q[0], QiPulse(length=var2))
                Recording(q[0], 200e-9, save_to="result")

        test._build_program()

        sequencer = test.cell_seq_dict[test.cells[0]]

        # unroll loop 0
        self.assertIsInstance(
            sequencer.instruction_list[0], SeqRegImmediateInst
        )  # set variable to 0
        self.assertIsInstance(
            sequencer.instruction_list[1], SeqTrigger
        )  # trigger 24e-9 unrolled loop
        self.assertIsInstance(sequencer.instruction_list[2], SeqWaitImm)  # Wait 24e-9
        self.assertIsInstance(
            sequencer.instruction_list[3], SeqTrigger
        )  # trigger recording
        self.assertIsInstance(
            sequencer.instruction_list[4], SeqWaitImm
        )  # Wait recording

        # unroll loop 1
        self.assertIsInstance(
            sequencer.instruction_list[5], SeqRegImmediateInst
        )  # set variable to 1
        self.assertIsInstance(
            sequencer.instruction_list[6], SeqTrigger
        )  # trigger 24e-9 unrolled loop
        self.assertIsInstance(sequencer.instruction_list[7], SeqWaitImm)  # Wait 24e-9
        self.assertIsInstance(
            sequencer.instruction_list[8], SeqTrigger
        )  # trigger readout var = 1
        self.assertIsInstance(sequencer.instruction_list[9], SeqTrigger)  # end trigger

        self.assertIsInstance(sequencer.instruction_list[10], SeqEnd)  # End


class NestedForRangeTest(unittest.TestCase):
    def test_nested_start_var(self):
        with QiJob(skip_nco_sync=True) as test_fr:
            q = QiCells(1)
            count = QiVariable(int)
            i = QiVariable(int)
            with ForRange(count, 10, 0, -1):
                with ForRange(i, count, 0, -1):
                    Play(q[0], QiPulse(length=24e-9))
                Wait(q[0], 24e-9)

        test_fr._build_program()

        sequencer = test_fr.cell_seq_dict[test_fr.cells[0]]

        self.assertIsInstance(sequencer.instruction_list[0], SeqRegImmediateInst)
        self.assertIsInstance(sequencer.instruction_list[1], SeqBranch)

        cmd = sequencer.instruction_list[2]
        self.assertIsInstance(cmd, SeqRegImmediateInst)

        if isinstance(cmd, SeqRegImmediateInst):
            self.assertEqual(cmd.dst_reg, sequencer.get_var_register(i).adr)
            self.assertEqual(cmd.register, sequencer.get_var_register(count).adr)
            self.assertEqual(cmd.immediate, 0)


class QiWaitZeroLengthTest(unittest.TestCase):
    def test_exact_zero_wait(self):

        with QiJob() as job:
            q = QiCells(1)
            Wait(q[0], 0e-9)

        job._build_program()

        sequencer = job.cell_seq_dict[job.cells[0]]

        self.assertEqual(len(sequencer.instruction_list), 2)
        self.assertIsInstance(sequencer.instruction_list[0], SeqTrigger)
        self.assertIsInstance(sequencer.instruction_list[1], SeqEnd)

    def test_almost_zero_wait(self):
        """Non-zero values due to floating point arithmetic errors should also be erased."""

        with QiJob() as job:
            q = QiCells(1)
            Wait(q[0], 0.09e-9)

        job._build_program()

        sequencer = job.cell_seq_dict[job.cells[0]]

        self.assertEqual(len(sequencer.instruction_list), 2)
        self.assertIsInstance(sequencer.instruction_list[0], SeqTrigger)
        self.assertIsInstance(sequencer.instruction_list[1], SeqEnd)

    def test_non_zero_wait(self):

        with QiJob() as job:
            q = QiCells(1)
            Wait(q[0], 5e-9)

        job._build_program()

        sequencer = job.cell_seq_dict[job.cells[0]]

        self.assertEqual(len(sequencer.instruction_list), 3)
        self.assertIsInstance(sequencer.instruction_list[0], SeqTrigger)
        self.assertIsInstance(sequencer.instruction_list[1], SeqWaitImm)
        self.assertEqual(sequencer.instruction_list[1].immediate, 2)
        self.assertIsInstance(sequencer.instruction_list[2], SeqEnd)


class ExcludeVarVisitorTest(unittest.TestCase):
    def setUp(self) -> None:
        job = QiJob()
        _set_job_reference(job)

        self.cell = QiCell(0)

        self.var1 = QiTimeVariable()

        with ForRange(self.var1, 0, 40e-9, 4e-9) as self.for_range:
            Play(self.cell, QiPulse(length=self.var1))

            with If(self.var1 == 0):

                Play(self.cell, QiPulse(length=self.var1))

                # readout and recording are not excluded
                PlayReadout(self.cell, QiPulse(length=50e-9))
                Recording(self.cell, "rec")

                with Parallel():
                    PlayReadout(self.cell, QiPulse(length=52e-9))
                with Parallel():
                    Play(self.cell, QiPulse(length=52e-9))

                Wait(self.cell, self.var1)
            with Else():
                Play(self.cell, QiPulse(length=50e-9))

                # readout and recording should be excluded
                PlayReadout(self.cell, QiPulse(length=self.var1))
                Recording(self.cell, "rec")

                Wait(self.cell, self.var1)

        cell_to_cm = qv.QiCMContainedCellVisitor()

        for cmd in self.for_range.body:
            cmd.accept(cell_to_cm)

    def tearDown(self) -> None:
        _delete_job_reference()
        return super().tearDown()

    def test_for_range_TimingVariable(self):
        exclude_var = QiCmdExcludeVar([self.var1])

        for cmd in self.for_range.body:
            cmd.accept(exclude_var)

        self.assertEqual(len(exclude_var.commands), 1)

        test_if = exclude_var.commands[0]

        self.assertIsInstance(test_if, If)
        self.assertIn(self.cell, test_if._relevant_cells)

        if isinstance(test_if, If):
            self.assertEqual(
                len(test_if.body), 2
            )  # should only contain readout command and Parallel

        test_else = test_if._else_body

        self.assertEqual(len(test_else), 2)  # play + recording


class BuildContextManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        job = QiJob()
        _set_job_reference(job)
        self.cell = QiCell(0)
        self.sequencer = Sequencer()
        self.var1 = QiVariable(int)
        self.sequencer.add_variable(self.var1)

        self.for_cmd = ForRange(self.var1, 1, 20, 5)
        self.for_cmd.body.append(cQiWait(self.cell, 5e-9))
        self.for_cmd._relevant_cells.add(self.cell)

        self.if_cmd = If(self.var1 == 3)
        self.if_cmd.body.append(cQiWait(self.cell, 5e-9))
        self.if_cmd._relevant_cells.add(self.cell)

    def tearDown(self) -> None:
        _delete_job_reference()
        return super().tearDown()

    def test_for_range_to_seq(self):
        prog_builder = ProgramBuilderVisitor({self.cell: self.sequencer}, [0])

        self.for_cmd.accept(prog_builder)

        # end value to register
        self.assertIsInstance(self.sequencer.instruction_list[0], SeqRegImmediateInst)

        # load start value '1' to register
        tmp_cmd = self.sequencer.instruction_list[1]
        self.assertIsInstance(tmp_cmd, SeqRegImmediateInst)

        if isinstance(tmp_cmd, SeqRegImmediateInst):
            # write 0 to var1
            self.assertEqual(tmp_cmd.immediate, 1)

        tmp_cmd = self.sequencer.instruction_list[2]
        self.assertIsInstance(tmp_cmd, SeqBranch)

        if isinstance(tmp_cmd, SeqBranch):
            # loop contains wait, addition and jump-back, to skip over loop-body add 4 to current program counter
            self.assertEqual(tmp_cmd.immediate, 4)

        # wait
        self.assertIsInstance(self.sequencer.instruction_list[3], SeqWaitImm)

        # add 5
        tmp_cmd = self.sequencer.instruction_list[4]
        self.assertIsInstance(tmp_cmd, SeqRegImmediateInst)

        if isinstance(tmp_cmd, SeqRegImmediateInst):
            # +1 to variable
            self.assertEqual(tmp_cmd.immediate, 5)

        tmp_cmd = self.sequencer.instruction_list[5]
        self.assertIsInstance(tmp_cmd, SeqJump)

        if isinstance(tmp_cmd, SeqJump):
            # program counter -3 to get back to branch
            self.assertEqual(tmp_cmd.jump_val, -3)

    def test_if_to_seq(self):
        prog_builder = ProgramBuilderVisitor({self.cell: self.sequencer}, [1])

        self.if_cmd.accept(prog_builder)

        # value 3 to register
        self.assertIsInstance(self.sequencer.instruction_list[0], SeqRegImmediateInst)

        tmp_cmd = self.sequencer.instruction_list[1]
        self.assertIsInstance(tmp_cmd, SeqBranch)

        if isinstance(tmp_cmd, SeqBranch):
            # if contains wait; to skip over if-body add 2 to current program counter
            self.assertEqual(tmp_cmd.immediate, 2)

            # condition of if needs to be inverted --> jump over if-body when if-condition is NOT true
            self.assertEqual(tmp_cmd.funct3, SeqBranchFunct3.BNE)

        # wait
        self.assertIsInstance(self.sequencer.instruction_list[2], SeqWaitImm)

    def test_if_else_to_seq(self):
        prog_builder = ProgramBuilderVisitor({self.cell: self.sequencer}, [1])

        self.if_cmd._else_body.append(cQiWait(self.cell, 5e-9))

        self.if_cmd.accept(prog_builder)

        # value 3 to register
        self.assertIsInstance(self.sequencer.instruction_list[0], SeqRegImmediateInst)

        tmp_cmd = self.sequencer.instruction_list[1]
        self.assertIsInstance(tmp_cmd, SeqBranch)

        if isinstance(tmp_cmd, SeqBranch):
            # if contains wait and jump; to skip over if-body add 3 to current program counter
            self.assertEqual(tmp_cmd.immediate, 3)

        # wait if-body
        self.assertIsInstance(self.sequencer.instruction_list[2], SeqWaitImm)

        tmp_cmd = self.sequencer.instruction_list[3]
        self.assertIsInstance(tmp_cmd, SeqJump)

        if isinstance(tmp_cmd, SeqJump):
            # at then end of if-body jump over else-body
            self.assertEqual(tmp_cmd.jump_val, 2)

        # wait else-body
        self.assertIsInstance(self.sequencer.instruction_list[4], SeqWaitImm)


class QiAssignToSeq(unittest.TestCase):
    # test if length variables in Assign are translated to cycles
    def test_assign_length_variables(self):
        with QiJob(skip_nco_sync=True) as test_assign:
            q = QiCells(1)
            x = QiTimeVariable()
            Assign(x, 48e-9)
            Play(q[0], QiPulse(x))

        test_assign._build_program()
        sequencer = test_assign.cell_seq_dict[test_assign.cells[0]]

        tmp_cmd = sequencer.instruction_list[0]
        self.assertIsInstance(tmp_cmd, SeqRegImmediateInst)

        if isinstance(tmp_cmd, SeqRegImmediateInst):
            self.assertEqual(tmp_cmd.immediate, 12)

    def test_assign_multiple_cells(self):
        with QiJob(skip_nco_sync=True) as test_assign:
            q = QiCells(2)
            x = QiTimeVariable(48e-9)
            Play(q[0], QiPulse(x))
            Play(q[1], QiPulse(x))

        test_assign._build_program()

        sequencer = test_assign.cell_seq_dict[test_assign.cells[0]]
        reg_x = sequencer.get_var_register(x)

        self.assertTrue(reg_x.valid)
        self.assertEqual(reg_x.value, util.conv_time_to_cycles(48e-9))

        sequencer = test_assign.cell_seq_dict[test_assign.cells[1]]
        reg_x = sequencer.get_var_register(x)

        self.assertTrue(reg_x.valid)
        self.assertEqual(reg_x.value, util.conv_time_to_cycles(48e-9))

    def test_assign_in_if(self):
        with QiJob(skip_nco_sync=True) as test_assign:
            q = QiCells(1)
            x = QiTimeVariable()
            with If(x == 0):
                Assign(x, 48e-9)  # should invalidate x
            Play(q[0], QiPulse(x))

        test_assign._build_program()

        sequencer = test_assign.cell_seq_dict[test_assign.cells[0]]

        self.assertIsInstance(
            sequencer.instruction_list[0], SeqBranch
        )  # compare x to reg 0
        self.assertIsInstance(
            sequencer.instruction_list[1], SeqRegImmediateInst
        )  # set x to 48e-9
        self.assertIsInstance(
            sequencer.instruction_list[2], SeqTrigger
        )  # Trigger Play pulse

    def test_assign_in_if_var_invalidation(self):
        with QiJob(skip_nco_sync=True) as test_assign:
            q = QiCells(1)
            x = QiTimeVariable()
            with If(x == 0):
                Assign(x, 48e-9)  # should invalidate x
            Play(q[0], QiPulse(x))

        test_assign._build_program()

        sequencer = test_assign.cell_seq_dict[test_assign.cells[0]]

        reg_x = sequencer.get_var_register(x)

        self.assertFalse(reg_x.valid)

    def test_assign_after_if(self):
        with QiJob(skip_nco_sync=True) as test_assign:
            q = QiCells(1)
            x = QiTimeVariable()
            with If(x == 0):
                Assign(x, 48e-9)  # should invalidate x
            Assign(x, 48e-9)  # should validate it again
            Play(q[0], QiPulse(x))

        test_assign._build_program()

        sequencer = test_assign.cell_seq_dict[test_assign.cells[0]]

        reg_x = sequencer.get_var_register(x)

        self.assertTrue(reg_x.valid)

    def test_assign_after_if_not_valid(self):
        with QiJob(skip_nco_sync=True) as test_assign:
            q = QiCells(1)
            x = QiTimeVariable()
            with If(x == 0):
                Assign(x, 48e-9)  # should invalidate x
            Assign(x, x + 48e-9)  # should stay invalid, since x is invalid
            Play(q[0], QiPulse(x))

        test_assign._build_program()

        sequencer = test_assign.cell_seq_dict[test_assign.cells[0]]

        reg_x = sequencer.get_var_register(x)

        self.assertFalse(reg_x.valid)

    def test_assign_after_if_valid(self):
        with QiJob(skip_nco_sync=True) as test_assign:
            q = QiCells(1)
            x = QiTimeVariable(0.0)
            y = QiTimeVariable(0.0)
            with If(x == 0):
                Assign(x, 48e-9)  # should invalidate x
            Assign(x, y + 48e-9)  # x should be valid again, since y is valid
            Play(q[0], QiPulse(x))

        test_assign._build_program()

        sequencer = test_assign.cell_seq_dict[test_assign.cells[0]]

        reg_x = sequencer.get_var_register(x)

        self.assertTrue(reg_x.valid)

    def test_assign_in_for_range(self):
        with QiJob(skip_nco_sync=True) as job:
            q = QiCells(1)
            length = QiTimeVariable()
            length_half = QiTimeVariable()
            with ForRange(length, 24e-9, 100e-9, 24e-9):
                Assign(length_half, length >> 1)
                Wait(q[0], length_half)

        job._build_program()
        sequencer = job.cell_seq_dict[job.cells[0]]

        self.assertIsInstance(
            sequencer.instruction_list[0], SeqRegImmediateInst
        )  # start val
        self.assertIsInstance(
            sequencer.instruction_list[1], SeqRegImmediateInst
        )  # end val
        self.assertIsInstance(sequencer.instruction_list[2], SeqBranch)  # branch

        tmp_cmd = sequencer.instruction_list[3]
        self.assertIsInstance(
            tmp_cmd, SeqRegImmediateInst
        )  # rd reg half, rs length, immediate 1, op SRA

        if isinstance(tmp_cmd, SeqRegImmediateInst):
            self.assertEqual(tmp_cmd.funct3, SeqRegImmFunct3.SR)
            self.assertEqual(tmp_cmd.immediate, 1)

        self.assertIsInstance(
            sequencer.instruction_list[4], SeqRegImmediateInst
        )  # rd length half, rs reg, immediate 0, op ADD
        self.assertIsInstance(sequencer.instruction_list[5], SeqWaitRegister)


class QiSynchToSeq(unittest.TestCase):
    def setUp(self) -> None:
        self.time = 40e-9
        with QiJob(skip_nco_sync=True) as self.job1:
            q = QiCells(3)
            Wait(q[0], self.time)
            Sync(q[0], q[1], q[2])

        with QiJob(skip_nco_sync=True) as self.job2:
            q = QiCells(3)
            x = QiTimeVariable(20e-9)
            Wait(q[0], x)
            Sync(q[0], q[1], q[2])

        with QiJob(skip_nco_sync=True) as self.job3:
            q = QiCells(3)
            var1 = QiVariable(int)
            Wait(q[0], self.time)
            with ForRange(var1, 0, 5):
                Wait(q[0], self.time)
                Wait(q[1], self.time)

        with QiJob(skip_nco_sync=True) as self.job4:
            q = QiCells(3)
            var1 = QiVariable(int)
            Wait(q[0], self.time)
            with If(var1 == 2):
                Wait(q[0], self.time)
                Wait(q[1], self.time)

    def test_synch_OK(self):
        self.job1._build_program()

        for cell in self.job1.cells:
            sequencer = self.job1.cell_seq_dict[cell]
            tmp_cmd = sequencer.instruction_list[0]
            self.assertIsInstance(tmp_cmd, SeqWaitImm)
            self.assertEqual(
                len(sequencer.instruction_list), 2
            )  # wait and end of program

            if isinstance(tmp_cmd, SeqWaitImm):
                self.assertEqual(tmp_cmd.immediate, util.conv_time_to_cycles(self.time))

    def test_synch_variable(self):
        self.job2._build_program()
        sequencer = self.job2.cell_seq_dict[self.job2.cells[1]]

        tmp_cmd = sequencer.instruction_list[0]
        self.assertIsInstance(tmp_cmd, SeqWaitImm)
        self.assertEqual(len(sequencer.instruction_list), 2)  # wait and end of program

        if isinstance(tmp_cmd, SeqWaitImm):
            self.assertEqual(tmp_cmd.immediate, 6)  # Assign 1 cycle + wait 5 cycle

        sequencer = self.job2.cell_seq_dict[self.job2.cells[2]]

        tmp_cmd = sequencer.instruction_list[0]
        self.assertIsInstance(tmp_cmd, SeqWaitImm)
        self.assertEqual(len(sequencer.instruction_list), 2)  # wait and end of program

        if isinstance(tmp_cmd, SeqWaitImm):
            self.assertEqual(tmp_cmd.immediate, 6)  # Assign 1 cycle + wait 5 cycle

    def test_synch_for_range(self):
        self.job3._build_program()
        sequencer = self.job3.cell_seq_dict[self.job3.cells[0]]

        self.assertIsInstance(sequencer.instruction_list[0], SeqWaitImm)  # wait
        self.assertIsInstance(
            sequencer.instruction_list[1], SeqRegImmediateInst
        )  # for range end value to register
        self.assertIsInstance(
            sequencer.instruction_list[2], SeqRegImmediateInst
        )  # for range start value to register
        self.assertIsInstance(
            sequencer.instruction_list[3], SeqBranch
        )  # for range value check

        sequencer = self.job3.cell_seq_dict[self.job3.cells[1]]
        self.assertIsInstance(
            sequencer.instruction_list[0], SeqWaitImm
        )  # wait implicitly added before ForRange
        self.assertIsInstance(
            sequencer.instruction_list[1], SeqRegImmediateInst
        )  # for range end value to register
        self.assertIsInstance(
            sequencer.instruction_list[2], SeqRegImmediateInst
        )  # for range start value to register
        self.assertIsInstance(
            sequencer.instruction_list[3], SeqBranch
        )  # for range value check

    def test_synch_If(self):
        self.job4._build_program()
        sequencer = self.job4.cell_seq_dict[self.job4.cells[0]]

        self.assertIsInstance(sequencer.instruction_list[0], SeqWaitImm)  # wait
        self.assertIsInstance(
            sequencer.instruction_list[1], SeqRegImmediateInst
        )  # if condition value to register
        self.assertIsInstance(sequencer.instruction_list[2], SeqBranch)  # If check

        sequencer = self.job4.cell_seq_dict[self.job4.cells[1]]
        self.assertIsInstance(
            sequencer.instruction_list[0], SeqWaitImm
        )  # wait implicitly added before If
        self.assertIsInstance(
            sequencer.instruction_list[1], SeqRegImmediateInst
        )  # if condition value to register
        self.assertIsInstance(sequencer.instruction_list[2], SeqBranch)  # If check

    def test_synch_Parallel(self):
        with QiJob(skip_nco_sync=True) as job:
            q = QiCells(3)
            Wait(q[0], self.time)
            with Parallel():
                Play(q[0], QiPulse(self.time))
                Play(q[1], QiPulse(self.time))
            with Parallel():
                Wait(q[0], self.time)
                Wait(q[1], self.time)

        job._build_program()
        sequencer = job.cell_seq_dict[job.cells[0]]

        self.assertIsInstance(sequencer.instruction_list[0], SeqWaitImm)
        self.assertIsInstance(sequencer.instruction_list[1], SeqTrigger)

        sequencer = job.cell_seq_dict[job.cells[1]]
        self.assertIsInstance(
            sequencer.instruction_list[0], SeqWaitImm
        )  # wait implicitly added before Parallel
        self.assertIsInstance(sequencer.instruction_list[1], SeqTrigger)

    def test_synch_inside_ForRange(self):
        double_time = self.time * 2
        with QiJob(skip_nco_sync=True) as job:
            q = QiCells(3)
            var1 = QiVariable(int)
            with ForRange(var1, 0, 5):
                Wait(q[0], double_time)
                Wait(q[1], self.time)

        job._build_program()
        sequencer = job.cell_seq_dict[job.cells[0]]

        self.assertIsInstance(
            sequencer.instruction_list[0], SeqRegImmediateInst
        )  # for range end value to register
        self.assertIsInstance(
            sequencer.instruction_list[1], SeqRegImmediateInst
        )  # for range start value to register
        self.assertIsInstance(
            sequencer.instruction_list[2], SeqBranch
        )  # for range value check
        self.assertIsInstance(sequencer.instruction_list[3], SeqWaitImm)  # wait

        sequencer = job.cell_seq_dict[job.cells[1]]
        self.assertIsInstance(
            sequencer.instruction_list[0], SeqRegImmediateInst
        )  # for range end value to register
        self.assertIsInstance(
            sequencer.instruction_list[1], SeqRegImmediateInst
        )  # for range start value to register
        self.assertIsInstance(
            sequencer.instruction_list[2], SeqBranch
        )  # for range value check
        self.assertIsInstance(sequencer.instruction_list[3], SeqWaitImm)  # first wait

        tmp_cmd = sequencer.instruction_list[4]
        self.assertIsInstance(tmp_cmd, SeqWaitImm)  # implicitly added wait

        if isinstance(tmp_cmd, SeqWaitImm):
            self.assertEqual(tmp_cmd.immediate, util.conv_time_to_cycles(self.time))

    def test_synch_inside_ForRange_variable_start(self):
        double_time = self.time * 2
        with QiJob(skip_nco_sync=True) as var_start:
            q = QiCells(3)
            var1 = QiVariable(int)
            var2 = QiVariable(int, 0)
            with ForRange(var1, var2, 5):
                Wait(q[0], double_time)
                Wait(q[1], self.time)

        var_start._build_program()
        sequencer = var_start.cell_seq_dict[var_start.cells[0]]

        self.assertIsInstance(
            sequencer.instruction_list[0], SeqRegImmediateInst
        )  # set value var2

        self.assertIsInstance(
            sequencer.instruction_list[1], SeqRegImmediateInst
        )  # for range end value to register

        self.assertIsInstance(
            sequencer.instruction_list[2], SeqRegImmediateInst
        )  # for range start value to register

        self.assertIsInstance(
            sequencer.instruction_list[3], SeqBranch
        )  # for range value check

        self.assertIsInstance(sequencer.instruction_list[4], SeqWaitImm)  # wait

        sequencer = var_start.cell_seq_dict[var_start.cells[1]]
        self.assertIsInstance(
            sequencer.instruction_list[0], SeqRegImmediateInst
        )  # set value var2

        self.assertIsInstance(
            sequencer.instruction_list[1], SeqRegImmediateInst
        )  # for range end value to register

        self.assertIsInstance(
            sequencer.instruction_list[2], SeqRegImmediateInst
        )  # for range start value to register

        self.assertIsInstance(
            sequencer.instruction_list[3], SeqBranch
        )  # for range value check

        self.assertIsInstance(sequencer.instruction_list[4], SeqWaitImm)  # first wait

        tmp_cmd = sequencer.instruction_list[5]
        self.assertIsInstance(tmp_cmd, SeqWaitImm)  # implicitly added wait

        if isinstance(tmp_cmd, SeqWaitImm):
            self.assertEqual(tmp_cmd.immediate, util.conv_time_to_cycles(self.time))

    def test_synch_inside_ForRange_variable_end(self):
        double_time = self.time * 2
        with QiJob(skip_nco_sync=True) as var_end:
            q = QiCells(3)
            var1 = QiVariable(int)
            var2 = QiVariable(int, 5)
            with ForRange(var1, 0, var2):
                Wait(q[0], double_time)
                Wait(q[1], self.time)

        var_end._build_program()
        sequencer = var_end.cell_seq_dict[var_end.cells[0]]

        self.assertIsInstance(
            sequencer.instruction_list[0], SeqRegImmediateInst
        )  # set value var2
        self.assertIsInstance(
            sequencer.instruction_list[1], SeqRegImmediateInst
        )  # for range start/end value to register
        self.assertIsInstance(
            sequencer.instruction_list[2], SeqBranch
        )  # for range value check
        self.assertIsInstance(sequencer.instruction_list[3], SeqWaitImm)  # wait

        sequencer = var_end.cell_seq_dict[var_end.cells[1]]
        self.assertIsInstance(
            sequencer.instruction_list[0], SeqRegImmediateInst
        )  # set value var2
        self.assertIsInstance(
            sequencer.instruction_list[1], SeqRegImmediateInst
        )  # for range start/end value to register
        self.assertIsInstance(
            sequencer.instruction_list[2], SeqBranch
        )  # for range value check
        self.assertIsInstance(sequencer.instruction_list[3], SeqWaitImm)  # first wait

        tmp_cmd = sequencer.instruction_list[4]
        self.assertIsInstance(tmp_cmd, SeqWaitImm)  # implicitly added wait

        if isinstance(tmp_cmd, SeqWaitImm):
            self.assertEqual(tmp_cmd.immediate, util.conv_time_to_cycles(self.time))


class ExplicitSyncTests(unittest.TestCase):
    def test_explicit_sync(self):
        with QiJob() as job:
            cells = QiCells(2)

            a = QiVariable(name="A", value=3)

            with If(a == 1):
                Wait(cells[0], 12e-9)

            Sync(cells[0], cells[1])
            Play(cells[0], QiPulse(20e-9))
            Play(cells[1], QiPulse(20e-9))

        job._build_program()
        asm = job.cell_seq_dict[cells[0]].instruction_list

        # program start
        self.assertIsInstance(asm[0], SeqTrigger)
        # load initial variable value 3
        self.assertIsInstance(asm[1], SeqRegImmediateInst)
        # load value to compare to
        self.assertIsInstance(asm[2], SeqRegImmediateInst)
        # branch
        self.assertIsInstance(asm[3], SeqBranch)
        # If then body (wait)
        self.assertIsInstance(asm[4], SeqWaitImm)
        # Sync instruction, because implicit sync is impossible due to if-else before.
        self.assertIsInstance(asm[5], SeqCellSync)
        # Pulse
        self.assertIsInstance(asm[6], SeqTrigger)
        self.assertIsInstance(asm[7], SeqWaitImm)
        # End of program
        self.assertIsInstance(asm[8], SeqEnd)

    def test_explicit_sync_before_if(self):
        with QiJob() as job:
            cells = QiCells(2)

            a = QiVariable(name="A", value=3)

            with If(a == 1):
                Wait(cells[0], 12e-9)

            with If(a == 2):
                Play(cells[0], QiPulse(20e-9))
                Play(cells[1], QiPulse(20e-9))

        job._build_program()
        asm = job.cell_seq_dict[cells[0]].instruction_list

        # program start
        self.assertIsInstance(asm[0], SeqTrigger)
        # load initial variable value 3
        self.assertIsInstance(asm[1], SeqRegImmediateInst)
        # load value to compare to
        self.assertIsInstance(asm[2], SeqRegImmediateInst)
        # branch
        self.assertIsInstance(asm[3], SeqBranch)
        # If then body (wait)
        self.assertIsInstance(asm[4], SeqWaitImm)
        # new if-else requires syncing which is explicit due to if-else before.
        self.assertIsInstance(asm[5], SeqCellSync)
        # load value to compare to
        self.assertIsInstance(asm[6], SeqRegImmediateInst)
        # branch
        self.assertIsInstance(asm[7], SeqBranch)
        # Pulse
        self.assertIsInstance(asm[8], SeqTrigger)
        self.assertIsInstance(asm[9], SeqWaitImm)
        # End of program
        self.assertIsInstance(asm[10], SeqEnd)

    def test_explicit_sync_before_parallel(self):
        with QiJob() as job:
            cells = QiCells(2)

            a = QiVariable(name="A", value=3)

            with If(a == 1):
                Wait(cells[0], 12e-9)

            with Parallel():
                Wait(cells[0], 20e-9)
                Wait(cells[1], 20e-9)

        job._build_program()
        asm0 = job.cell_seq_dict[cells[0]].instruction_list

        # program start
        self.assertIsInstance(asm0[0], SeqTrigger)
        # load initial variable value 3
        self.assertIsInstance(asm0[1], SeqRegImmediateInst)
        # load value to compare to
        self.assertIsInstance(asm0[2], SeqRegImmediateInst)
        # branch
        self.assertIsInstance(asm0[3], SeqBranch)
        # If then body (wait)
        self.assertIsInstance(asm0[4], SeqWaitImm)
        # parallel requires syncing which is explicit due to if-else before.
        self.assertIsInstance(asm0[5], SeqCellSync)
        # Parallel body wait
        self.assertIsInstance(asm0[6], SeqWaitImm)
        # End of program
        self.assertIsInstance(asm0[7], SeqEnd)

        asm1 = job.cell_seq_dict[cells[1]].instruction_list

        # program start
        self.assertIsInstance(asm1[0], SeqTrigger)
        # sync before parallel
        self.assertIsInstance(asm1[1], SeqCellSync)
        # wait in parallel body
        self.assertIsInstance(asm1[2], SeqWaitImm)
        # End of program
        self.assertIsInstance(asm1[3], SeqEnd)

    def test_explicit_sync_at_end_of_forrange_body(self):
        with QiJob() as job:
            cells = QiCells(2)

            a = QiVariable(name="A")

            with ForRange(a, 8e-9, 100e-9, 4e-9):
                Wait(cells[0], 12e-9)
                Wait(cells[1], a)

        job._build_program()
        asm0 = job.cell_seq_dict[cells[0]].instruction_list

        # Program start
        self.assertIsInstance(asm0[0], SeqTrigger)
        # load loop end value
        self.assertIsInstance(asm0[1], SeqRegImmediateInst)
        # load loop start value
        self.assertIsInstance(asm0[2], SeqRegImmediateInst)
        # loop branch
        self.assertIsInstance(asm0[3], SeqBranch)
        # Wait in loop
        self.assertIsInstance(asm0[4], SeqWaitImm)
        # Explicit sync because of wait with non constant length;
        self.assertIsInstance(asm0[5], SeqCellSync)
        # Increase loop variable
        self.assertIsInstance(asm0[6], SeqRegImmediateInst)
        # Jump back
        self.assertIsInstance(asm0[7], SeqJump)

        self.assertIsInstance(asm0[8], SeqEnd)

        job._build_program()
        asm1 = job.cell_seq_dict[cells[1]].instruction_list

        # Program start
        self.assertIsInstance(asm1[0], SeqTrigger)
        # load loop end value
        self.assertIsInstance(asm1[1], SeqRegImmediateInst)
        # load loop start value
        self.assertIsInstance(asm1[2], SeqRegImmediateInst)
        # loop branch
        self.assertIsInstance(asm1[3], SeqBranch)
        # Wait in loop
        self.assertIsInstance(asm1[4], SeqWaitRegister)
        # Explicit sync because of wait with non constant length;
        self.assertIsInstance(asm1[5], SeqCellSync)
        # Increase loop variable
        self.assertIsInstance(asm1[6], SeqRegImmediateInst)
        # Jump back
        self.assertIsInstance(asm1[7], SeqJump)

        self.assertIsInstance(asm1[8], SeqEnd)

    def test_explicit_sync_after_loop_unroll0(self):
        with QiJob() as job:
            cells = QiCells(2)

            a = QiVariable(name="A")
            b = QiVariable(name="B")

            with ForRange(a, b, 100e-9, 4e-9):
                Wait(cells[0], 12e-9)
                Wait(cells[1], b)

        job._build_program()
        asm0 = job.cell_seq_dict[cells[0]].instruction_list

        # explicit sync after unroll0
        self.assertIsInstance(asm0[4], SeqCellSync)
        # explicit sync after unroll1
        self.assertIsInstance(asm0[12], SeqCellSync)
        # explicit sync after loop body
        self.assertIsInstance(asm0[17], SeqCellSync)

        asm1 = job.cell_seq_dict[cells[1]].instruction_list

        # explicit sync after unroll0
        self.assertIsInstance(asm1[4], SeqCellSync)
        # explicit sync after unroll1
        self.assertIsInstance(asm1[12], SeqCellSync)
        # explicit sync after loop body
        self.assertIsInstance(asm1[17], SeqCellSync)

    def test_implicit_sync_after_explicit_sync(self):
        with QiJob() as job:
            cells = QiCells(2)

            a = QiVariable(name="A")

            with If(a == 1):
                Wait(cells[0], 12e-9)

            # Explicit sync, due to if-else
            Sync(cells[0], cells[1])

            Wait(cells[0], 20e-9)

            # Implicit sync, due to same syncpoint and constant wait.
            Sync(cells[0], cells[1])

        job._build_program()
        asm0 = job.cell_seq_dict[cells[0]].instruction_list
        # program start
        self.assertIsInstance(asm0[0], SeqTrigger)
        # load if comparison value
        self.assertIsInstance(asm0[1], SeqRegImmediateInst)
        # if branch
        self.assertIsInstance(asm0[2], SeqBranch)
        # wait in if
        self.assertIsInstance(asm0[3], SeqWaitImm)
        # first sync command, which is explicit.
        self.assertIsInstance(asm0[4], SeqCellSync)
        # second wait
        self.assertIsInstance(asm0[5], SeqWaitImm)
        # second sync command is implicit and therefore not represented in this cell
        # program end
        self.assertIsInstance(asm0[6], SeqEnd)

        asm1 = job.cell_seq_dict[cells[1]].instruction_list
        # program start
        self.assertIsInstance(asm1[0], SeqTrigger)
        # first sync command, which is explicit.
        self.assertIsInstance(asm1[1], SeqCellSync)
        # wait to implicitely sync for the second sync command.
        self.assertIsInstance(asm1[2], SeqWaitImm)
        # program end
        self.assertIsInstance(asm1[3], SeqEnd)

    def test_sync_without_cells(self):
        with QiJob() as job:
            cells = QiCells(3)

            a = QiVariable(name="A")

            with If(a == 1):
                Wait(cells[0], 12e-9)

            Sync()

        job._build_program()

        self.assertIsInstance(
            job.cell_seq_dict[cells[0]].instruction_list[4], SeqCellSync
        )
        self.assertIsInstance(
            job.cell_seq_dict[cells[1]].instruction_list[1], SeqCellSync
        )
        self.assertIsInstance(
            job.cell_seq_dict[cells[2]].instruction_list[1], SeqCellSync
        )


class QiParallelToSeq(unittest.TestCase):
    def setUp(self) -> None:
        with QiJob(skip_nco_sync=True) as self.job1:
            q = QiCells(1)
            with Parallel():
                Play(q[0], QiPulse(24e-9))
            with Parallel():
                PlayReadout(q[0], QiPulse(48e-9))

        with QiJob(skip_nco_sync=True) as self.job2:
            q = QiCells(1)
            with Parallel():
                Play(q[0], QiPulse(24e-9))
                Play(q[0], QiPulse(24e-9))
            with Parallel():
                PlayReadout(q[0], QiPulse(48e-9))

        self.recording_length = 200e-9

        with QiJob(skip_nco_sync=True) as self.job3:
            q = QiCells(1)
            q[0]["recording_length"] = self.recording_length
            with Parallel():
                Wait(q[0], 4e-9)
                Play(q[0], QiPulse(24e-9))
            with Parallel():
                PlayReadout(q[0], QiPulse(48e-9))
                Recording(q[0], q[0]["recording_length"])

    def test_parallel_job1(self):
        # parallel trigger should be combined
        self.job1._build_program()
        sequencer = self.job1.cell_seq_dict[self.job1.cells[0]]

        self.assertEqual(
            len(sequencer.instruction_list), 3
        )  # combined trigger, wait, end

        self.assertIsInstance(
            sequencer.instruction_list[0], SeqTrigger
        )  # combined in single trigger

        wait = sequencer.instruction_list[1]
        self.assertIsInstance(wait, SeqWaitImm)  # combined in single trigger

        if isinstance(wait, SeqWaitImm):
            self.assertEqual(wait.immediate, 11)

    def test_parallel_job2(self):
        # Combine first play and playreadout, at 24e-9 add another trigger
        self.job2._build_program()
        sequencer = self.job2.cell_seq_dict[self.job2.cells[0]]

        self.assertEqual(
            len(sequencer.instruction_list), 5
        )  # combined trigger, wait, trigger, wait, end

        self.assertIsInstance(
            sequencer.instruction_list[0], SeqTrigger
        )  # combined in single trigger

        wait = sequencer.instruction_list[1]
        self.assertIsInstance(wait, SeqWaitImm)  # combined in single trigger

        if isinstance(wait, SeqWaitImm):
            self.assertEqual(wait.immediate, 5)

        self.assertIsInstance(
            sequencer.instruction_list[2], SeqTrigger
        )  # combined in single trigger

        wait = sequencer.instruction_list[3]
        self.assertIsInstance(wait, SeqWaitImm)  # combined in single trigger

        if isinstance(wait, SeqWaitImm):
            self.assertEqual(wait.immediate, 5)

    def test_parallel_job3(self):
        # ignore first wait, trigger readout, then manipulation, then wait until recording is finished
        self.job3._build_program()
        sequencer = self.job3.cell_seq_dict[self.job3.cells[0]]

        self.assertEqual(
            len(sequencer.instruction_list), 5
        )  # trigger, trigger,  triggerwait, wait, end

        self.assertIsInstance(sequencer.instruction_list[0], SeqTrigger)  # Readout

        self.assertIsInstance(sequencer.instruction_list[1], SeqTrigger)  # Manipulation

        wait = sequencer.instruction_list[2]
        self.assertIsInstance(wait, SeqWaitImm)  # combined in single trigger

        if isinstance(wait, SeqWaitImm):
            self.assertEqual(wait.immediate, 5)

        # Another Wait should be added to wait until
        wait = sequencer.instruction_list[3]
        self.assertIsInstance(wait, SeqWaitImm)  # combined in single trigger

        wait_cycles = (
            util.conv_time_to_cycles(self.recording_length)
            - (1 + 1 + 5)
            + sequencer.RECORDING_MODULE_DELAY_CYCLES
        )  # trigger+trigger+ 5 triggerwait

        if isinstance(wait, SeqWaitImm):
            self.assertEqual(
                wait.immediate, wait_cycles
            )  # trigger, trigger, 5 triggerwait, 5 wait

    def test_parallel_multiple_cells(self):
        rec_length = 400e-9
        with QiJob(skip_nco_sync=True) as multiple_cells:
            q = QiCells(2)
            with Parallel():
                Wait(q[0], 4e-9)
                Play(q[0], QiPulse(24e-9))
                Wait(q[1], 4e-9)
                Play(q[1], QiPulse(24e-9))
            with Parallel():
                PlayReadout(q[1], QiPulse(48e-9))
                Recording(q[1], rec_length)
                PlayReadout(q[0], QiPulse(48e-9))
                Recording(q[0], rec_length)

        multiple_cells._build_program()

        for i in range(0, 2):
            sequencer = multiple_cells.cell_seq_dict[
                multiple_cells.cells[i]
            ]  # same program for both cells

            self.assertEqual(
                len(sequencer.instruction_list), 5
            )  # trigger, trigger,  triggerwait, wait, end

            self.assertIsInstance(sequencer.instruction_list[0], SeqTrigger)  # Readout

            self.assertIsInstance(
                sequencer.instruction_list[1], SeqTrigger
            )  # Manipulation

            wait = sequencer.instruction_list[2]
            self.assertIsInstance(wait, SeqWaitImm)

            if isinstance(wait, SeqWaitImm):
                self.assertEqual(wait.immediate, 5)

            # Another Wait should be added to wait until rec finished
            wait = sequencer.instruction_list[3]
            self.assertIsInstance(wait, SeqWaitImm)

            wait_cycles = (
                util.conv_time_to_cycles(rec_length)
                - (1 + 1 + 5)
                + sequencer.RECORDING_MODULE_DELAY_CYCLES
            )  # trigger+trigger+ 5 triggerwait

            if isinstance(wait, SeqWaitImm):
                self.assertEqual(
                    wait.immediate, wait_cycles
                )  # trigger, trigger, 5 triggerwait, 5 wait

    def test_variable_length(self):
        rec_length = 400e-9
        with QiJob(skip_nco_sync=True) as para_test:
            q = QiCells(1)
            var1 = QiTimeVariable(4e-9)
            var2 = QiTimeVariable(24e-9)

            with Parallel():
                Wait(q[0], var1)
                Play(q[0], QiPulse(var2))
                Play(q[0], QiPulse(var2))
            with Parallel():
                PlayReadout(q[0], QiPulse(48e-9))
                Recording(q[0], rec_length)

        para_test._build_program()

        sequencer = para_test.cell_seq_dict[para_test.cells[0]]

        # assign, assign, trigger readout, trigger manip,  triggerwait, trigger manip, triggerwait, choke manip, wait, end
        self.assertEqual(len(sequencer.instruction_list), 10)

        self.assertIsInstance(sequencer.instruction_list[2], SeqTrigger)  # Readout

        self.assertIsInstance(sequencer.instruction_list[3], SeqTrigger)  # Manipulation

        self.assertIsInstance(sequencer.instruction_list[4], SeqWaitImm)  # Wait

        self.assertIsInstance(sequencer.instruction_list[5], SeqTrigger)  # Manipulation

        self.assertIsInstance(sequencer.instruction_list[6], SeqWaitImm)  # Wait

        self.assertIsInstance(sequencer.instruction_list[7], SeqTrigger)  # Choke

        self.assertIsInstance(
            sequencer.instruction_list[8], SeqWaitImm
        )  # Wait until rec finished

        wait = sequencer.instruction_list[4]
        self.assertIsInstance(wait, SeqWaitImm)

        if isinstance(wait, SeqWaitImm):
            self.assertEqual(wait.immediate, 5)

        trigger = sequencer.instruction_list[5]
        if isinstance(trigger, SeqTrigger):
            self.assertNotEqual(
                trigger._trig_indices[_TriggerModules.MANIPULATION],
                Sequencer.CHOKE_PULSE_INDEX,
            )

        wait = sequencer.instruction_list[6]
        self.assertIsInstance(wait, SeqWaitImm)

        if isinstance(wait, SeqWaitImm):
            self.assertEqual(wait.immediate, 5)

        choke = sequencer.instruction_list[7]
        if isinstance(choke, SeqTrigger):
            self.assertEqual(
                choke._trig_indices[_TriggerModules.MANIPULATION],
                Sequencer.CHOKE_PULSE_INDEX,
            )
            self.assertEqual(choke._trig_indices[_TriggerModules.READOUT], 0)

        # Another Wait should be added to wait until end
        wait = sequencer.instruction_list[8]
        self.assertIsInstance(wait, SeqWaitImm)  # combined in single trigger

        wait_cycles = (
            util.conv_time_to_cycles(rec_length)
            - (3 + 10 + 1)
            + sequencer.RECORDING_MODULE_DELAY_CYCLES
        )  # 2 trigger + 5 triggerwait + 1 choke trigger

        if isinstance(wait, SeqWaitImm):
            self.assertEqual(
                wait.immediate, wait_cycles
            )  # trigger, trigger, 5 triggerwait, 5 wait

    def test_variable_length_end_choke(self):
        # Test if final choke command is added
        with QiJob(skip_nco_sync=True) as para_test:
            q = QiCells(1)
            var = QiTimeVariable(24e-9)

            with Parallel():
                Wait(q[0], 8e-9)
                Play(q[0], QiPulse(var))
            with Parallel():
                PlayReadout(q[0], QiPulse(24e-9))

        para_test._build_program()

        sequencer = para_test.cell_seq_dict[para_test.cells[0]]

        # assign, trigger readout, wait, trigger manip,  wait, choke manip, end
        self.assertEqual(len(sequencer.instruction_list), 7)

        self.assertIsInstance(sequencer.instruction_list[1], SeqTrigger)  # Readout

        self.assertIsInstance(sequencer.instruction_list[2], SeqWaitImm)  # Wait

        self.assertIsInstance(sequencer.instruction_list[3], SeqTrigger)  # Manipulation

        self.assertIsInstance(sequencer.instruction_list[4], SeqWaitImm)  # Manipulation

        self.assertIsInstance(sequencer.instruction_list[5], SeqTrigger)  # Choke

    def test_parallel_sync(self):
        length = 12e-9
        with QiJob(skip_nco_sync=True) as para_test:
            q = QiCells(2)

            Play(
                q[1], QiPulse(length)
            )  # q[0] should receive wait-instruction with length

            with Parallel():
                Play(q[0], QiPulse(24e-9))
                Play(q[1], QiPulse(24e-9))
            with Parallel():
                PlayReadout(q[0], QiPulse(48e-9))
                PlayReadout(q[1], QiPulse(48e-9))

        para_test._build_program()

        sequencer = para_test.cell_seq_dict[para_test.cells[0]]

        wait = sequencer.instruction_list[0]
        self.assertIsInstance(wait, SeqWaitImm)  # Wait inserted by synch operation

        if isinstance(wait, SeqWaitImm):
            self.assertEqual(wait.immediate, util.conv_time_to_cycles(length))

    def test_variable_length_undefined(self):
        with QiJob(skip_nco_sync=True) as para_test:
            q = QiCells(1)
            var1 = QiTimeVariable()
            var2 = QiTimeVariable()
            with Parallel():
                Wait(q[0], var1)
                Play(q[0], QiPulse(var2))
            with Parallel():
                PlayReadout(q[0], QiPulse(48e-9))
                Recording(q[0], 48e-9)

        with self.assertRaises(RuntimeError):
            para_test._build_program()

    def test_variable_length_invalid(self):
        with QiJob(skip_nco_sync=True) as para_test:
            q = QiCells(1)
            var1 = QiTimeVariable()
            Assign(var1, 4e-9)
            var2 = QiTimeVariable()
            Assign(var2, 24e-9)
            with If(var1 == 4):
                Assign(var1, 8e-9)  # invalidates var1
            with Parallel():
                Wait(q[0], var1)
                Play(q[0], QiPulse(var2))
            with Parallel():
                PlayReadout(q[0], QiPulse(48e-9))
                Recording(q[0], 48e-9)

        with self.assertRaises(RuntimeError):
            para_test._build_program()


class SequencerCyclesAfterLoopTest(unittest.TestCase):
    def setUp(self):
        with QiJob(skip_nco_sync=True) as self.job1:
            q = QiCells(1)
            var1 = QiVariable()
            with ForRange(var1, 0, 5, 1):
                Play(q[0], QiPulse(length=4e-9))

        with QiJob(skip_nco_sync=True) as self.job2:
            q = QiCells(1)
            var1 = QiVariable(int)
            with ForRange(var1, 5, 0, -1):
                Play(q[0], QiPulse(length=4e-9))

        with QiJob(skip_nco_sync=True) as self.job3:
            q = QiCells(1)
            var2 = QiTimeVariable()
            with ForRange(var2, 8e-9, 24e-9, 4e-9):
                Play(q[0], QiPulse(length=var2))
                Play(q[0], QiPulse(length=4e-9))

        with QiJob(skip_nco_sync=True) as self.job4:
            q = QiCells(1)
            var2 = QiTimeVariable()
            with ForRange(var2, 24e-9, 8e-9, -4e-9):
                Play(q[0], QiPulse(length=var2))
                Play(q[0], QiPulse(length=4e-9))

        with QiJob(skip_nco_sync=True) as self.job5:
            q = QiCells(1)
            var1 = QiVariable()
            with ForRange(var1, 5, 0, -1):
                with If(var1 == 0):
                    Play(q[0], QiPulse(length=4e-9))

        with QiJob(skip_nco_sync=True) as self.job6:
            q = QiCells(1)
            var2 = QiTimeVariable()
            with ForRange(var2, 8e-9, 24e-9, 4e-9):
                with Parallel():
                    Play(q[0], QiPulse(length=4e-9))
                    PlayReadout(q[0], QiPulse(length=4e-9))

    def test_for_range_cycles(self):
        self.job1._build_program()
        sequencer = self.job1.cell_seq_dict[self.job1.cells[0]]
        # Set up For Range 2cyc, (Branch 1cyc + Trigger 1cyc + Add 1cyc + Jump 2cyc) * 5 + Branch 2cyc + End 1cyc
        self.assertEqual(sequencer.prog_cycles, 30)

        self.job2._build_program()
        sequencer = self.job2.cell_seq_dict[self.job2.cells[0]]
        # Set up For Range 1cyc (uses reg0 as endval --> no load to reg needed), (Branch 1cyc + Trigger 1cyc + Add 1cyc + Jump 2cyc) * 5 + Branch 2cyc + End 1cyc
        self.assertEqual(sequencer.prog_cycles, 29)

    def test_for_range_variable_cycles(self):
        self.job3._build_program()
        sequencer = self.job3.cell_seq_dict[self.job3.cells[0]]
        # Set up For Range 2cyc, (Branch 1 + Trigger 1 + Add 1 + Jump 2) * 4 + Branch 2 + End 1
        # variable pulse trigger: (1wait + 1trigger) + (2w + 1t) + (3w + 1t) + (4w + 1t)
        self.assertEqual(sequencer.prog_cycles, 39)

        self.job4._build_program()
        sequencer = self.job4.cell_seq_dict[self.job4.cells[0]]
        # Set up For Range 2cyc, (Branch 1 + Trigger 1 + Add 1 + Jump 2) * 4 + Branch 2 + End 1 + (6 + 1) + (5 + 1) + (4 + 1) + (3 + 1)
        self.assertEqual(sequencer.prog_cycles, 43)

    def test_FR_cycles_If(self):
        # Using If should invalidate prog_cycles
        self.job5._build_program()
        sequencer = self.job5.cell_seq_dict[self.job5.cells[0]]

        self.assertEqual(sequencer.prog_cycles, -1)

    def test_FR_cycles_Parallel(self):
        # parallel uses variable length so another trigger is added to stop ongoing trigger
        self.job6._build_program()
        sequencer = self.job6.cell_seq_dict[self.job6.cells[0]]
        # Set up For Range 2cyc, (Branch 1cyc + Add 1cyc + Trigger 1 + Trigger 1+ Jump 2cyc) * 4 + Branch 2cyc + End 1cyc
        self.assertEqual(sequencer.prog_cycles, 29)

    def test_FR_cycles_var_start(self):
        with QiJob(skip_nco_sync=True) as job:
            q = QiCells(1)
            var1 = QiVariable(int)
            var2 = QiVariable(int, 0)
            with ForRange(var1, var2, 5):
                Play(q[0], QiPulse(24e-9))

        job._build_program()
        sequencer = job.cell_seq_dict[job.cells[0]]

        # (var2 = 0) 1 cyc + Set up For Range 2cyc, (Branch 1cyc + Add 1cyc + Trigger 1 + WaitTrigger 4
        # + Trigger 1+ Jump 2) * 5 + Branch 2cyc + End 1cyc
        self.assertEqual(sequencer.prog_cycles, -1)

    def test_FR_cycles_var_start_invalid(self):
        with QiJob(skip_nco_sync=True) as job:
            q = QiCells(1)
            var1 = QiVariable(int)
            var2 = QiVariable(int, 0)

            with If(var2 == 0):
                Assign(var2, 2)  # should invalidate var2
            with ForRange(var1, var2, 5):
                Play(q[0], QiPulse(24e-9))

        job._build_program()
        sequencer = job.cell_seq_dict[job.cells[0]]

        self.assertEqual(sequencer.prog_cycles, -1)

    def test_FR_cycles_var_end(self):
        with QiJob(skip_nco_sync=True) as job:
            q = QiCells(1)
            var1 = QiVariable(int)
            var2 = QiVariable(int, 5)
            with ForRange(var1, 0, var2):
                Play(q[0], QiPulse(24e-9))

        job._build_program()
        sequencer = job.cell_seq_dict[job.cells[0]]

        # (var2 = 5) 1 cyc + Set up For Range 1cyc (end_val already loaded at var2), (Branch 1cyc + Add 1cyc
        # + Trigger 1 + WaitTrigger 4 + Trigger 1 + Jump 2) * 5 + Branch 2cyc + End 1cyc
        self.assertEqual(sequencer.prog_cycles, -1)

    def test_FR_cycles_var_end_invalid(self):
        with QiJob(skip_nco_sync=True) as job:
            q = QiCells(1)
            var1 = QiVariable(int)
            var2 = QiVariable(int)
            with ForRange(var1, 0, var2):
                Play(q[0], QiPulse(24e-9))

        job._build_program()
        sequencer = job.cell_seq_dict[job.cells[0]]

        self.assertEqual(sequencer.prog_cycles, -1)


class ForRangeEntryTest(unittest.TestCase):
    def test_sequential_for_range(self):
        with QiJob(skip_nco_sync=True) as test_fr:
            q = QiCells(1)
            var1 = QiTimeVariable()
            var2 = QiVariable(int)

            with ForRange(var1, 0, 24e-9, 4e-9):
                Play(q[0], QiPulse(var1))

            with ForRange(var2, 5, 0, -1):
                Play(q[0], QiPulse(24e-9))

        test_fr._build_program()
        sequencer = test_fr.cell_seq_dict[test_fr.cells[0]]

        entry = sequencer._for_range_list[0]

        # unroll var1 == 4e-9 --> #0 reg_imm, #1 trigger, #2 end trigger
        self.assertEqual(entry.end_addr, 2)
        self.assertEqual(entry.start, 1)  # 0 and 1 unrolled
        self.assertEqual(entry.end, 2)
        self.assertEqual(entry.step, 1)
        self.assertEqual(entry.reg_addr, sequencer.get_var_register(var1).adr)
        self.assertEqual(entry.iterations, 1)
        self.assertEqual(entry.aggregate_iterations, 1)

        entry = sequencer._for_range_list[1]

        # unroll var1 == 0 --> nothing
        # unroll var1 == 4e-9 --> #0 reg_imm, #1 trigger, #2 end trigger
        # loop --> #3 reg_imm, #4 reg_imm, #5 branch, #6 trigger, #7 wait, #8 end trigger, #9 add_var, #10 jump
        self.assertEqual(entry.end_addr, 10)
        self.assertEqual(entry.start, 2)  # 0 and 1 unrolled
        self.assertEqual(entry.end, 6)
        self.assertEqual(entry.step, 1)
        self.assertEqual(entry.reg_addr, sequencer.get_var_register(var1).adr)
        self.assertEqual(entry.iterations, 4)
        self.assertEqual(entry.aggregate_iterations, 4)

        entry = sequencer._for_range_list[2]

        self.assertEqual(
            entry.end_addr, 16
        )  # 9 reg_imm, #10 branch, #11 trigger, #12 wait, #13 add_var, #14 jump; end_val uses reg0, so doesnt need to be set up
        self.assertEqual(entry.start, 5)
        self.assertEqual(entry.end, 0)
        self.assertEqual(entry.step, -1)
        self.assertEqual(entry.reg_addr, sequencer.get_var_register(var2).adr)
        self.assertEqual(entry.iterations, 5)
        self.assertEqual(entry.aggregate_iterations, 5)

    def test_nested_for_range(self):
        with QiJob(skip_nco_sync=True) as test_fr:
            q = QiCells(1)
            var1 = QiTimeVariable()
            var2 = QiVariable(int)

            with ForRange(var1, 0, 24e-9, 4e-9):
                Play(q[0], QiPulse(var1))

                with ForRange(var2, 5, 0, -1):
                    Play(q[0], QiPulse(24e-9))

        test_fr._build_program()
        sequencer = test_fr.cell_seq_dict[test_fr.cells[0]]

        # unroll var1 == 0 --> generates entry with iteration = 1; aggregate 5 because of the contained loop
        entry = sequencer._for_range_list[0]

        self.assertEqual(
            entry.end_addr, 6
        )  # 1 reg_imm, #2 branch, #3 trigger, #4 wait, #5 add_var, #6 jump
        self.assertEqual(entry.start, 0)
        self.assertEqual(entry.end, 1)
        self.assertEqual(entry.step, 1)
        self.assertEqual(entry.reg_addr, sequencer.get_var_register(var1).adr)
        self.assertEqual(entry.iterations, 1)
        self.assertEqual(entry.aggregate_iterations, 5)

        # unroll var1 == 0 --> #0 start val, #1-6 unrolled nested loop
        # nested loop of unroll var1 == 0
        entry = sequencer._for_range_list[0].contained_entries[0]

        self.assertEqual(
            entry.end_addr, 6
        )  # 1 reg_imm, #2 branch, #3 trigger, #4 wait, #5 add_var, #6 jump
        self.assertEqual(entry.start, 5)
        self.assertEqual(entry.end, 0)
        self.assertEqual(entry.step, -1)
        self.assertEqual(entry.reg_addr, sequencer.get_var_register(var2).adr)
        self.assertEqual(entry.iterations, 5)
        self.assertEqual(entry.aggregate_iterations, 5)

        # unroll var1 == 1 --> generates entry with iteration = 1; aggregate 5 because of the contained loop
        entry = sequencer._for_range_list[1]

        self.assertEqual(
            entry.end_addr, 15
        )  # 1 reg_imm, #2 branch, #3 trigger, #4 wait, #5 add_var, #6 jump
        self.assertEqual(entry.start, 1)
        self.assertEqual(entry.end, 2)
        self.assertEqual(entry.step, 1)
        self.assertEqual(entry.reg_addr, sequencer.get_var_register(var1).adr)
        self.assertEqual(entry.iterations, 1)
        self.assertEqual(entry.aggregate_iterations, 5)

        # unroll var1 == 1 --> #7 start val, #8 trigger, #9 end trigger, #10-15 nested loop
        # nested loop of unroll var1 == 1
        entry = sequencer._for_range_list[1].contained_entries[0]

        self.assertEqual(
            entry.end_addr, 15
        )  # 10 reg_imm, #11 branch, #12 trigger, #13 wait, #14 add_var, #15 jump
        self.assertEqual(entry.start, 5)
        self.assertEqual(entry.end, 0)
        self.assertEqual(entry.step, -1)
        self.assertEqual(entry.reg_addr, sequencer.get_var_register(var2).adr)
        self.assertEqual(entry.iterations, 5)
        self.assertEqual(entry.aggregate_iterations, 5)

        # loop #16 reg_imm, #17 reg_imm, #18 branch, #19 trigger, #20 wait, #21 end trigger,
        # 22-27 nested loop #28 add_var, #29 jump
        entry = sequencer._for_range_list[2]

        self.assertEqual(entry.end_addr, 29)
        self.assertEqual(entry.start, 2)
        self.assertEqual(entry.end, 6)
        self.assertEqual(entry.step, 1)
        self.assertEqual(entry.reg_addr, sequencer.get_var_register(var1).adr)
        self.assertEqual(entry.iterations, 4)
        self.assertEqual(entry.aggregate_iterations, 20)  # 4*5 for nested loop

        entry = sequencer._for_range_list[2].contained_entries[0]

        self.assertEqual(
            entry.end_addr, 27
        )  # 22 reg_imm, #23 branch, #24 trigger, #25 wait, #26 add_var, #27 jump
        self.assertEqual(entry.start, 5)
        self.assertEqual(entry.end, 0)
        self.assertEqual(entry.step, -1)
        self.assertEqual(entry.reg_addr, sequencer.get_var_register(var2).adr)
        self.assertEqual(entry.iterations, 5)
        self.assertEqual(entry.aggregate_iterations, 5)

    def test_nested_for_range_2(self):
        with QiJob(skip_nco_sync=True) as test_fr:
            q = QiCells(1)
            var1 = QiTimeVariable()
            var2 = QiVariable(int)

            with ForRange(var2, 5, 0, -1):
                Play(q[0], QiPulse(24e-9))

                with ForRange(var1, 0, 24e-9, 4e-9):
                    Play(q[0], QiPulse(var1))

        test_fr._build_program()
        sequencer = test_fr.cell_seq_dict[test_fr.cells[0]]

        # var2 containing everything
        entry = sequencer._for_range_list[0]

        self.assertEqual(entry.end_addr, 16)
        # 0 var2 = 5, #1 branch, #2 trigger, #3 wait_trigger,
        # unroll var1==1:  #4 var1=1, #5 trigger #6 stop_trigger
        # inner loop:   #7 start_val, #8 end_val, 9# branch, 10# trigger, 11# wait_trigger, #12 stop_trigger, #13 add_var, #14 jump
        # finish outer : #15 add_var, #16 jump
        self.assertEqual(entry.start, 5)
        self.assertEqual(entry.end, 0)
        self.assertEqual(entry.step, -1)
        self.assertEqual(entry.reg_addr, sequencer.get_var_register(var2).adr)
        self.assertEqual(entry.iterations, 5)
        self.assertEqual(entry.aggregate_iterations, 25)

        entry = sequencer._for_range_list[0].contained_entries[0]

        self.assertEqual(entry.end_addr, 6)
        # unroll var1==1:  #4 var1=1, #5 trigger #6 stop_trigger
        self.assertEqual(entry.start, 1)
        self.assertEqual(entry.end, 2)
        self.assertEqual(entry.step, 1)
        self.assertEqual(entry.reg_addr, sequencer.get_var_register(var1).adr)
        self.assertEqual(entry.iterations, 1)
        self.assertEqual(entry.aggregate_iterations, 1)

        entry = sequencer._for_range_list[0].contained_entries[1]

        self.assertEqual(entry.end_addr, 14)
        # inner loop:   #7 start_val, #8 end_val, 9# branch, 10# trigger, 11# wait_trigger, #12 stop_trigger, #13 add_var, #14 jump
        self.assertEqual(entry.start, 2)
        self.assertEqual(entry.end, 6)
        self.assertEqual(entry.step, 1)
        self.assertEqual(entry.reg_addr, sequencer.get_var_register(var1).adr)
        self.assertEqual(entry.iterations, 4)
        self.assertEqual(entry.aggregate_iterations, 4)

    def test_nested_for_range_var_start(self):
        with QiJob(skip_nco_sync=True) as test_fr:
            q = QiCells(1)
            var1 = QiTimeVariable()
            var2 = QiVariable(int)
            var3 = QiVariable(int, 5)

            with ForRange(var2, var3, 0, -1):
                Play(q[0], QiPulse(24e-9))

                with ForRange(var1, 0, 24e-9, 4e-9):
                    Play(q[0], QiPulse(var1))

        test_fr._build_program()
        sequencer = test_fr.cell_seq_dict[test_fr.cells[0]]

        # var2 containing everything
        entry = sequencer._for_range_list[0]

        self.assertEqual(entry.end_addr, 17)
        # #0 var3 = 5 #1 var2 = 5, #2 branch, #3 trigger, #4 wait_trigger,
        # unroll var1==1:  #5 var1=1, #6 trigger #7 stop_trigger
        # inner loop:   #8 start_val, #9 end_val, 10# branch, 11# trigger, 12# wait_trigger, #13 stop_trigger, #14 add_var, #15 jump
        # finish outer : #16 add_var, #17 jump
        self.assertEqual(entry.start, 5)
        self.assertEqual(entry.end, 0)
        self.assertEqual(entry.step, -1)
        self.assertEqual(entry.reg_addr, sequencer.get_var_register(var2).adr)
        self.assertEqual(entry.iterations, 5)
        self.assertEqual(entry.aggregate_iterations, 25)

        entry = sequencer._for_range_list[0].contained_entries[0]

        self.assertEqual(entry.end_addr, 7)
        # unroll var1==1:  #5 var1=1, #6 trigger #7 stop_trigger
        self.assertEqual(entry.start, 1)
        self.assertEqual(entry.end, 2)
        self.assertEqual(entry.step, 1)
        self.assertEqual(entry.reg_addr, sequencer.get_var_register(var1).adr)
        self.assertEqual(entry.iterations, 1)
        self.assertEqual(entry.aggregate_iterations, 1)

        entry = sequencer._for_range_list[0].contained_entries[1]

        self.assertEqual(entry.end_addr, 15)
        # inner loop:   #8 start_val, #9 end_val, 10# branch, 11# trigger, 12# wait_trigger, #13 stop_trigger, #14 add_var, #15 jump
        self.assertEqual(entry.start, 2)
        self.assertEqual(entry.end, 6)
        self.assertEqual(entry.step, 1)
        self.assertEqual(entry.reg_addr, sequencer.get_var_register(var1).adr)
        self.assertEqual(entry.iterations, 4)
        self.assertEqual(entry.aggregate_iterations, 4)

    def test_nested_for_range_var_end(self):
        with QiJob(skip_nco_sync=True) as test_fr:
            q = QiCells(1)
            var1 = QiTimeVariable()
            var2 = QiVariable(int)
            var3 = QiVariable(int, 0)

            with ForRange(var2, 5, var3, -1):
                Play(q[0], QiPulse(24e-9))

                with ForRange(var1, 0, 24e-9, 4e-9):
                    Play(q[0], QiPulse(var1))

        test_fr._build_program()
        sequencer = test_fr.cell_seq_dict[test_fr.cells[0]]

        # var2 containing everything
        entry = sequencer._for_range_list[0]

        self.assertEqual(entry.end_addr, 17)
        # #0 var3 = 0 #1 var2 = 5, #2 branch, #3 trigger, #4 wait_trigger,
        # unroll var1==1:  #5 var1=1, #6 trigger #7 stop_trigger
        # inner loop:   #8 start_val, #9 end_val, 10# branch, 11# trigger, 12# wait_trigger, #13 stop_trigger, #14 add_var, #15 jump
        # finish outer : #16 add_var, #17 jump
        self.assertEqual(entry.start, 5)
        self.assertEqual(entry.end, 0)
        self.assertEqual(entry.step, -1)
        self.assertEqual(entry.reg_addr, sequencer.get_var_register(var2).adr)
        self.assertEqual(entry.iterations, 5)
        self.assertEqual(entry.aggregate_iterations, 25)

        entry = sequencer._for_range_list[0].contained_entries[0]

        self.assertEqual(entry.end_addr, 7)
        # unroll var1==1:  #5 var1=1, #6 trigger #7 stop_trigger
        self.assertEqual(entry.start, 1)
        self.assertEqual(entry.end, 2)
        self.assertEqual(entry.step, 1)
        self.assertEqual(entry.reg_addr, sequencer.get_var_register(var1).adr)
        self.assertEqual(entry.iterations, 1)
        self.assertEqual(entry.aggregate_iterations, 1)

        entry = sequencer._for_range_list[0].contained_entries[1]

        self.assertEqual(entry.end_addr, 15)
        # inner loop:   #8 start_val, #9 end_val, 10# branch, 11# trigger, 12# wait_trigger, #13 stop_trigger, #14 add_var, #15 jump
        self.assertEqual(entry.start, 2)
        self.assertEqual(entry.end, 6)
        self.assertEqual(entry.step, 1)
        self.assertEqual(entry.reg_addr, sequencer.get_var_register(var1).adr)
        self.assertEqual(entry.iterations, 4)
        self.assertEqual(entry.aggregate_iterations, 4)

    def test_nested_for_range_var_end_2(self):
        with QiJob(skip_nco_sync=True) as test_fr:
            q = QiCells(1)
            var1 = QiTimeVariable()
            var2 = QiTimeVariable()

            with ForRange(var2, 0, 24e-9, 4e-9):
                with ForRange(var1, 0, var2, 4e-9):
                    Play(q[0], QiPulse(var1))
                    Wait(q[0], 4e-9)

        test_fr._build_program()
        sequencer = test_fr.cell_seq_dict[test_fr.cells[0]]

        entry = sequencer._for_range_list[0]

        self.assertEqual(entry.end_addr, 0)
        # #0 var2 = 4e-9
        self.assertEqual(entry.start, 0)
        self.assertEqual(entry.end, 1)
        self.assertEqual(entry.step, 1)
        self.assertEqual(entry.reg_addr, sequencer.get_var_register(var2).adr)
        self.assertEqual(entry.iterations, 1)
        self.assertEqual(entry.aggregate_iterations, 1)

        entry = sequencer._for_range_list[1]

        self.assertEqual(entry.end_addr, 3)
        self.assertEqual(entry.start, 1)
        self.assertEqual(entry.end, 2)
        self.assertEqual(entry.step, 1)
        self.assertEqual(entry.reg_addr, sequencer.get_var_register(var2).adr)
        self.assertEqual(entry.iterations, 1)
        self.assertEqual(entry.aggregate_iterations, 1)

        entry = sequencer._for_range_list[2]

        self.assertEqual(entry.end_addr, 22)
        self.assertEqual(entry.start, 2)
        self.assertEqual(entry.end, 6)
        self.assertEqual(entry.step, 1)
        self.assertEqual(entry.reg_addr, sequencer.get_var_register(var2).adr)
        self.assertEqual(entry.iterations, 4)
        self.assertEqual(entry.aggregate_iterations, 24)


class ProgBuilderFunctionTest(unittest.TestCase):
    def setUp(self) -> None:
        job = QiJob()
        _set_job_reference(job)

    def tearDown(self) -> None:
        _delete_job_reference()
        return super().tearDown()

    def test_get_for_range_val_invalid(self):
        # If variables have different values at relevant cells, return None
        cell0 = QiCell(0)
        cell1 = QiCell(1)
        seq0 = Sequencer()
        seq1 = Sequencer()
        var = QiVariable(int)

        seq0.add_variable(var)
        seq0.set_variable_value(var, 1)
        seq1.add_variable(var)
        seq1.set_variable_value(var, 2)
        pb = ProgramBuilderVisitor({cell0: seq0, cell1: seq1}, [0, 1])

        self.assertEqual(None, pb.get_var_value_on_seq(var, [cell0, cell1]))


class ProgBuilderVariableMapTest(unittest.TestCase):
    def setUp(self) -> None:
        with QiJob() as self.job:
            self.cells = QiCells(2)
            self.delay = QiTimeVariable(name="delay")
            self.x = QiVariable(int, name="x")
            self.y = QiVariable(int, name="y")
            with ForRange(self.x, 0, 10):
                Wait(self.cells[0], 100e-9)
                Wait(self.cells[1], 100e-9)
            with If(self.delay == 0):
                Play(self.cells[0], QiPulse(100e-9))
            with Else():
                Wait(self.cells[0], self.delay)
        self.job._build_program()

    def test_variable_extraction(self):
        self.assertIn(self.delay, self.job._var_reg_map)
        self.assertIn(self.x, self.job._var_reg_map)
        self.assertNotIn(self.y, self.job._var_reg_map)

        self.assertIn(self.cells[0], self.job._var_reg_map[self.delay])
        self.assertNotIn(self.cells[1], self.job._var_reg_map[self.delay])

        self.assertIn(self.cells[0], self.job._var_reg_map[self.x])
        self.assertIn(self.cells[1], self.job._var_reg_map[self.x])

        # Should have different register indices
        self.assertNotEqual(
            self.job._var_reg_map[self.delay][self.cells[0]],
            self.job._var_reg_map[self.x][self.cells[0]],
        )


class InlineASMTest(unittest.TestCase):
    def test_single_insert(self):
        wait_instr = SeqWaitImm(10)

        with QiJob() as job:
            cells = QiCells(1)
            ASM(cells[0], wait_instr)

        job._build_program()

        instructions = job.cell_seq_dict[cells[0]].instruction_list

        self.assertEqual(instructions[1], wait_instr)

    def test_multiple_insert(self):
        wait_instr = SeqWaitImm(10)
        store_instr = SeqStore(3, 4)
        load_instr = SeqLoad(5, 4)

        with QiJob() as job:
            cells = QiCells(1)
            ASM(cells[0], wait_instr)
            ASM(cells[0], store_instr)
            ASM(cells[0], load_instr)

        job._build_program()

        instructions = job.cell_seq_dict[cells[0]].instruction_list

        self.assertEqual(instructions[1], wait_instr)
        self.assertEqual(instructions[2], store_instr)
        self.assertEqual(instructions[3], load_instr)

    def test_multiple_cells(self):
        instr = SeqWaitImm(123)
        with QiJob() as job:
            cells = QiCells(3)

            ASM(cells[0], instr)
            ASM(cells[2], instr)

            job._build_program()

            self.assertEqual(job.cell_seq_dict[cells[0]].instruction_list[1], instr)
            self.assertEqual(job.cell_seq_dict[cells[2]].instruction_list[1], instr)


class RecordingOffsetTest(unittest.TestCase):
    def test_constant_rec_offset(self):
        with QiJob() as job:
            cells = QiCells(1)

            Recording(cells[0], 20e-9, offset=8e-9)

            Recording(cells[0], 20e-9, offset=16e-9)

        job._build_program()

        instructions = job.cell_seq_dict[cells[0]].instruction_list

        self.assertIsInstance(instructions[0], SeqTrigger)

        self.assertIsInstance(instructions[1], SeqRegImmediateInst)
        self.assertEqual(instructions[1].immediate, util.conv_time_to_cycles(8e-9))
        self.assertIsInstance(instructions[2], SeqLoadUpperImm)
        self.assertIsInstance(instructions[3], SeqRegImmediateInst)
        self.assertIsInstance(instructions[4], SeqStore)

        self.assertIsInstance(instructions[5], SeqTrigger)
        self.assertIsInstance(instructions[6], SeqWaitImm)
        self.assertIsInstance(instructions[7], SeqRegImmediateInst)
        self.assertEqual(instructions[7].immediate, util.conv_time_to_cycles(16e-9))
        self.assertIsInstance(instructions[8], SeqLoadUpperImm)
        self.assertIsInstance(instructions[9], SeqRegImmediateInst)
        self.assertIsInstance(instructions[10], SeqStore)
        self.assertIsInstance(instructions[11], SeqTrigger)
        self.assertIsInstance(instructions[12], SeqWaitImm)

    def test_variable_rec_offset(self):
        with QiJob() as job:
            cells = QiCells(1)

            a = QiVariable(name="A", value=16e-9)

            Recording(cells[0], 20e-9, a)

        job._build_program()

        instructions = job.cell_seq_dict[cells[0]].instruction_list

        self.assertIsInstance(instructions[0], SeqTrigger)
        self.assertIsInstance(instructions[1], SeqRegImmediateInst)
        self.assertIsInstance(instructions[2], SeqLoadUpperImm)
        self.assertIsInstance(instructions[3], SeqRegImmediateInst)
        self.assertIsInstance(instructions[4], SeqStore)
        self.assertEqual(instructions[4].src_reg, instructions[1].dst_reg)
        self.assertIsInstance(instructions[5], SeqTrigger)
