from qicode.qi_pulse import SHAPE_ID_RECT

from qicode import (
    Assign,
    Else,
    If,
    Play,
    QiCells,
    QiJob,
    QiPulse,
    QiVariable,
    Sync,
)
from qicode.proto import (
    Cell,
    DeclareCommand,
    DiscretePulse,
    Expression,
    PlayCommand,
    Pulse,
    Shape,
    SyncCommand,
    Type,
    Variable,
)


def test_sync_command():
    with QiJob() as job:
        cells = QiCells(2)
        Sync()

    assert job.commands[0].syncCommand == SyncCommand(cells=[])

    with QiJob() as job:
        cells = QiCells(2)
        Sync(cells[0])

    assert job.commands[0].syncCommand == SyncCommand(cells=[Cell(index=0)])

    with QiJob() as job:
        cells = QiCells(2)
        Sync(cells[0], cells[1])

    assert job.commands[0].syncCommand == SyncCommand(
        cells=[Cell(index=0), Cell(index=1)]
    )


def test_play_command():
    with QiJob() as job:
        cells = QiCells(1)
        Play(cells[0], QiPulse(length=1e-6, frequency=100e6))
    assert job.commands[0].playCommand == PlayCommand(
        cell=Cell(index=0),
        pulse=Pulse(
            discrete=DiscretePulse(
                length=Expression(literal=Expression.Literal(floatLiteral=1e-6)),
                frequency=Expression(literal=Expression.Literal(floatLiteral=100e6)),
                amplitude=Expression(literal=Expression.Literal(floatLiteral=1.0)),
                phase=Expression(literal=Expression.Literal(floatLiteral=0.0)),
                shape=Shape(id=SHAPE_ID_RECT),
                hold=False,
            )
        ),
    )


def test_nested_if_command():
    with QiJob() as job:
        q = QiVariable(int)
        with If(q < 5):
            with If(q < 3):
                Assign(q, 2)
            with Else():
                Assign(q, 4)
        with Else():
            Assign(q, 20)

    assert len(job.commands) == 3
    assert job.commands[0].declareCommand == DeclareCommand(
        var=Variable(id=0), type=Type(scalar=Type.Scalar.Normal), static=False
    )
    assert job.commands[1].HasField("ifCommand")
    outer_if_cmd = job.commands[1].ifCommand
    assert len(outer_if_cmd.body) == 2
    assert outer_if_cmd.body[0].HasField("ifCommand")
    inner_if_cmd = outer_if_cmd.body[0].ifCommand
    assert len(inner_if_cmd.body) == 1
