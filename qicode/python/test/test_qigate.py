from qicode.qi_cell import QiCells
from qicode.qi_command import Play, QiGate
from qicode.qi_job import QiJob
from qicode.qi_pulse import QiPulse


def test_qigate_wraps_play_in_gate_command():
    @QiGate
    def my_pi_pulse(cell):
        Play(cell, QiPulse(48e-9))

    with QiJob() as job:
        q = QiCells(1)
        my_pi_pulse(q[0])

    assert len(job.commands) == 1
    cmd = job.commands[0]
    assert cmd.HasField("gateCommand")
    gate_body = cmd.gateCommand.body
    assert len(gate_body) == 1
    assert gate_body[0].HasField("playCommand")


def test_qigate_preserves_function_name():
    @QiGate
    def my_custom_gate(cell):
        Play(cell, QiPulse(24e-9))

    assert my_custom_gate.__name__ == "my_custom_gate"


def test_qigate_multiple_commands_in_body():
    @QiGate
    def double_pulse(cell):
        Play(cell, QiPulse(48e-9))
        Play(cell, QiPulse(24e-9))

    with QiJob() as job:
        q = QiCells(1)
        double_pulse(q[0])

    assert len(job.commands) == 1
    gate_body = job.commands[0].gateCommand.body
    assert len(gate_body) == 2
    assert all(c.HasField("playCommand") for c in gate_body)
