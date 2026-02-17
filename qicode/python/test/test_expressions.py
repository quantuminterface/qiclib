from qicode import Assign, QiCells, QiJob, QiVariable
from qicode.proto import AssignCommand, Cell, CellProperty, Expression, Variable


def test_qi_cell_property():
    with QiJob() as job:
        q = QiCells(1)
        v = QiVariable(int)
        Assign(v, q[0]["prop"] + 1)

    assert job.commands[1].assignCommand == AssignCommand(
        destination=Variable(id=0),
        value=Expression(
            binary=Expression.Binary(
                lhs=Expression(property=CellProperty(cell=Cell(index=0), name="prop")),
                op=Expression.Binary.Operator.Plus,
                rhs=Expression(literal=Expression.Literal(intLiteral=1)),
            )
        ),
    )
