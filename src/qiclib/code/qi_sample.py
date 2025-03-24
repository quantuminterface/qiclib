from __future__ import annotations

import json
import os
from collections.abc import MutableMapping, MutableSequence
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from qiclib.code.qi_var_definitions import _QiVariableBase
    from qiclib.hardware.controller import QiController
    from qiclib.hardware.unitcell import UnitCell


class QiSampleCell(MutableMapping):
    """QiSampleCell is the representation of a single qubit/cell and its properties.

    All necessary parameters to perform experiments can be stored here. For this
    purpose, the QiSampleCell can be used as a dictionary with user-defined keys.
    """

    def __init__(self, cell_id: int, cells_ref: QiSample):
        self.cell_id = cell_id
        self._cells_ref = cells_ref
        self._relevant_vars: set[_QiVariableBase] = set()

        self._properties: dict[str, Any] = {}

    def __len__(self):
        return len(self._properties)

    def __contains__(self, item):
        return item in self._properties

    def __getitem__(self, key):
        return self._properties[key]

    def __setitem__(self, key, value):
        self._properties[key] = value

    def __delitem__(self, key):
        del self._properties[key]

    def __iter__(self):
        return iter(self._properties)

    def update(self, *args, **kwargs: Any) -> None:
        self._properties.update(*args, **kwargs)

    def __call__(self, qic: QiController) -> UnitCell:
        return qic.cell[self.qic_cell]

    def __str__(self):
        return str(self._properties)

    @property
    def qic_cell(self):
        return self._cells_ref.cell_map[self.cell_id]

    def get_properties(self) -> dict[str, Any]:
        return self._properties.copy()


class QiSample(MutableSequence[QiSampleCell]):
    """Representation of an experiment sample and its properties.

    Property keys can be arbitrary strings, and property values can be anything.
    Set the keys using :python:`sample["property_key"] = property_value` and get the values
    the same way, i.e., :python:`property_value = sample["property_key"]`.

    Note that this class **cannot** be instantiated within a :class:`QiJob`.
    Instead, it must be defined outside one.
    Accessing samples defined here within a QiJob is still possible, however, using the :class:`QiCell` object:

    .. code-block:: python

        sample: QiSample = ...
        qic: QiController = ...
        sample["t1"] = 100e-6

        with QiJob() as job:
            q = QiCells(1)
            Wait(q[0], q[0]["t1"])

        job.run(
            qic, sample
        )  # Note that we pass the sample object here to make the value available in the job

    The :python:`QiSample` object is serializable to `JSON <https://www.json.org/>`_.
    Have a look at the :meth:`save` and :meth:`load` methods for more

    :param num: The number of cells/qubits this sample has.
    :param cell_map: On which QiController cells these are mapped, by default [0, 1, ..., num-1]
    :raises RuntimeError: When the Sample is used within a :class:`QiJob`
    """

    def __init__(self, num: int, cell_map: list[int] | None = None) -> None:
        self._cell_map = None

        self.cells: list[QiSampleCell] = []
        for x in range(num):
            self.cells.append(QiSampleCell(cell_id=x, cells_ref=self))

        self.cell_map = cell_map or list(range(num))

    def __getitem__(self, key):
        return self.cells[key]

    def __setitem__(self, key, value):
        self.cells[key] = value

    def __delitem__(self, key):
        del self.cells[key]

    def __len__(self):
        return len(self.cells)

    def insert(self, index, value):
        self.cells.insert(index, value)

    def __str__(self):
        return f"{self.__class__.__name__}(cells=[{', '.join(map(str, self.cells))}], cell_map={self._cell_map})"

    def _arrange_for_controller(self) -> list[QiSampleCell | None]:
        inverse: list[QiSampleCell | None] = [None] * (max(self.cell_map) + 1)
        for cell, qi_cell_index in enumerate(self.cell_map):
            inverse[qi_cell_index] = self[cell]
        return inverse

    @property
    def cell_map(self):
        return self._cell_map

    @cell_map.setter
    def cell_map(self, cell_map):
        if len(cell_map) != len(self):
            raise ValueError(
                "cell_map needs to have as many entries as the there are cells, but "
                f"{len(cell_map)} entries given and {len(self)} required!"
            )
        if len(set(cell_map)) != len(cell_map):
            raise ValueError("Duplicate values not allowed in cell_map!")
        if any(c < 0 for c in cell_map):
            raise ValueError("Cell indices inside cell_map cannot be negative!")
        self._cell_map = cell_map

    def to_dict(self) -> dict[str, Any]:
        properties = [cell.get_properties() for cell in self.cells]
        return {"cells": properties, "cell_map": self.cell_map}

    @classmethod
    def from_dict(cls, source: dict[str, Any]) -> QiSample:
        cells = source.get("cells")
        if cells is None:
            raise ValueError("Imported JSON string does not contain 'cells'.")
        sample = QiSample(len(cells))
        for i, cell in enumerate(cells):
            # legacy support
            if "properties" in cell:
                sample.cells[i].update(**cell["properties"])
            else:
                sample.cells[i].update(**cell)
        sample.cell_map = source.get("cell_map", list(range(len(cells))))
        print(sample)
        return sample

    def save(self, file_path: str | os.PathLike, overwrite: bool = False):
        """
        Save the sample to a file denoted by the :python:`file_path` argument in JSON format.

        :param file_path: Where to store the file
        :param overwrite: When true, allow overwriting an existing file.
        :raise FileExistsError: When overwrite is False and the file exists.
        """
        mode = "w" if overwrite is True else "x"

        with open(file_path, mode, encoding="utf-8") as file:
            json.dump(self.to_dict(), file)

    @classmethod
    def load(cls, file_path: str | os.PathLike) -> QiSample:
        """
        Loads the file at :python:`file_path`

        :param file_path: Where to look for the file
        """
        with open(file_path, encoding="utf-8") as file:
            return cls.from_dict(json.load(file))

    @classmethod
    def loads(cls, json_string: str) -> QiSample:
        """
        Loads the value given by the JSON-encoded string `json_string`

        :param json_string: The value, encoded as JSON
        """
        return cls.from_dict(json.loads(json_string))
