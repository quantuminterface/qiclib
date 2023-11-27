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

from qiclib.code.analysis.qi_insert_mem_parameters import (
    READOUT_PULSE_FREQUENCY_ADDRESS,
    insert_recording_offset_store_commands,
    insert_manipulation_pulse_frequency_store_commands,
    insert_readout_pulse_frequency_store_commands,
    MANIPULATION_PULSE_FREQUENCY_ADDRESS,
)
import unittest
from qiclib.code.qi_pulse import QiPulse
from qiclib.code.qi_jobs import (
    Assign,
    Else,
    ForRange,
    If,
    Parallel,
    Play,
    PlayReadout,
    QiCells,
    QiJob,
    QiTimeVariable,
    QiVariable,
    Recording,
    Wait,
    cQiDeclare,
    cQiMemStore,
    cQiPlay,
    cQiPlayReadout,
    cQiRecording,
)


class RecordingOffsetInsertionTest(unittest.TestCase):
    def test_somewhat_complex_example(self):
        with QiJob() as job:
            cells = QiCells(2)

            # cQiMemStore(cell[1], 4.0)
            # cQiMemStore(cell[0], 2.0)
            x = QiVariable(name="X")
            Recording(cells[0], 20e-9, offset=2.0)

            # cQiMemStore(cell[0], 4.0)
            with If(x == 12):
                Recording(cells[1], 20e-9, offset=2.0)
            with Else():
                Assign(x, 6)

            Recording(cells[0], 20e-9, offset=4.0)
            t = QiVariable(name="T")
            with ForRange(t, 0, 100e-9, 8e-9):
                # cQiMemStore(cell[0], t)
                Recording(cells[0], 20e-9, offset=t)

                # cQiMemStore(cell[0], 6.0)

                with ForRange(t, 0, 100e-9, 8e-9):
                    Recording(cells[0], 20e-9, offset=6.0)

        insert_recording_offset_store_commands(job)

        self.assertEqual(cells[1].initial_recording_offset, 2.0)

        self.assertIsInstance(job.commands[0], cQiMemStore)
        self.assertEqual(job.commands[0].value.float_value, 2.0)

        self.assertIsInstance(job.commands[3], cQiMemStore)
        self.assertEqual(job.commands[3].value.float_value, 4.0)

        self.assertIsInstance(job.commands[7], ForRange)
        self.assertIsInstance(job.commands[7].body[0], cQiMemStore)
        self.assertIs(job.commands[7].body[0].value, t)

        self.assertIsInstance(job.commands[7].body[2], cQiMemStore)
        self.assertEqual(job.commands[7].body[2].value.float_value, 6.0)

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
                # cQiMemStore(cell[0], a)

                Recording(cells[0], 1, offset=a)

                with If(a == 4):
                    # cQiMemStore(cell[0], 0.0)
                    Recording(cells[0], 1, offset=0)
                    # cQiMemStore(cell[0], a)

                with ForRange(b, 0, 100e-9):
                    Recording(cells[0], 1, offset=a)

            # cQiMemStore(cells[0], 24e-9)
            Recording(cells[0], 1, offset=24e-9)

        insert_recording_offset_store_commands(job)

        print(job)

        self.assertEqual(cells[0].initial_recording_offset, 0.0)

        self.assertIsInstance(job.commands[4], ForRange)
        self.assertIsInstance(job.commands[4].body[0], cQiMemStore)
        self.assertIsInstance(job.commands[4].body[2], If)

        if_cmd = job.commands[4].body[2]

        self.assertIsInstance(if_cmd.body[0], cQiMemStore)
        self.assertEqual(if_cmd.body[0].value.float_value, 0.0)
        self.assertIsInstance(if_cmd.body[2], cQiMemStore)
        self.assertIs(if_cmd.body[2].value, a)

        self.assertIsInstance(job.commands[5], cQiMemStore)
        self.assertEqual(job.commands[5].value.float_value, 24e-9)

    def test_store_instruction_in_if_body(self):
        # TODO: We probably want to improve this by inserting
        # only one store after the if.
        # Right now we insert them as early as possible thereby
        # causing unecessary duplicates as shown in this test.

        with QiJob() as job:
            cells = QiCells(2)

            a = QiTimeVariable(name="A", value=2.0)
            b = QiVariable(name="B", value=4)

            with If(a == 4) as i:
                # cQiMemStore(cells[0], 8e-9)
                pass
            with Else():
                # cQiMemStore(cells[0], 0.0)
                Recording(cells[0], 1, offset=0)
                # cQiMemStore(cells[0], 8e-9)

            Recording(cells[0], 1, offset=8e-9)

        insert_recording_offset_store_commands(job)

        self.assertIsInstance(job.commands[4], If)
        if_cmd = job.commands[4]

        self.assertIsInstance(if_cmd.body[0], cQiMemStore)
        self.assertEqual(if_cmd.body[0].value.float_value, 8e-9)

        self.assertIsInstance(if_cmd._else_body[0], cQiMemStore)
        self.assertEqual(if_cmd._else_body[0].value.float_value, 0.0)
        self.assertIsInstance(if_cmd._else_body[2], cQiMemStore)
        self.assertEqual(if_cmd._else_body[2].value.float_value, 8e-9)

    def test_store_instruction_in_else(self):
        # TODO: We probably want to improve this by inserting
        # only one store after the if.
        # Right now we insert them as early as possible thereby
        # causing unecessary duplicates as shown in this test.

        with QiJob() as job:
            cells = QiCells(2)

            a = QiTimeVariable(name="A", value=2.0)
            b = QiVariable(name="B", value=4)

            with If(a == 4) as i:
                Recording(cells[0], 1, offset=0)

            Recording(cells[0], 1, offset=8e-9)

        insert_recording_offset_store_commands(job)
        self.assertIsInstance(i.body[0], cQiMemStore)
        self.assertIsInstance(i.body[2], cQiMemStore)
        self.assertIsInstance(i._else_body[0], cQiMemStore)

    def test_insert_store_after_var_decl(self):
        with QiJob() as job:
            cells = QiCells(2)

            a = QiVariable(name="A")

            with ForRange(QiTimeVariable(), 0, 100e-9):
                Recording(cells[0], 1, offset=a)

        insert_recording_offset_store_commands(job)
        print(job)

        cmd = job.commands[1]
        self.assertIsInstance(cmd, cQiMemStore)
        self.assertEqual(cmd.value, a)

    def test_initial_recording_offset(self):
        with QiJob() as job:
            cells = QiCells(2)

            a = QiTimeVariable(name="A", value=2.0)

            Recording(cells[0], 1, offset=4e-9)

        insert_recording_offset_store_commands(job)
        self.assertEqual(cells[0].initial_recording_offset, 4e-9)
        self.assertEqual(len(job.commands), 3)

    def test_move_before_loop(self):
        with QiJob() as job:
            cells = QiCells(1)

            # cQiMemStore(20e-9)

            Recording(cells[0], 12e-9, 20e-9)

            # cQiMemStore(40e-9)

            a = QiTimeVariable(name="A")

            with ForRange(a, 0, 100e-9):
                Recording(cells[0], 12e-9, 40e-9)

        insert_recording_offset_store_commands(job)

        self.assertIsInstance(job.commands[0], cQiMemStore)
        self.assertEqual(job.commands[0].value.float_value, 20e-9)

        self.assertIsInstance(job.commands[1], cQiRecording)

        self.assertIsInstance(job.commands[2], cQiMemStore)
        self.assertEqual(job.commands[2].value.float_value, 40e-9)

        self.assertIsInstance(job.commands[3], cQiDeclare)

    def test_invariant_expression_in_loop(self):

        with QiJob() as job:
            cells = QiCells(1)

            a = QiTimeVariable(name="A")

            b = QiTimeVariable(name="B")
            # cQiMemStore(offset)

            with ForRange(a, 0, 100e-9):
                offset = b + 1
                Recording(cells[0], 12e-9, offset=offset)

        insert_recording_offset_store_commands(job)

        print(job)

        self.assertIsInstance(job.commands[2], cQiMemStore)
        self.assertIs(job.commands[2].value, offset)

        self.assertIsInstance(job.commands[3], ForRange)
        self.assertIsInstance(job.commands[3].body[0], cQiRecording)
        self.assertEqual(len(job.commands[3].body), 1)

    def test_not_invariant_expression_in_loop(self):

        with QiJob() as job:
            cells = QiCells(1)

            a = QiTimeVariable(name="A")

            b = QiTimeVariable(name="B")
            # cQiMemStore(offset)

            with ForRange(a, 0, 100e-9):
                offset = b + 1
                Recording(cells[0], 12e-9, offset=offset)

                with If(a == 20e-9):
                    Assign(b, 5)
                    # cQiMemStore(offset)

        insert_recording_offset_store_commands(job)

        print(job)

        self.assertIsInstance(job.commands[2], cQiMemStore)
        self.assertIs(job.commands[2].value, offset)

        self.assertIsInstance(job.commands[3], ForRange)
        self.assertIsInstance(job.commands[3].body[0], cQiRecording)
        self.assertIsInstance(job.commands[3].body[1], If)
        self.assertIsInstance(job.commands[3].body[1].body[1], cQiMemStore)
        self.assertIs(job.commands[3].body[1].body[1].value, offset)

    def test_multiple_cells(self):
        with QiJob() as job:
            cells = QiCells(3)

            a = QiTimeVariable(name="A")

            b = QiTimeVariable(name="B")

            with ForRange(a, 0, 100e-9):
                offset_cell_1 = a + 1
                offset_cell_2 = b + 1

                with If(a == 20e-9):
                    # cQiMemStore(cell1, offset_cell_1)
                    Assign(b, 5)
                    # cQiMemStore(cell2, offset_cell_2)
                    Recording(cells[1], 12e-9, offset=offset_cell_1)
                # with Else():
                #   cQiMemStore(cell2, offset_cell_2)

                Recording(cells[2], 12e-9, offset=offset_cell_2)
                Recording(cells[0], 12e-9, offset=20e-9)

        insert_recording_offset_store_commands(job)

        self.assertEqual(cells[0].initial_recording_offset, 20e-9)

        self.assertIsInstance(job.commands[2], ForRange)
        self.assertIsInstance(job.commands[2].body[0], If)

        if_cmd = job.commands[2].body[0]

        self.assertIsInstance(if_cmd.body[0], cQiMemStore)
        self.assertEqual(if_cmd.body[0]._relevant_cells, set([cells[1]]))
        self.assertIs(if_cmd.body[0].value, offset_cell_1)

        self.assertIsInstance(if_cmd.body[2], cQiMemStore)
        self.assertEqual(if_cmd.body[2]._relevant_cells, set([cells[2]]))
        self.assertIs(if_cmd.body[2].value, offset_cell_2)

        self.assertTrue(if_cmd.is_followed_by_else())
        self.assertIsInstance(if_cmd._else_body[0], cQiMemStore)
        self.assertIs(if_cmd._else_body[0].value, offset_cell_2)
        self.assertEqual(if_cmd._else_body[0]._relevant_cells, set([cells[2]]))

    def test_play_readout(self):
        with QiJob() as job:
            cells = QiCells(1)
            # cQiMemStore(12e-9)

            Recording(cells[0], 20e-9, 12e-9)

            # cQiMemStore(40e-9)

            PlayReadout(cells[0], QiPulse(40e-9))
            Recording(cells[0], 20e-9, 16e-9)

        insert_recording_offset_store_commands(job)

        self.assertIsInstance(job.commands[0], cQiMemStore)
        self.assertEqual(job.commands[0].value.float_value, 12e-9)

        self.assertIsInstance(job.commands[2], cQiMemStore)
        self.assertEqual(job.commands[2].value.float_value, 16e-9)

    def test_different_offsets_in_parallel_blocks_not_allowed(self):
        with QiJob() as job:
            cells = QiCells(1)

            with Parallel():
                Recording(cells[0], 12e-9, 10e-9)
            with Parallel():
                Wait(cells[0], 20e-9)
                Recording(cells[0], 12e-9, 8e-9)

        with self.assertRaisesRegex(
            RuntimeError,
            "Parallel Blocks with multiple Recording instructions with different offsets are not supported.",
        ):
            insert_recording_offset_store_commands(job)

    def test_parallel_blocks(self):
        with QiJob() as job:
            cells = QiCells(1)

            # cQiMemStore(12e-9)
            Recording(cells[0], 12e-9, 12e-9)

            # cQiMemStore(16e-9)
            with Parallel():
                Recording(cells[0], 12e-9, 16e-9)

        insert_recording_offset_store_commands(job)

        self.assertIsInstance(job.commands[0], cQiMemStore)
        self.assertEqual(job.commands[0].value.float_value, 12e-9)

        self.assertIsInstance(job.commands[2], cQiMemStore)
        self.assertEqual(job.commands[2].value.float_value, 16e-9)

    def test_multiple_recording_in_sequence(self):
        with QiJob() as job:
            cells = QiCells(1)

            # cQiMemStore(cells[0], 8e-9)
            Recording(cells[0], 8e-9, 8e-9)
            Recording(cells[0], 8e-9, 8e-9)

            # cQiMemStore(cells[0], 12e-9)
            Recording(cells[0], 8e-9, 12e-9)

            # cQiMemStore(cells[0], 16e-9)
            Recording(cells[0], 8e-9, 16e-9)

        insert_recording_offset_store_commands(job)

        self.assertIsInstance(job.commands[0], cQiMemStore)
        self.assertEqual(job.commands[0].value.float_value, 8e-9)

        self.assertIsInstance(job.commands[3], cQiMemStore)
        self.assertEqual(job.commands[3].value.float_value, 12e-9)

        self.assertIsInstance(job.commands[5], cQiMemStore)
        self.assertEqual(job.commands[5].value.float_value, 16e-9)

    def test_nested_loops(self):
        with QiJob() as job:
            cells = QiCells(1)

            a = QiTimeVariable(name="A")

            with ForRange(a, 0, 100e-9):
                # cQiMemStore
                with ForRange(QiVariable(), 0, 100):
                    with ForRange(QiVariable(), 0, 100):
                        Recording(cells[0], 8e-9, a)

        insert_recording_offset_store_commands(job)

        self.assertIsInstance(job.commands[1].body[0], cQiMemStore)
        self.assertIs(job.commands[1].body[0].value, a)

    def test_qi_cell_property_recording_offset(self):
        with QiJob() as job:
            cells = QiCells(1)

            cell_prop_1 = cells[0]["first_rec_offset"]
            cell_prop_2 = cells[0]["second_rec_offset"]
            cell_prop_3 = cells[0]["third_rec_offset"]

            # cQiMemStore(cells[0], cells[0]["second_rec_offset"])

            with ForRange(QiTimeVariable(), 0, 100e-9):
                Recording(cells[0], 20e-9, cell_prop_2)

            # cQiMemStore(cells[0], cells[0]["third_rec_offset"]) // the factor of two is folded into the QiCellProperty

            Recording(cells[0], 20e-9, cell_prop_3 * 2)

        insert_recording_offset_store_commands(job)

        print(job)

        self.assertIsInstance(job.commands[0], cQiMemStore)
        self.assertIs(job.commands[0].value, cell_prop_2)

        self.assertIsInstance(job.commands[3], cQiMemStore)
        self.assertIs(job.commands[3].value, cell_prop_3)


class PlayFrequencyTest(unittest.TestCase):
    def test_simple_play(self):
        with QiJob() as job:
            cells = QiCells(1)

            # cQiMemStore
            Play(cells[0], QiPulse(20e-9, frequency=10))
            # cQiMemStore
            Play(cells[0], QiPulse(20e-9, frequency=20))

        insert_manipulation_pulse_frequency_store_commands(job)

        self.assertIsInstance(job.commands[0], cQiMemStore)
        self.assertEqual(job.commands[0].addr, MANIPULATION_PULSE_FREQUENCY_ADDRESS)
        self.assertEqual(job.commands[0].value, 10)

        self.assertIsInstance(job.commands[1], cQiPlay)

        self.assertIsInstance(job.commands[2], cQiMemStore)
        self.assertEqual(job.commands[2].addr, MANIPULATION_PULSE_FREQUENCY_ADDRESS)
        self.assertEqual(job.commands[2].value, 10)

        self.assertIsInstance(job.commands[3], cQiPlay)

    def test_keep_frequency(self):
        with QiJob() as job:
            cells = QiCells(1)

            # cQiMemStore
            Play(cells[0], QiPulse(20e-9, frequency=10))

            Play(cells[0], QiPulse(20e-9))
            # cQiMemStore
            Play(cells[0], QiPulse(20e-9, frequency=20))

            insert_manipulation_pulse_frequency_store_commands(job)

            self.assertIsInstance(job.commands[0], cQiMemStore)
            self.assertEqual(job.commands[0].value, 10)

            self.assertIsInstance(job.commands[1], cQiPlay)

            self.assertIsInstance(job.commands[2], cQiPlay)

            self.assertIsInstance(job.commands[3], cQiMemStore)
            self.assertEqual(job.commands[3].value, 10)

            self.assertIsInstance(job.commands[4], cQiPlay)

    def test_readout_frequency(self):
        with QiJob() as job:
            cells = QiCells(1)

            # cQiMemStore
            PlayReadout(cells[0], QiPulse(20e-9, frequency=10))
            # cQiMemStore
            PlayReadout(cells[0], QiPulse(20e-9, frequency=20))

        insert_readout_pulse_frequency_store_commands(job)

        self.assertIsInstance(job.commands[0], cQiMemStore)
        self.assertEqual(job.commands[0].addr, READOUT_PULSE_FREQUENCY_ADDRESS)
        self.assertEqual(job.commands[0].value, 10)

        self.assertIsInstance(job.commands[1], cQiPlayReadout)

        self.assertIsInstance(job.commands[2], cQiMemStore)
        self.assertEqual(job.commands[2].addr, READOUT_PULSE_FREQUENCY_ADDRESS)
        self.assertEqual(job.commands[2].value, 10)

        self.assertIsInstance(job.commands[3], cQiPlayReadout)

    def test_initial_manip_frequency(self):
        with QiJob() as job:
            cells = QiCells(1)

            Play(cells[0], QiPulse(20e-9, frequency=10))

        insert_manipulation_pulse_frequency_store_commands(job)

        self.assertEqual(cells[0].initial_manipulation_frequency, 10)

    def test_initial_readout_frequency(self):
        with QiJob() as job:
            cells = QiCells(1)

            PlayReadout(cells[0], QiPulse(20e-9, frequency=10))

        insert_readout_pulse_frequency_store_commands(job)

        self.assertEqual(cells[0].initial_readout_frequency, 10)

    def test_manip_and_readout_frequencies_combined(self):
        with QiJob() as job:
            cells = QiCells(1)

            # cQiMemStore for PlayReadout
            # cQiMemStore for Play

            Play(cells[0], QiPulse(20e-9, frequency=10))

            # cQiMemStore for Play

            PlayReadout(cells[0], QiPulse(20e-9, frequency=10))

            Play(cells[0], QiPulse(20e-9, frequency=20))

            # cQiMemStore for Play

            PlayReadout(cells[0], QiPulse(20e-9, frequency=10))

            # cQiMemStore for PlayReadout

            Play(cells[0], QiPulse(20e-9, frequency=30))

            PlayReadout(cells[0], QiPulse(20e-9, frequency=20))

        job._build_program()

        self.assertIsInstance(job.commands[0], cQiMemStore)
        self.assertEqual(job.commands[0].value, 10)
        self.assertEqual(job.commands[0].addr, READOUT_PULSE_FREQUENCY_ADDRESS)

        self.assertIsInstance(job.commands[1], cQiMemStore)
        self.assertEqual(job.commands[1].value, 10)
        self.assertEqual(job.commands[1].addr, MANIPULATION_PULSE_FREQUENCY_ADDRESS)

        self.assertIsInstance(job.commands[2], cQiPlay)

        self.assertIsInstance(job.commands[3], cQiMemStore)
        self.assertEqual(job.commands[3].value, 20)
        self.assertEqual(job.commands[3].addr, MANIPULATION_PULSE_FREQUENCY_ADDRESS)

        self.assertIsInstance(job.commands[4], cQiPlayReadout)

        self.assertIsInstance(job.commands[5], cQiPlay)

        self.assertIsInstance(job.commands[6], cQiMemStore)
        self.assertEqual(job.commands[6].value, 60)
        self.assertEqual(job.commands[6].addr, MANIPULATION_PULSE_FREQUENCY_ADDRESS)

        self.assertIsInstance(job.commands[7], cQiPlayReadout)

        self.assertIsInstance(job.commands[8], cQiMemStore)
        self.assertEqual(job.commands[8].value, 20)
        self.assertEqual(job.commands[8].addr, READOUT_PULSE_FREQUENCY_ADDRESS)

        self.assertIsInstance(job.commands[9], cQiPlay)

        self.assertIsInstance(job.commands[10], cQiPlayReadout)

    def test_variable_manipulation_frequency(self):
        with QiJob() as job:
            cells = QiCells(1)

            x = QiVariable(name="X")

            with ForRange(x, 0, 100):
                Play(cells[0], QiPulse(20e-9, frequency=x))

        job._build_program()

        self.assertIsInstance(job.commands[1], ForRange)
        self.assertIsInstance(job.commands[1].body[0], cQiMemStore)
        self.assertEqual(
            job.commands[1].body[0].addr, MANIPULATION_PULSE_FREQUENCY_ADDRESS
        )
        self.assertIs(job.commands[1].body[0].value, x)

        self.assertIsInstance(job.commands[1].body[1], cQiPlay)

    def test_command_with_no_manipulation_frequency(self):
        with QiJob() as job:
            cells = QiCells(1)

            # cQiMemStore
            Play(cells[0], QiPulse(20e-9, frequency=12e3))
            Play(cells[0], QiPulse(20e-9))  # inherits frequency from prev command.

            # cQiMemStore
            Play(cells[0], QiPulse(20e-9, frequency=24e3))

        job._build_program()

        self.assertIsInstance(job.commands[0], cQiMemStore)
        self.assertEqual(job.commands[0].value.float_value, 12e3)
        self.assertEqual(job.commands[0].addr, MANIPULATION_PULSE_FREQUENCY_ADDRESS)

        self.assertIsInstance(job.commands[1], cQiPlay)

        self.assertIsInstance(job.commands[2], cQiPlay)

        self.assertIsInstance(job.commands[3], cQiMemStore)
        self.assertEqual(job.commands[3].value.float_value, 24e3)
        self.assertEqual(job.commands[3].addr, MANIPULATION_PULSE_FREQUENCY_ADDRESS)

        self.assertIsInstance(job.commands[4], cQiPlay)

    def test_command_with_no_readout_frequency(self):
        with QiJob() as job:
            cells = QiCells(1)

            # cQiMemStore
            PlayReadout(cells[0], QiPulse(20e-9, frequency=12e3))
            PlayReadout(
                cells[0], QiPulse(20e-9)
            )  # inherits frequency from prev command.

            # cQiMemStore
            PlayReadout(cells[0], QiPulse(20e-9, frequency=24e3))

        job._build_program()

        self.assertIsInstance(job.commands[0], cQiMemStore)
        self.assertEqual(job.commands[0].value.float_value, 12e3)
        self.assertEqual(job.commands[0].addr, READOUT_PULSE_FREQUENCY_ADDRESS)

        self.assertIsInstance(job.commands[1], cQiPlayReadout)

        self.assertIsInstance(job.commands[2], cQiPlayReadout)

        self.assertIsInstance(job.commands[3], cQiMemStore)
        self.assertEqual(job.commands[3].value.float_value, 24e3)
        self.assertEqual(job.commands[3].addr, READOUT_PULSE_FREQUENCY_ADDRESS)

        self.assertIsInstance(job.commands[4], cQiPlayReadout)

    def test_integer_pseudo_vna(self):
        with QiJob() as pseudo_vna:
            q = QiCells(1)
            fr = QiVariable()
            with ForRange(fr, 0, 100000000, 100000):
                PlayReadout(q[0], QiPulse(416e-9, frequency=fr))
                Recording(q[0], 400e-9, 280e-9, save_to="result")
                Wait(q[0], 2e-6)

        pseudo_vna._build_program()

        self.assertIsInstance(pseudo_vna.commands[1], ForRange)

        self.assertIsInstance(pseudo_vna.commands[1].body[0], cQiMemStore)
        self.assertEqual(pseudo_vna.commands[1].body[0].value, fr)

        self.assertTrue(len(pseudo_vna.cell_seq_dict[q[0]].instruction_list) > 20)

    def test_float_pseudo_vna(self):
        with QiJob() as pseudo_vna:
            q = QiCells(1)
            fr = QiVariable()
            with ForRange(fr, 0, 100e6, 0.1e6):
                PlayReadout(q[0], QiPulse(416e-9, frequency=fr))
                Recording(q[0], 400e-9, 280e-9, save_to="result")
                Wait(q[0], 2e-6)

        pseudo_vna._build_program()

        self.assertIsInstance(pseudo_vna.commands[1], ForRange)

        self.assertIsInstance(pseudo_vna.commands[1].body[0], cQiMemStore)
        self.assertEqual(pseudo_vna.commands[1].body[0].value, fr)

        self.assertTrue(len(pseudo_vna.cell_seq_dict[q[0]].instruction_list) > 20)

    def test_preserve_frequency(self):
        # This tests ensures that programs with empty Memory Parameters (like the second Play command here)
        # still can have a constant memory parameter and therefore don't insert a store command in the beginning.

        with QiJob() as job:
            q = QiCells(1)
            Play(q[0], QiPulse(100e-9, frequency=100e6))
            Play(q[0], QiPulse(200e-9))

        job._build_program()
        self.assertIsInstance(job.commands[0], cQiPlay)
        self.assertIsInstance(job.commands[1], cQiPlay)
