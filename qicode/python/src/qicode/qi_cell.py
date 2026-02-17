from collections.abc import Iterator, Sequence

from qicode.proto.cell_pb2 import Cell, Coupler
from qicode.qi_expression import QiCellProperty
from qicode.qi_job import QiJob


class QiCell:
    def __init__(self, index: int) -> None:
        self._cell = Cell(index=index)
        self._job = QiJob._current()

    def _proto(self) -> Cell:
        return self._cell

    def __getitem__(self, key: str) -> QiCellProperty:
        if QiJob._current() != self._job:
            raise RuntimeError(
                "Tried getting values for cells registered to other QiJob"
            )
        return QiCellProperty(self, key)

    def __str__(self) -> str:
        return f"QiCell({self._cell.index})"


class QiCells(Sequence[QiCell]):
    def __init__(self, num: int) -> None:
        self.cells = [QiCell(x) for x in range(num)]
        QiJob._current().register_cells(self.cells)

    def __contains__(self, value: object) -> bool:
        return value in self.cells

    def __iter__(self) -> Iterator[QiCell]:
        return iter(self.cells)

    def __len__(self) -> int:
        return len(self.cells)

    def __getitem__(self, index: int) -> QiCell:
        return self.cells[index]

    def __str__(self) -> str:
        return f"QiCells({len(self.cells)})"


class QiCoupler:
    def __init__(self, index: int) -> None:
        self._coupler = Coupler(index=index)

    def _proto(self) -> Coupler:
        return self._coupler

    def __str__(self) -> str:
        return f"QiCoupler({self._coupler.index})"


class QiCouplers(Sequence):
    def __init__(self, num: int) -> None:
        self.couplers = [QiCoupler(x) for x in range(num)]
        QiJob._current().register_couplers(self.couplers)

    def __contains__(self, value: object) -> bool:
        return value in self.couplers

    def __iter__(self) -> Iterator:
        return iter(self.couplers)

    def __len__(self) -> int:
        return len(self.couplers)

    def __getitem__(self, index):
        return self.couplers[index]

    def __str__(self) -> str:
        return f"QiCouplers({len(self.couplers)})"
