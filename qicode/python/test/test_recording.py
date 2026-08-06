from qicode import QiCells, QiJob, Recording
from qicode.proto import RecordingCommand


def test_recording_toggle_continuous_true():
    with QiJob() as job:
        q = QiCells(1)
        Recording(q[0], toggle_continuous=True)

    cmd = job.commands[0].recordingCommand
    assert cmd.mode == RecordingCommand.Mode.ContinuousOn


def test_recording_toggle_continuous_false():
    with QiJob() as job:
        q = QiCells(1)
        Recording(q[0], toggle_continuous=False)

    cmd = job.commands[0].recordingCommand
    assert cmd.mode == RecordingCommand.Mode.ContinuousOff


def test_recording_normal_mode():
    with QiJob() as job:
        q = QiCells(1)
        Recording(q[0])

    cmd = job.commands[0].recordingCommand
    assert cmd.mode == RecordingCommand.Mode.Normal
