import numpy as np
import pytest

from qiclib.code import *
from qiclib.code.qi_types import QiType


def test_stringify_qi_array():
    qi_array = QiType.ARRAY(QiType.NORMAL)
    assert str(qi_array) == "Array[NORMAL, ?]"

    qi_array = QiType.ARRAY(QiType.NORMAL, (10,))
    assert str(qi_array) == "Array[NORMAL, 10]"

    qi_array = QiType.ARRAY(QiType.NORMAL, (10, 20))
    assert str(qi_array) == "Array[NORMAL, 10x20]"

    qi_array = QiType.ARRAY(QiType.NORMAL, (10, None))
    assert str(qi_array) == "Array[NORMAL, 10x?]"


def test_qi_array_can_be_declared():
    with QiJob() as job:
        _v = QiVariable(type=QiType.ARRAY(element_type=QiType.NORMAL, shape=(10,)))
        _v[0]

    # Should compile
    job._build_program()


def test_assigning_element_of_array_to_variable():
    with QiJob() as job:
        v = QiVariable(type=QiType.ARRAY(element_type=QiType.NORMAL, shape=(10,)))
        u = QiVariable(type=QiType.NORMAL)
        Assign(u, v[0])

    # Should compile
    job._build_program()


def test_array_index_must_be_normal():
    with QiJob():
        v = QiVariable(type=QiType.ARRAY(element_type=QiType.NORMAL, shape=(10,)))
        index = QiVariable(type=QiType.FREQUENCY, name="index")
        with pytest.raises(
            TypeError,
        ):
            v[index]


def test_qi_array_in_for_loop():
    with QiJob() as job:
        q = QiCells(1)
        f = QiVariable(
            type=QiType.ARRAY(element_type=QiType.FREQUENCY, shape=(10,)), name="f"
        )
        i = QiIntVariable(0, name="i")
        with ForRange(i, 0, 10):
            Play(q[0], QiPulse(length=100e-9, frequency=f[i]))

    assert (
        job.get_assembly()
        == [
            "tr 0x0, 0x0, 0x0, 0x0, 0x0, 0x0",
            "addi r1, r0, 0x0",  # This is incorrect and an artifact from loop unrolling (I think)
            "addi r2, r0, 0xa",  # Initialize loop destination
            "addi r1, r0, 0x0",  # Initialize loop counter
            "bge r1, r2, 0xc",  # If r1 > 10, jump to end
            "lui r4, 0x8000",  # Load address
            "addi r4, r4, 0x400",  # ...
            "add r3, r1, r4",  # Add index
            "lw r4, 0(r3)",  # Load the frequency word to r3
            "lui r5, 0x6000",  # Load storage address
            "addi r5, r5, 0x5",  # ...
            "sw r4, 0(r5)",  # Write the register to the NCO address
            "tr 0x0, 0x0, 0x1, 0x0, 0x0, 0x0",  # Play the pulse
            "wti 0x18",  # Wait
            "addi r1, r1, 0x1",  # Increment loop counter by 1
            "j -0xb",  # Jump to beginning
            "end",
        ]
    )


def test_qi_array_initial_values():
    with QiJob() as job:
        q = QiCells(1)
        f = QiVariable(
            type=QiType.ARRAY(element_type=QiType.FREQUENCY, shape=(10,)),
            value=[10e6, 20e6, 30e6, 40e6, 50e6, 60e6, 70e6, 80e6, 90e6, 100e6],
            name="f",
        )
        i = QiIntVariable(0, name="i")
        with ForRange(i, 0, 10):
            Play(q[0], QiPulse(length=100e-9, frequency=f[i]))

    job._build_program()
    assert job.cell_seq_dict[job.cells[0]].static_region == [
        42949673,
        85899346,
        128849019,
        171798692,
        214748365,
        257698038,
        300647711,
        343597384,
        386547057,
        429496730,
    ]


def test_qi_array_type_inference():
    with QiJob() as job:
        q = QiCells(1)
        f = QiVariable(
            value=[10e6, 20e6],
            name="f",
        )
        i = QiIntVariable(0, name="i")
        with ForRange(i, 0, 10):
            Play(q[0], QiPulse(length=100e-9, frequency=f[i]))

    job._build_program()
    assert f.type == QiType.ARRAY(element_type=QiType.FREQUENCY, shape=(2,))

    with QiJob() as job:
        q = QiCells(1)
        t = QiVariable(
            value=[1e-6, 2e-6, 3e-6],
            name="t",
        )
        i = QiIntVariable(0, name="i")
        with ForRange(i, 0, 10):
            Play(q[0], QiPulse(length=t[i]))

    job._build_program()
    assert t.type == QiType.ARRAY(element_type=QiType.TIME, shape=(3,))


def test_compatibility_with_numpy():
    freqcs = np.arange(100e6, 500e6, 10e6)
    with QiJob() as job:
        q = QiCells(1)
        f = QiVariable(
            value=freqcs,
            name="f",
        )
        i = QiIntVariable(0, name="i")
        with ForRange(i, 0, 10):
            Play(q[0], QiPulse(length=100e-9, frequency=f[i]))

    job._build_program()
    assert f.type == QiType.ARRAY(element_type=QiType.FREQUENCY, shape=freqcs.shape)
