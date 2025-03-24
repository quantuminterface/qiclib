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
import pytest

from qiclib.code.analysis.qi_insert_mem_parameters import (
    MANIPULATION_PULSE_FREQUENCY_ADDRESS,
    READOUT_PULSE_FREQUENCY_ADDRESS,
    replace_variable_assignment_with_store_commands,
)
from qiclib.code.qi_command import (
    DeclareCommand,
    ForRangeCommand,
    IfCommand,
    MemStoreCommand,
    PlayCommand,
    PlayReadoutCommand,
    RecordingCommand,
)
from qiclib.code.qi_jobs import (
    Assign,
    Else,
    ForRange,
    If,
    Parallel,
    Play,
    PlayReadout,
    QiAmplitudeVariable,
    QiCells,
    QiJob,
    QiPhaseVariable,
    QiTimeVariable,
    QiVariable,
    Recording,
    Wait,
)
from qiclib.code.qi_pulse import QiPulse


class TestRecordingOffsetInsertion:
    def test_somewhat_complex_example(self):
        with QiJob() as job:
            cells = QiCells(2)

            # MemStoreCommand(cell[1], 4.0)
            # MemStoreCommand(cell[0], 2.0)
            x = QiVariable(name="X")
            Recording(cells[0], 20e-9, offset=2.0)

            # MemStoreCommand(cell[0], 4.0)
            with If(x == 12):
                Recording(cells[1], 20e-9, offset=2.0)
            with Else():
                Assign(x, 6)

            Recording(cells[0], 20e-9, offset=4.0)
            t = QiVariable(name="T")
            with ForRange(t, 0, 100e-9, 8e-9):
                # MemStoreCommand(cell[0], t)
                Recording(cells[0], 20e-9, offset=t)

                # MemStoreCommand(cell[0], 6.0)

                with ForRange(t, 0, 100e-9, 8e-9):
                    Recording(cells[0], 20e-9, offset=6.0)

        replace_variable_assignment_with_store_commands(job)

        assert cells[1].initial_recording_offset == 2.0

        assert isinstance(job.commands[0], MemStoreCommand)
        assert job.commands[0].value.float_value == 2.0

        assert isinstance(job.commands[3], MemStoreCommand)
        assert job.commands[3].value.float_value == 4.0

        assert isinstance(job.commands[7], ForRangeCommand)
        assert isinstance(job.commands[7].body[0], MemStoreCommand)
        assert job.commands[7].body[0].value is t

        assert isinstance(job.commands[7].body[2], MemStoreCommand)
        assert job.commands[7].body[2].value.float_value == 6.0

    def test_other_somewhat_complex_example(self):
        # This test demonstrates some flaws in the current implementation.
        # The first store command could be placed before the loop, but because
        # the pseudo instruction heuristic checks if all uses of a memory parameter
        # in a loop use the same value it won't do it in this case.
        # If we were the check the anticipated value at the start, and the available
        # value at the end of a loop we could detect this.
        # But because we need the pseudo instructions before we start the anticipated
        # analysis of the entire program we have this circular dependency.
        # We could first analyse all loops, going from inner to outer loops,
        # then use this information to insert all pseudo instructions.
        # But because qicode programs tend to not be control flow heavy this is deemed
        # not necessary right now because it would significantly increase the complexity
        # of the algorithm, with questionable gain in performance.
        with QiJob() as job:
            cells = QiCells(2)

            a = QiTimeVariable(name="A", value=2.0)
            b = QiTimeVariable(name="B", value=4)

            with ForRange(b, 0, 100e-9):
                # MemStoreCommand(cell[0], a)

                Recording(cells[0], 1, offset=a)

                with If(a == 4):
                    # MemStoreCommand(cell[0], 0.0)
                    Recording(cells[0], 1, offset=0)
                    # MemStoreCommand(cell[0], a)

                with ForRange(b, 0, 100e-9):
                    Recording(cells[0], 1, offset=a)

            # MemStoreCommand(cells[0], 24e-9)
            Recording(cells[0], 1, offset=24e-9)

        replace_variable_assignment_with_store_commands(job)

        print(job)

        assert cells[0].initial_recording_offset == 0.0

        assert isinstance(job.commands[4], ForRangeCommand)
        assert isinstance(job.commands[4].body[0], MemStoreCommand)
        assert isinstance(job.commands[4].body[2], IfCommand)

        if_cmd = job.commands[4].body[2]

        assert isinstance(if_cmd.body[0], MemStoreCommand)
        assert if_cmd.body[0].value.float_value == 0.0
        assert isinstance(if_cmd.body[2], MemStoreCommand)
        assert if_cmd.body[2].value is a

        assert isinstance(job.commands[5], MemStoreCommand)
        assert job.commands[5].value.float_value == 24e-9

    def test_store_instruction_in_if_body(self):
        # TODO: We probably want to improve this by inserting
        # only one store after the if.
        # Right now we insert them as early as possible thereby
        # causing unecessary duplicates as shown in this test.

        with QiJob() as job:
            cells = QiCells(2)

            a = QiTimeVariable(name="A", value=2.0)
            _b = QiVariable(name="B", value=4)

            with If(a == 4):
                # MemStoreCommand(cells[0], 8e-9)
                pass
            with Else():
                # MemStoreCommand(cells[0], 0.0)
                Recording(cells[0], 1, offset=0)
                # MemStoreCommand(cells[0], 8e-9)

            Recording(cells[0], 1, offset=8e-9)

        replace_variable_assignment_with_store_commands(job)

        assert isinstance(job.commands[4], IfCommand)
        if_cmd = job.commands[4]

        assert isinstance(if_cmd.body[0], MemStoreCommand)
        assert if_cmd.body[0].value.float_value == 8e-9

        assert isinstance(if_cmd._else_body[0], MemStoreCommand)
        assert if_cmd._else_body[0].value.float_value == 0.0
        assert isinstance(if_cmd._else_body[2], MemStoreCommand)
        assert if_cmd._else_body[2].value.float_value == 8e-9

    def test_store_instruction_in_else(self):
        # TODO: We probably want to improve this by inserting
        # only one store after the if.
        # Right now we insert them as early as possible thereby
        # causing unecessary duplicates as shown in this test.

        with QiJob() as job:
            cells = QiCells(2)

            a = QiTimeVariable(name="A", value=2.0)
            _b = QiVariable(name="B", value=4)

            with If(a == 4) as i:
                Recording(cells[0], 1, offset=0)

            Recording(cells[0], 1, offset=8e-9)

        replace_variable_assignment_with_store_commands(job)
        assert isinstance(i.body[0], MemStoreCommand)
        assert isinstance(i.body[2], MemStoreCommand)
        assert isinstance(i._else_body[0], MemStoreCommand)

    def test_insert_store_after_var_decl(self):
        with QiJob() as job:
            cells = QiCells(2)

            a = QiVariable(name="A")

            with ForRange(QiTimeVariable(), 0, 100e-9):
                Recording(cells[0], 1, offset=a)

        replace_variable_assignment_with_store_commands(job)
        print(job)

        cmd = job.commands[1]
        assert isinstance(cmd, MemStoreCommand)
        assert cmd.value == a

    def test_initial_recording_offset(self):
        with QiJob() as job:
            cells = QiCells(2)

            _a = QiTimeVariable(name="A", value=2.0)

            Recording(cells[0], 1, offset=4e-9)

        replace_variable_assignment_with_store_commands(job)
        assert cells[0].initial_recording_offset == 4e-9
        assert len(job.commands) == 3

    def test_move_before_loop(self):
        with QiJob() as job:
            cells = QiCells(1)

            # MemStoreCommand(20e-9)

            Recording(cells[0], 12e-9, 20e-9)

            # MemStoreCommand(40e-9)

            a = QiTimeVariable(name="A")

            with ForRange(a, 0, 100e-9):
                Recording(cells[0], 12e-9, 40e-9)

        replace_variable_assignment_with_store_commands(job)

        assert isinstance(job.commands[0], MemStoreCommand)
        assert job.commands[0].value.float_value == 20e-9

        assert isinstance(job.commands[1], RecordingCommand)

        assert isinstance(job.commands[2], MemStoreCommand)
        assert job.commands[2].value.float_value == 40e-9

        assert isinstance(job.commands[3], DeclareCommand)

    def test_invariant_expression_in_loop(self):
        with QiJob() as job:
            cells = QiCells(1)

            a = QiTimeVariable(name="A")

            b = QiTimeVariable(name="B")
            # MemStoreCommand(offset)

            with ForRange(a, 0, 100e-9):
                offset = b + 1
                Recording(cells[0], 12e-9, offset=offset)

        replace_variable_assignment_with_store_commands(job)

        print(job)

        assert isinstance(job.commands[2], MemStoreCommand)
        assert job.commands[2].value is offset

        assert isinstance(job.commands[3], ForRangeCommand)
        assert isinstance(job.commands[3].body[0], RecordingCommand)
        assert len(job.commands[3].body) == 1

    def test_not_invariant_expression_in_loop(self):
        with QiJob() as job:
            cells = QiCells(1)

            a = QiTimeVariable(name="A")

            b = QiTimeVariable(name="B")
            # MemStoreCommand(offset)

            with ForRange(a, 0, 100e-9):
                offset = b + 1
                Recording(cells[0], 12e-9, offset=offset)

                with If(a == 20e-9):
                    Assign(b, 5)
                    # MemStoreCommand(offset)

        replace_variable_assignment_with_store_commands(job)

        print(job)

        assert isinstance(job.commands[2], MemStoreCommand)
        assert job.commands[2].value is offset

        assert isinstance(job.commands[3], ForRangeCommand)
        assert isinstance(job.commands[3].body[0], RecordingCommand)
        assert isinstance(job.commands[3].body[1], IfCommand)
        assert isinstance(job.commands[3].body[1].body[1], MemStoreCommand)
        assert job.commands[3].body[1].body[1].value is offset

    def test_multiple_cells(self):
        with QiJob() as job:
            cells = QiCells(3)

            a = QiTimeVariable(name="A")

            b = QiTimeVariable(name="B")

            with ForRange(a, 0, 100e-9):
                offset_cell_1 = a + 1
                offset_cell_2 = b + 1

                with If(a == 20e-9):
                    # MemStoreCommand(cell1, offset_cell_1)
                    Assign(b, 5)
                    # MemStoreCommand(cell2, offset_cell_2)
                    Recording(cells[1], 12e-9, offset=offset_cell_1)
                # with Else():
                #   MemStoreCommand(cell2, offset_cell_2)

                Recording(cells[2], 12e-9, offset=offset_cell_2)
                Recording(cells[0], 12e-9, offset=20e-9)

        replace_variable_assignment_with_store_commands(job)

        assert cells[0].initial_recording_offset == 20e-9

        assert isinstance(job.commands[2], ForRangeCommand)
        assert isinstance(job.commands[2].body[0], IfCommand)

        if_cmd = job.commands[2].body[0]

        assert isinstance(if_cmd.body[0], MemStoreCommand)
        assert if_cmd.body[0]._relevant_cells == {cells[1]}
        assert if_cmd.body[0].value is offset_cell_1

        assert isinstance(if_cmd.body[2], MemStoreCommand)
        assert if_cmd.body[2]._relevant_cells == {cells[2]}
        assert if_cmd.body[2].value is offset_cell_2

        assert if_cmd.is_followed_by_else()
        assert isinstance(if_cmd._else_body[0], MemStoreCommand)
        assert if_cmd._else_body[0].value is offset_cell_2
        assert if_cmd._else_body[0]._relevant_cells == {cells[2]}

    def test_play_readout(self):
        with QiJob() as job:
            cells = QiCells(1)
            # MemStoreCommand(12e-9)

            Recording(cells[0], 20e-9, 12e-9)

            # MemStoreCommand(40e-9)

            PlayReadout(cells[0], QiPulse(40e-9))
            Recording(cells[0], 20e-9, 16e-9)

        replace_variable_assignment_with_store_commands(job)

        assert isinstance(job.commands[0], MemStoreCommand)
        assert job.commands[0].value.float_value == 12e-9

        assert isinstance(job.commands[2], MemStoreCommand)
        assert job.commands[2].value.float_value == 16e-9

    def test_different_offsets_in_parallel_blocks_not_allowed(self):
        with QiJob() as job:
            cells = QiCells(1)

            with Parallel():
                Recording(cells[0], 12e-9, 10e-9)
            with Parallel():
                Wait(cells[0], 20e-9)
                Recording(cells[0], 12e-9, 8e-9)

        with pytest.raises(
            RuntimeError,
            match="Parallel Blocks with multiple Recording instructions with different offsets are not supported.",
        ):
            replace_variable_assignment_with_store_commands(job)

    def test_parallel_blocks(self):
        with QiJob() as job:
            cells = QiCells(1)

            # MemStoreCommand(12e-9)
            Recording(cells[0], 12e-9, 12e-9)

            # MemStoreCommand(16e-9)
            with Parallel():
                Recording(cells[0], 12e-9, 16e-9)

        replace_variable_assignment_with_store_commands(job)

        assert isinstance(job.commands[0], MemStoreCommand)
        assert job.commands[0].value.float_value == 12e-9

        assert isinstance(job.commands[2], MemStoreCommand)
        assert job.commands[2].value.float_value == 16e-9

    def test_multiple_recording_in_sequence(self):
        with QiJob() as job:
            cells = QiCells(1)

            # MemStoreCommand(cells[0], 8e-9)
            Recording(cells[0], 8e-9, 8e-9)
            Recording(cells[0], 8e-9, 8e-9)

            # MemStoreCommand(cells[0], 12e-9)
            Recording(cells[0], 8e-9, 12e-9)

            # MemStoreCommand(cells[0], 16e-9)
            Recording(cells[0], 8e-9, 16e-9)

        replace_variable_assignment_with_store_commands(job)

        assert isinstance(job.commands[0], MemStoreCommand)
        assert job.commands[0].value.float_value == 8e-9

        assert isinstance(job.commands[3], MemStoreCommand)
        assert job.commands[3].value.float_value == 12e-9

        assert isinstance(job.commands[5], MemStoreCommand)
        assert job.commands[5].value.float_value == 16e-9

    def test_nested_loops(self):
        with QiJob() as job:
            cells = QiCells(1)

            a = QiTimeVariable(name="A")

            with ForRange(a, 0, 100e-9):
                # MemStoreCommand
                with ForRange(QiVariable(), 0, 100):
                    with ForRange(QiVariable(), 0, 100):
                        Recording(cells[0], 8e-9, a)

        replace_variable_assignment_with_store_commands(job)

        assert isinstance(job.commands[1].body[0], MemStoreCommand)
        assert job.commands[1].body[0].value is a

    def test_qi_cell_property_recording_offset(self):
        with QiJob() as job:
            cells = QiCells(1)

            _cell_prop_1 = cells[0]["first_rec_offset"]
            cell_prop_2 = cells[0]["second_rec_offset"]
            cell_prop_3 = cells[0]["third_rec_offset"]

            # MemStoreCommand(cells[0], cells[0]["second_rec_offset"])

            with ForRange(QiTimeVariable(), 0, 100e-9):
                Recording(cells[0], 20e-9, cell_prop_2)

            # MemStoreCommand(cells[0], cells[0]["third_rec_offset"]) // the factor of two is folded into the QiCellProperty

            Recording(cells[0], 20e-9, cell_prop_3 * 2)

        replace_variable_assignment_with_store_commands(job)

        print(job)

        assert isinstance(job.commands[0], MemStoreCommand)
        assert job.commands[0].value is cell_prop_2

        assert isinstance(job.commands[3], MemStoreCommand)
        assert job.commands[3].value is cell_prop_3


class TestPlayFrequency:
    def test_simple_play(self):
        with QiJob() as job:
            cells = QiCells(1)

            # MemStoreCommand
            Play(cells[0], QiPulse(20e-9, frequency=10))
            # MemStoreCommand
            Play(cells[0], QiPulse(20e-9, frequency=20))

        replace_variable_assignment_with_store_commands(job)

        assert isinstance(job.commands[0], MemStoreCommand)
        assert job.commands[0].addr == MANIPULATION_PULSE_FREQUENCY_ADDRESS
        assert job.commands[0].value == 10

        assert isinstance(job.commands[1], PlayCommand)

        assert isinstance(job.commands[2], MemStoreCommand)
        assert job.commands[2].addr == MANIPULATION_PULSE_FREQUENCY_ADDRESS
        assert job.commands[2].value == 10

        assert isinstance(job.commands[3], PlayCommand)

    def test_keep_frequency(self):
        with QiJob() as job:
            cells = QiCells(1)

            # MemStoreCommand
            Play(cells[0], QiPulse(20e-9, frequency=10))

            Play(cells[0], QiPulse(20e-9))
            # MemStoreCommand
            Play(cells[0], QiPulse(20e-9, frequency=20))

            replace_variable_assignment_with_store_commands(job)

            assert isinstance(job.commands[0], MemStoreCommand)
            assert job.commands[0].value == 10

            assert isinstance(job.commands[1], PlayCommand)

            assert isinstance(job.commands[2], PlayCommand)

            assert isinstance(job.commands[3], MemStoreCommand)
            assert job.commands[3].value == 10

            assert isinstance(job.commands[4], PlayCommand)

    def test_readout_frequency(self):
        with QiJob() as job:
            cells = QiCells(1)

            # MemStoreCommand
            PlayReadout(cells[0], QiPulse(20e-9, frequency=10))
            # MemStoreCommand
            PlayReadout(cells[0], QiPulse(20e-9, frequency=20))

        replace_variable_assignment_with_store_commands(job)

        assert isinstance(job.commands[0], MemStoreCommand)
        assert job.commands[0].addr == READOUT_PULSE_FREQUENCY_ADDRESS
        assert job.commands[0].value == 10

        assert isinstance(job.commands[1], PlayReadoutCommand)

        assert isinstance(job.commands[2], MemStoreCommand)
        assert job.commands[2].addr == READOUT_PULSE_FREQUENCY_ADDRESS
        assert job.commands[2].value == 10

        assert isinstance(job.commands[3], PlayReadoutCommand)

    def test_initial_manip_frequency(self):
        with QiJob() as job:
            cells = QiCells(1)

            Play(cells[0], QiPulse(20e-9, frequency=10))

        replace_variable_assignment_with_store_commands(job)

        assert cells[0].initial_manipulation_frequency == 10

    def test_initial_readout_frequency(self):
        with QiJob() as job:
            cells = QiCells(1)

            PlayReadout(cells[0], QiPulse(20e-9, frequency=10))

        replace_variable_assignment_with_store_commands(job)

        assert cells[0].initial_readout_frequency == 10

    def test_manip_and_readout_frequencies_combined(self):
        with QiJob() as job:
            cells = QiCells(1)

            # MemStoreCommand for PlayReadout
            # MemStoreCommand for Play

            Play(cells[0], QiPulse(20e-9, frequency=10))

            # MemStoreCommand for Play

            PlayReadout(cells[0], QiPulse(20e-9, frequency=10))

            Play(cells[0], QiPulse(20e-9, frequency=20))

            # MemStoreCommand for Play

            PlayReadout(cells[0], QiPulse(20e-9, frequency=10))

            # MemStoreCommand for PlayReadout

            Play(cells[0], QiPulse(20e-9, frequency=30))

            PlayReadout(cells[0], QiPulse(20e-9, frequency=20))

        job._build_program()

        assert isinstance(job.commands[0], MemStoreCommand)
        assert job.commands[0].value == 10
        assert job.commands[0].addr == READOUT_PULSE_FREQUENCY_ADDRESS

        assert isinstance(job.commands[1], MemStoreCommand)
        assert job.commands[1].value == 10
        assert job.commands[1].addr == MANIPULATION_PULSE_FREQUENCY_ADDRESS

        assert isinstance(job.commands[2], PlayCommand)

        assert isinstance(job.commands[3], MemStoreCommand)
        assert job.commands[3].value == 20
        assert job.commands[3].addr == MANIPULATION_PULSE_FREQUENCY_ADDRESS

        assert isinstance(job.commands[4], PlayReadoutCommand)

        assert isinstance(job.commands[5], PlayCommand)

        assert isinstance(job.commands[6], MemStoreCommand)
        assert job.commands[6].value == 60
        assert job.commands[6].addr == MANIPULATION_PULSE_FREQUENCY_ADDRESS

        assert isinstance(job.commands[7], PlayReadoutCommand)

        assert isinstance(job.commands[8], MemStoreCommand)
        assert job.commands[8].value == 20
        assert job.commands[8].addr == READOUT_PULSE_FREQUENCY_ADDRESS

        assert isinstance(job.commands[9], PlayCommand)

        assert isinstance(job.commands[10], PlayReadoutCommand)

    def test_variable_manipulation_frequency(self):
        with QiJob() as job:
            cells = QiCells(1)

            x = QiVariable(name="X")

            with ForRange(x, 0, 100):
                Play(cells[0], QiPulse(20e-9, frequency=x))

        job._build_program()

        assert isinstance(job.commands[1], ForRangeCommand)
        assert isinstance(job.commands[1].body[0], MemStoreCommand)
        assert job.commands[1].body[0].addr == MANIPULATION_PULSE_FREQUENCY_ADDRESS
        assert job.commands[1].body[0].value is x

        assert isinstance(job.commands[1].body[1], PlayCommand)

    def test_command_with_no_manipulation_frequency(self):
        with QiJob() as job:
            cells = QiCells(1)

            # MemStoreCommand
            Play(cells[0], QiPulse(20e-9, frequency=12e3))
            Play(cells[0], QiPulse(20e-9))  # inherits frequency from prev command.

            # MemStoreCommand
            Play(cells[0], QiPulse(20e-9, frequency=24e3))

        job._build_program()

        assert isinstance(job.commands[0], MemStoreCommand)
        assert job.commands[0].value.float_value == 12e3
        assert job.commands[0].addr == MANIPULATION_PULSE_FREQUENCY_ADDRESS

        assert isinstance(job.commands[1], PlayCommand)

        assert isinstance(job.commands[2], PlayCommand)

        assert isinstance(job.commands[3], MemStoreCommand)
        assert job.commands[3].value.float_value == 24e3
        assert job.commands[3].addr == MANIPULATION_PULSE_FREQUENCY_ADDRESS

        assert isinstance(job.commands[4], PlayCommand)

    def test_command_with_no_readout_frequency(self):
        with QiJob() as job:
            cells = QiCells(1)

            # MemStoreCommand
            PlayReadout(cells[0], QiPulse(20e-9, frequency=12e3))
            PlayReadout(
                cells[0], QiPulse(20e-9)
            )  # inherits frequency from prev command.

            # MemStoreCommand
            PlayReadout(cells[0], QiPulse(20e-9, frequency=24e3))

        job._build_program()

        assert isinstance(job.commands[0], MemStoreCommand)
        assert job.commands[0].value.float_value == 12e3
        assert job.commands[0].addr == READOUT_PULSE_FREQUENCY_ADDRESS

        assert isinstance(job.commands[1], PlayReadoutCommand)

        assert isinstance(job.commands[2], PlayReadoutCommand)

        assert isinstance(job.commands[3], MemStoreCommand)
        assert job.commands[3].value.float_value == 24e3
        assert job.commands[3].addr == READOUT_PULSE_FREQUENCY_ADDRESS

        assert isinstance(job.commands[4], PlayReadoutCommand)

    def test_integer_pseudo_vna(self):
        with QiJob() as pseudo_vna:
            q = QiCells(1)
            fr = QiVariable()
            with ForRange(fr, 0, 100000000, 100000):
                PlayReadout(q[0], QiPulse(416e-9, frequency=fr))
                Recording(q[0], 400e-9, 280e-9, save_to="result")
                Wait(q[0], 2e-6)

        pseudo_vna._build_program()

        assert isinstance(pseudo_vna.commands[1], ForRangeCommand)

        assert isinstance(pseudo_vna.commands[1].body[0], MemStoreCommand)
        assert pseudo_vna.commands[1].body[0].value == fr

        assert len(pseudo_vna.cell_seq_dict[q[0]].instruction_list) > 20

    def test_float_pseudo_vna(self):
        with QiJob() as pseudo_vna:
            q = QiCells(1)
            fr = QiVariable()
            with ForRange(fr, 0, 100e6, 0.1e6):
                PlayReadout(q[0], QiPulse(416e-9, frequency=fr))
                Recording(q[0], 400e-9, 280e-9, save_to="result")
                Wait(q[0], 2e-6)

        pseudo_vna._build_program()

        assert isinstance(pseudo_vna.commands[1], ForRangeCommand)

        assert isinstance(pseudo_vna.commands[1].body[0], MemStoreCommand)
        assert pseudo_vna.commands[1].body[0].value == fr

        assert len(pseudo_vna.cell_seq_dict[q[0]].instruction_list) > 20

    def test_preserve_frequency(self):
        # This tests ensures that programs with empty Memory Parameters (like the second Play command here)
        # still can have a constant memory parameter and therefore don't insert a store command in the beginning.

        with QiJob() as job:
            q = QiCells(1)
            Play(q[0], QiPulse(100e-9, frequency=100e6))
            Play(q[0], QiPulse(200e-9))

        job._build_program()
        assert isinstance(job.commands[0], PlayCommand)
        assert isinstance(job.commands[1], PlayCommand)

    def test_variable_manipulation_amplitude(self):
        with QiJob() as job:
            q = QiCells(1)
            a = QiAmplitudeVariable()
            with ForRange(a, 0.0, 1.0, 0.1):
                Play(q[0], QiPulse(length=100e-9, amplitude=a))
        assert job.get_assembly() == [
            "tr 0x0, 0x0, 0x0, 0x0, 0x0, 0x0",
            # Initialize r2 to int16 max
            "lui r2, 32768",
            "addi r2, r2, 0xfff",
            # Intialize r1 to 0
            "addi r1, r0, 0x0",
            # Main loop: branch if greater or equal
            "bge r1, r2, 0xc",
            # r3 := shift r1 left by 16
            "sll r3, r1, 0x10",
            # r4 := r1 | r3
            "or r4, r1, r3",
            # Load address
            "lui r3, 24576",
            "addi r3, r3, 0x4",
            # Store r4 @ r3
            "sw r4, 0(r3)",
            # trigger + wait (play pulse)
            "tr 0x0, 0x0, 0x1, 0x0, 0x0, 0x0",
            "wti 0x18",
            # Increase r1 by r3
            "lui r3, 4096",
            "addi r3, r3, 0xccc",
            "add r1, r1, r3",
            "j -0xb",
            "end",
        ]

    def test_variable_readout_amplitude(self):
        with QiJob() as job:
            q = QiCells(1)
            a = QiAmplitudeVariable()
            with ForRange(a, 0.0, 1.0, 0.1):
                PlayReadout(q[0], QiPulse(length=100e-9, amplitude=a))
        assert job.get_assembly() == [
            "tr 0x0, 0x0, 0x0, 0x0, 0x0, 0x0",
            # Initialize r2 to int16 max
            "lui r2, 32768",
            "addi r2, r2, 0xfff",
            # Intialize r1 to 0
            "addi r1, r0, 0x0",
            # Main loop: branch if greater or equal
            "bge r1, r2, 0xc",
            # r3 := shift r1 left by 16
            "sll r3, r1, 0x10",
            # r4 := r1 | r3
            "or r4, r1, r3",
            # Load address
            "lui r3, 57344",
            "addi r3, r3, 0x4",
            # Store r4 @ r3
            "sw r4, 0(r3)",
            # trigger + wait (play pulse)
            "tr 0x1, 0x0, 0x0, 0x0, 0x0, 0x0",
            "wti 0x18",
            # Increase r1 by r3
            "lui r3, 4096",
            "addi r3, r3, 0xccc",
            "add r1, r1, r3",
            "j -0xb",
            "end",
        ]

    def test_variable_manipulation_phase(self):
        with QiJob() as job:
            q = QiCells(1)
            p = QiPhaseVariable()
            with ForRange(p, 0.0, 6, 1):
                Play(q[0], QiPulse(length=100e-9, phase=p))
        assert job.get_assembly() == [
            "tr 0x0, 0x0, 0x0, 0x0, 0x0, 0x0",
            # Initialize r2 to int16 max
            "lui r2, 61440",
            "addi r2, r2, 0x476",
            # Intialize r1 to 0
            "addi r1, r0, 0x0",
            # Main loop: branch if greater or equal
            "bge r1, r2, 0xa",
            # Load address
            "lui r3, 24576",
            "addi r3, r3, 0xc",
            # Store r4 @ r3
            "sw r1, 0(r3)",
            # trigger + wait (play pulse)
            "tr 0x0, 0x0, 0x1, 0x0, 0x0, 0x0",
            "wti 0x18",
            "lui r3, 12288",
            "addi r3, r3, 0x8be",
            "add r1, r1, r3",
            "j -0x9",
            "end",
        ]

    def test_variable_readout_phase(self):
        with QiJob() as job:
            q = QiCells(1)
            p = QiPhaseVariable()
            with ForRange(p, 0.0, 6, 1):
                PlayReadout(q[0], QiPulse(length=100e-9, phase=p))
        assert job.get_assembly() == [
            "tr 0x0, 0x0, 0x0, 0x0, 0x0, 0x0",
            # Initialize r2 to int16 max
            "lui r2, 61440",
            "addi r2, r2, 0x476",
            # Intialize r1 to 0
            "addi r1, r0, 0x0",
            # Main loop: branch if greater or equal
            "bge r1, r2, 0xa",
            # Load address
            "lui r3, 57344",
            "addi r3, r3, 0xc",
            # Store r4 @ r3
            "sw r1, 0(r3)",
            # trigger + wait (play pulse)
            "tr 0x1, 0x0, 0x0, 0x0, 0x0, 0x0",
            "wti 0x18",
            "lui r3, 12288",
            "addi r3, r3, 0x8be",
            "add r1, r1, r3",
            "j -0x9",
            "end",
        ]
