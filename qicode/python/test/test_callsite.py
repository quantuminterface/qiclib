from qicode import If, Play, QiCells, QiJob, QiPulse, QiVariable, Sync, Wait
from qicode.proto import CallSite


def test_callsites():
    with QiJob() as job:
        q = QiCells(1)
        Play(q[0], QiPulse(length=200e-9, frequency=10e6))
        Sync(q[0])
        x = QiVariable(int, 2)
        with If(x > 1):
            Wait(q[0], 10e-6)

    assert job.commands[0].sourceInfo == CallSite(
        file=__file__,
        line=8,
    )
    assert job.commands[1].sourceInfo == CallSite(
        file=__file__,
        line=9,
    )
    # Declare command
    assert job.commands[2].sourceInfo == CallSite(
        file=__file__,
        line=10,
    )
    assert job.commands[3].sourceInfo == CallSite(
        file=__file__,
        line=11,
    )
    assert job.commands[3].ifCommand.body[0].sourceInfo == CallSite(
        file=__file__,
        line=12,
    )
