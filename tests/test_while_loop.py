"""Test While loop functionality in QiCode."""

import pytest

from qiclib.code import *


def check_job_compiles(job: QiJob):
    try:
        job._build_program()
    except RuntimeError as e:
        pytest.fail(f"Job {job} did not compile successfully: {e}")


def test_while_loop_basic_functionality():
    """Test that while loops can be created and used in programs."""
    with QiJob() as job:
        q = QiCells(1)
        counter = QiIntVariable(0)

        with While(counter < 5):
            Wait(q[0], 1e-6)
            Assign(counter, counter + 1)

    check_job_compiles(job)


def test_while_loop_with_state_variables():
    """Test while loops work with state variables in conditions."""
    with QiJob() as job:
        q = QiCells(1)
        state = QiStateVariable()

        # Record initial state
        Recording(q[0], 1e-6, state_to=state)

        # While loop with state condition
        with While(state != 1):
            Wait(q[0], 500e-9)
            Recording(q[0], 1e-6, state_to=state)

    check_job_compiles(job)


def test_while_loop_assembly_generation():
    """Test that while loops generate correct assembly instructions."""
    with QiJob() as job:
        q = QiCells(1)
        counter = QiIntVariable(0)

        with While(counter < 3):
            Wait(q[0], 1e-6)
            Assign(counter, counter + 1)

    # Build and verify assembly contains branch instructions
    # Get assembly code for the cell
    assembly_lines = job.get_assembly(q, 0)

    # Should contain branch and jump instructions for while loop
    has_branch = any(
        "bge" in line or "blt" in line or "beq" in line or "bne" in line
        for line in assembly_lines
    )
    has_jump = any("j " in line for line in assembly_lines)

    assert has_branch, "While loop should generate branch instructions"
    assert has_jump, "While loop should generate jump instructions for iteration"


def test_while_loop_nested_behavior():
    """Test nested while loops generate correct structure."""
    with QiJob() as job:
        q = QiCells(1)
        outer = QiIntVariable(0)
        inner = QiIntVariable(0)

        with While(outer < 2):
            with While(inner < 3):
                Wait(q[0], 1e-6)
                Assign(inner, inner + 1)
            Assign(outer, outer + 1)
            Assign(inner, 0)

    # Verify compilation and structure
    # Should generate multiple branch/jump pairs
    assembly_lines = job.get_assembly(q, 0)
    branch_count = sum(
        1
        for line in assembly_lines
        if any(op in line for op in ["bge", "blt", "beq", "bne"])
    )
    jump_count = sum(1 for line in assembly_lines if "j " in line)

    # Nested loops should generate multiple branches and jumps
    assert branch_count >= 2, "Nested while loops should generate multiple branches"
    assert jump_count >= 2, "Nested while loops should generate multiple jumps"


def test_while_loop_condition_types():
    """Test different condition types in while loops."""
    with QiJob() as job:
        q = QiCells(1)

        # Integer conditions
        int_var = QiIntVariable(0)
        with While(int_var < 5):
            Assign(int_var, int_var + 1)

        # Time conditions
        time_var = QiTimeVariable(0.0)
        with While(time_var < 1e-3):
            Assign(time_var, time_var + 100e-6)

        # State conditions
        state_var = QiStateVariable()
        Recording(q[0], 1e-6, state_to=state_var)
        with While(state_var == 0):
            Recording(q[0], 1e-6, state_to=state_var)

    check_job_compiles(job)


def test_while_loop_with_recordings():
    """Test while loops with recording operations for state feedback."""
    with QiJob() as job:
        q = QiCells(1)
        measurement_count = QiIntVariable(0)

        # Loop until we get enough measurements
        with While(measurement_count < 10):
            Recording(q[0], 1e-6, save_to=f"measurement_{measurement_count}")
            Wait(q[0], 100e-6)  # Wait between measurements
            Assign(measurement_count, measurement_count + 1)

    # Verify the structure makes sense
    # Should have recording instructions
    assembly_lines = job.get_assembly(q, 0)
    # Recording operations appear as 'tr' (trigger) instructions in assembly
    has_recording = any("tr" in line.lower() for line in assembly_lines)

    assert has_recording, "While loop should contain recording operations"


def test_while_loop_error_conditions():
    """Test error handling in while loop creation."""
    # Invalid condition type should raise error
    with pytest.raises(
        RuntimeError, match="While loop condition must be a QiCondition"
    ):
        with QiJob():
            q = QiCells(1)
            counter = QiIntVariable(0)
            with While(counter):  # Not a condition
                Wait(q[0], 1e-6)


def test_while_loop_with_multiple_cells():
    """Test while loops affecting multiple qubits."""
    with QiJob() as job:
        q = QiCells(3)
        counter = QiIntVariable(0)

        with While(counter < 5):
            # Operations on all cells
            Wait(q[0], 1e-6)
            Wait(q[1], 2e-6)
            Wait(q[2], 1.5e-6)
            Assign(counter, counter + 1)

    # Verify compilation handles multiple cells
    # Each cell should have meaningful content
    for i in range(len(q)):
        assembly = job.get_assembly(q, i)
        assert len(assembly) > 0, f"Cell {i} should have generated code"


def test_while_loop_state_based_termination():
    """Test a realistic state-based while loop scenario."""
    with QiJob() as job:
        q = QiCells(1)
        qubit_state = QiStateVariable()
        attempt_count = QiIntVariable(0)

        # Initialize state
        Recording(q[0], 1e-6, state_to=qubit_state)

        # Keep trying until we get the desired state
        with While(qubit_state != 1):
            # Do some operation (simplified from PiPulse for testing)
            Wait(q[0], 1e-6)

            # Measure the result
            Recording(q[0], 1e-6, state_to=qubit_state)

            # Increment attempt counter
            Assign(attempt_count, attempt_count + 1)

    check_job_compiles(job)


def test_while_loop_integration_with_if():
    """Test while loops working together with if statements."""
    with QiJob() as job:
        q = QiCells(1)
        counter = QiIntVariable(0)
        state = QiStateVariable()

        Recording(q[0], 1e-6, state_to=state)

        with While(counter < 10):
            with If(state == 0):
                Wait(q[0], 500e-9)  # Simplified operation instead of PiPulse

            Recording(q[0], 1e-6, state_to=state)
            Assign(counter, counter + 1)

    check_job_compiles(job)


def test_while_loop_timing_consistency():
    """Test that while loop timing behavior is predictable."""
    with QiJob() as job:
        q = QiCells(1)
        counter = QiIntVariable(0)

        # Fixed timing operations in loop
        with While(counter < 3):
            Wait(q[0], 1e-6)  # Always 1 microsecond
            Assign(counter, counter + 1)

    # Verify timing information is preserved
    # Assembly should contain wait instructions with correct timing
    assembly_lines = job.get_assembly(q, 0)
    # Wait operations appear as 'wti' (wait time immediate) instructions
    has_wait = any("wti" in line.lower() for line in assembly_lines)

    assert has_wait, "While loop should preserve timing operations"
