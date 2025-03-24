from __future__ import annotations

from typing import Any


class QiResult:
    """Result of an experiment. Can be accessed via :python:`job.cells[cell_index].data("result name")`.
    Where :python:`cells` denotes a :class:`QiCells` object and :python:`cell_index` an integer.

    The actual data can be retrieved as a numpy array using the :meth:`get` Method

    Example
    -------

    .. code-block:: python

        qic: QiController = ...
        sample: QiSample = ...

        with QiJob() as job:
            q = QiCells(1)
            Readout(q[0], save_to="result")

        job.run(qic, sample, averages=1000)
        data = job.cells[0].data("result")

    :param name: The name of the variable, by default None
    """

    def __init__(self, name: str | None = None) -> None:
        self._cell = None
        self.data = None
        self.recording_count = 0
        self.name: str = "" if name is None else name

    def get(self) -> Any:
        """gets the data of the result, commonly as a numpy array

        :return: The data of the experiment
        """
        return self.data

    def __str__(self) -> str:
        return f'QiResult("{self.name}")'
