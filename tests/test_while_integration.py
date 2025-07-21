"""Test While loop integration with existing QiCode features."""

from qiclib.code import *


def test_while_with_if_statements():
    """Test While loop containing If statements."""
    with QiJob() as job:
        q = QiCells(1)
        counter = QiIntVariable(0)
        flag = QiIntVariable(1)

        with While(counter < 5):
            with If(flag == 1):
                Wait(q[0], 1e-6)
            with Else():
                Wait(q[0], 2e-6)
            Assign(counter, counter + 1)

    # Find the while command
    while_cmd = None
    for cmd in job.commands:
        if hasattr(cmd, "__class__") and cmd.__class__.__name__ == "WhileCommand":
            while_cmd = cmd
            break

    assert while_cmd is not None
    assert len(while_cmd.body) == 2  # If command and Assign command

    # Check that first command in body is an If command
    if_cmd = while_cmd.body[0]
    assert hasattr(if_cmd, "__class__") and if_cmd.__class__.__name__ == "IfCommand"


def test_while_with_for_range():
    """Test While loop containing ForRange loop."""
    with QiJob() as job:
        q = QiCells(1)
        outer_counter = QiIntVariable(0)
        inner_var = QiIntVariable()

        with While(outer_counter < 3):
            with ForRange(inner_var, 0, 5, 1):
                Wait(q[0], 1e-6)
            Assign(outer_counter, outer_counter + 1)

    assert (
        job.get_assembly()
        == [
            "tr 0x0, 0x0, 0x0, 0x0, 0x0, 0x0",
            "addi r1, r0, 0x0",  # r1 => outer_counter
            "addi r3, r0, 0x3",  # r3 => outer_counter end value
            "bge r1, r3, 0x9",  # Branch to end if r1 >= r3
            "addi r4, r0, 0x5",  # r4 => inner_var end value (uses different register than outer loop)
            "addi r2, r0, 0x0",  # r2 => inner_var
            "bge r2, r4, 0x4",  # Branch to outer loop increment if r2 >= r4
            "wti 0xfa",  # Wait
            "addi r2, r2, 0x1",  # Increment r2 by 1
            "j -0x3",  # Jump to `bge r2, ...` call
            "addi r1, r1, 0x1",  # Increment outer_counter by 1
            "j -0x8",  # Jump to comparison `bge r1, ...`
            "end",
        ]
    )


def test_while_string_representation_in_job():
    """Test that While loop appears correctly in job string representation."""
    with QiJob() as job:
        q = QiCells(1)
        counter = QiIntVariable(0)

        with While(counter < 3):
            Wait(q[0], 1e-6)
            Assign(counter, counter + 1)

    job_str = str(job)
    assert (
        job_str
        == """\
QiJob:
    q = QiCells(1)
    v0 =  QiVariable()
    Assign(v0, 0)
    While(v0 < 3):
        Wait(q[0], 1e-06)
        Assign(v0, (v0 + 1))\
"""
    )


def test_while_with_sync():
    """Test While loop with cell synchronization."""
    with QiJob() as job:
        q = QiCells(2)
        counter = QiIntVariable(0)

        with While(counter < 3):
            Wait(q[0], 1e-6)
            Wait(q[1], 2e-6)
            Sync(q[0], q[1])
            Assign(counter, counter + 1)

    while_cmd = None
    for cmd in job.commands:
        if hasattr(cmd, "__class__") and cmd.__class__.__name__ == "WhileCommand":
            while_cmd = cmd
            break

    assert while_cmd is not None
    assert len(while_cmd.body) == 4  # Two waits, sync, assign


def test_while_with_variable_pulse_properties():
    """Test While loop with variable pulse properties."""
    with QiJob() as job:
        q = QiCells(1)
        counter = QiIntVariable(0)
        amplitude = QiAmplitudeVariable(0.5)

        with While(counter < 3):
            pulse = QiPulse(1e-6, amplitude=amplitude)
            Play(q[0], pulse)
            Assign(counter, counter + 1)
            Assign(amplitude, amplitude + 0.1)

    while_cmd = None
    for cmd in job.commands:
        if hasattr(cmd, "__class__") and cmd.__class__.__name__ == "WhileCommand":
            while_cmd = cmd
            break

    assert while_cmd is not None
    assert len(while_cmd.body) == 3  # Play, two assigns


def test_while_loop_assembly_generation():
    """Test that While loop can generate assembly code without errors."""
    with QiJob() as job:
        q = QiCells(1)
        counter = QiIntVariable(0)

        with While(counter < 5):
            Wait(q[0], 1e-6)
            Assign(counter, counter + 1)

    assembly = job.get_assembly()
    assert assembly == [
        "tr 0x0, 0x0, 0x0, 0x0, 0x0, 0x0",
        "addi r1, r0, 0x0",
        "addi r2, r0, 0x5",
        "bge r1, r2, 0x4",
        "wti 0xfa",
        "addi r1, r1, 0x1",
        "j -0x3",
        "end",
    ]


def test_while_with_time_variables():
    """Test While loop with time-based conditions."""
    with QiJob() as job:
        q = QiCells(1)
        elapsed_time = QiTimeVariable(0.0)

        with While(elapsed_time < 10e-6):  # 10 microseconds
            Wait(q[0], 1e-6)
            Assign(elapsed_time, elapsed_time + 1e-6)

    while_cmd = None
    for cmd in job.commands:
        if hasattr(cmd, "__class__") and cmd.__class__.__name__ == "WhileCommand":
            while_cmd = cmd
            break

    assert while_cmd is not None
    assert len(while_cmd.body) == 2  # Wait and Assign


def test_while_with_frequency_variables():
    """Test While loop with frequency-based conditions."""
    with QiJob() as job:
        q = QiCells(1)
        frequency = QiFrequencyVariable(100e6)  # 100 MHz
        max_freq = QiFrequencyVariable(200e6)  # 200 MHz
        freq_step = QiFrequencyVariable(10e6)  # 10 MHz

        with While(frequency < max_freq):  # Up to 200 MHz
            pulse = QiPulse(1e-6, frequency=frequency)
            Play(q[0], pulse)
            Assign(frequency, frequency + freq_step)  # Increment by 10 MHz

    while_cmd = None
    for cmd in job.commands:
        if hasattr(cmd, "__class__") and cmd.__class__.__name__ == "WhileCommand":
            while_cmd = cmd
            break

    assert while_cmd is not None
    assert len(while_cmd.body) == 2  # Play and Assign
