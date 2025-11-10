import pytest

from qiclib.code import *
from qiclib.code.qi_sequencer import Sequencer


def test_static_variable_is_present():
    with QiJob() as job:
        q = QiCells(1)
        v = QiVariable(int, 1, static=True)
        with If(v == 1):
            Wait(q[0], 12e-9)

    job._build_program()

    assert job.get_assembly() == [
        "tr 0x0, 0x0, 0x0, 0x0, 0x0, 0x0",
        "lui r1, 0x8000",
        "addi r1, r1, 0x400",
        "lw r2, 0(r1)",
        "addi r3, r0, 0x1",
        "bne r2, r3, 0x2",
        "wti 0x3",
        "end",
    ]
    static_region = job.cell_seq_dict[job.cells[0]].static_region
    assert len(static_region) == 1
    assert static_region[0] == 1


def test_static_variable_assignment():
    with QiJob() as job:
        q = QiCells(1)
        v = QiVariable(int, 2, static=True)
        with If(v == 2):
            Assign(v, 0)
            Wait(q[0], 12e-9)

    job._build_program()
    assert job.get_assembly() == [
        "tr 0x0, 0x0, 0x0, 0x0, 0x0, 0x0",
        "lui r1, 0x8000",
        "addi r1, r1, 0x400",
        "lw r2, 0(r1)",
        "addi r3, r0, 0x2",
        "bne r2, r3, 0x5",
        "lui r3, 0x8000",
        "addi r3, r3, 0x400",
        "sw r0, 0(r3)",
        "wti 0x3",
        "end",
    ]
    static_region = job.cell_seq_dict[job.cells[0]].static_region
    assert len(static_region) == 1
    assert static_region[0] == 2


def test_static_variable_computation():
    with QiJob() as job:
        q = QiCells(1)
        v = QiVariable(int, 1, static=True)
        Assign(v, v + 1)
        # Prevents optimizations since v must be used in a cell
        with If(v == 1):
            Wait(q[0], 12e-9)

    assert (
        job.get_assembly()
        == [
            "tr 0x0, 0x0, 0x0, 0x0, 0x0, 0x0",
            "lui r1, 0x8000",  # r1 -> source address
            "addi r1, r1, 0x400",
            "lui r2, 0x8000",  # r2 -> target address. This hurts a bit, but we're not optimizing at the moment
            "addi r2, r2, 0x400",
            "lw r3, 0(r2)",  # r3 = mem[r2]
            "addi r4, r3, 0x1",  # Set r4 = r3 + 1
            "sw r4, 0(r1)",  # Write back r4 to mem[r1]
            "lui r5, 0x8000",  # Load target address
            "addi r5, r5, 0x400",
            "lw r6, 0(r5)",  # Load the word we have just written
            "addi r7, r0, 0x1",  # Compare value (1)
            "bne r6, r7, 0x2",  # branch (from if condition)
            "wti 0x3",  # Wait
            "end",
        ]
    )
    static_region = job.cell_seq_dict[job.cells[0]].static_region
    assert len(static_region) == 1
    assert static_region[0] == 1


def test_static_region_with_recording():
    with QiJob() as job:
        q = QiCells(1)
        v = QiVariable(int, 0, static=True)
        Assign(v, v + 1)
        sv = QiStateVariable()
        Recording(q[0], duration=200e-9, state_to=sv)
        with If(v == 1):
            Wait(q[0], 12e-9)

    assert (
        job.get_assembly()
        == [
            "tr 0x0, 0x0, 0x0, 0x0, 0x0, 0x0",
            "lui r1, 0x8000",  # r1 -> source address
            "addi r1, r1, 0x400",
            "lui r2, 0x8000",  # r2 -> target address. This hurts a bit, but we're not optimizing at the moment
            "addi r2, r2, 0x400",
            "lw r3, 0(r2)",  # r3 = mem[r2]
            "addi r4, r3, 0x1",  # Set r4 = r3 + 1
            "sw r4, 0(r1)",  # Write back r4 to mem[r1]
            "tr 0x0, 0x2, 0x0, 0x0, 0x0, 0x0",  # Recording trigger
            "wtq r5, 0",  # Wait until recording is done
            "lui r6, 0x8000",  # Load target address
            "addi r6, r6, 0x400",
            "lw r7, 0(r6)",  # Load the word we have just written
            "addi r8, r0, 0x1",  # Compare value (1)
            "bne r7, r8, 0x2",  # branch (from if condition)
            "wti 0x3",  # Wait
            "end",
        ]
    )


def test_cannot_store_more_than_4095_words():
    sequencer = Sequencer(0)
    sequencer.request_memory([0] * 4095)  # Should not raise

    sequencer.reset()
    with pytest.raises(RuntimeError):
        sequencer.request_memory([0] * 4096)
