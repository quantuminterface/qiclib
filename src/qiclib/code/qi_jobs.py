# Copyright © 2017-2023 Quantum Interface (quantuminterface@ipe.kit.edu)
# Richard Gebauer, IPE, Karlsruhe Institute of Technology
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
This is the main module of QiCode.
Here, all important commands write QiPrograms are defined.
"""
import os
from abc import abstractmethod
import json
from typing import (
    Dict,
    List,
    Callable,
    Optional,
    Union,
    Set,
    Any,
    Type,
    Iterable,
)
from typing_extensions import Protocol
import functools
import warnings

import numpy as np

import qiclib.packages.utility as util
from qiclib.hardware import digital_trigger
from qiclib.hardware.taskrunner import TaskRunner
from qiclib.experiment.qicode.data_provider import DataProvider
from qiclib.experiment.qicode.data_handler import DataHandler
from qiclib.code.qi_seq_instructions import SequencerInstruction
from qiclib.code.qi_var_definitions import (
    _QiVariableBase,
    _QiCalcBase,
    _QiConstValue,
    QiCellProperty,
    QiExpression,
    QiVariableSet,
    QiCondition,
)
from qiclib.code.qi_pulse import QiPulse
from qiclib.code.qi_visitor import (
    QiCMContainedCellVisitor,
    QiResultCollector,
    QiVarInForRange,
)
from qiclib.code.qi_prog_builder import QiProgramBuilder
from qiclib.code.qi_types import (
    QiType,
    QiPostTypecheckVisitor,
    QiTypeFallbackVisitor,
    _TypeDefiningUse,
)


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

    def __init__(self, name: Optional[str] = None) -> None:
        self._cell = None
        self.data = None
        self.recording_count = 0
        self.name: str = "" if name is None else name

    def get(self) -> np.ndarray:
        """gets the data of the result as a numpy array

        :return: The data of the experiment
        """
        return np.array(self.data)

    def __str__(self) -> str:
        return f'QiResult("{self.name}")'


class QiCommand:
    """Base class of every Job command.
    Provides _relevant_cells, containing every cell used for the execution of the command.
    Provides _associated_variable_set, containing every variable needed for the execution of the command.
    """

    def __init__(self) -> None:
        self._associated_variable_set = QiVariableSet()
        self._relevant_cells: Set[QiCell] = set()

    @abstractmethod
    def accept(self, visitor, *input):
        raise RuntimeError(
            f"{self.__class__} doesn't implement `accept`. This is a bug."
        )

    def is_variable_relevant(self, variable: _QiVariableBase) -> bool:
        return variable in self._associated_variable_set

    def add_associated_variable(self, x):
        if isinstance(x, _QiVariableBase):
            self._associated_variable_set.add(x)

    def __str__(self) -> str:
        return "cQiCommand"

    def _stringify(self) -> str:
        raise NotImplementedError(f"_stringify not implemented for {repr(self)}")


_QiJobReference = None


def _add_cmd_to_job(cmd: QiCommand):
    if _QiJobReference is None:
        raise RuntimeError("Can not use command outside QiJob context manager.")
    _QiJobReference._add_command(cmd)


def _set_job_reference(job):
    """Used for testing purposes"""
    # pylint: disable=global-statement
    global _QiJobReference
    _QiJobReference = job


def _delete_job_reference():
    """Used for testing purposes"""
    # pylint: disable=global-statement
    global _QiJobReference
    _QiJobReference = None


class QiCell:
    """A QiCell is an abstract representation of the qubit/cell the program is run on.
    Usually, a single :python:`QiCell` is not instantiated, but instead a :class:`QiCells` object.
    For a single :python:`QiCell`, use instead :python:`QiCells(1)`

    A :python:`QiCell` must be instantiated inside within a :class:`QiJob` context.

    The :python:`QiCell` object can be used to get properties that are defined on :class:`QiSamples <QiSample>`.
    For this, index the :python:`QiCell` object using the name of the property:

    .. code-block:: python

        q: QiCell = ...
        t1_time = q["t1"]

    The actual value for the accessed property (in the example above, the T1 time) is filled in when executing a
    :class:`QiJob` and providing the actual sample.

    **Tasks of the QiCell**:

    - Saves the pulses needed for program execution.
    - Provides a dictionary functionality to define commonly used durations/properties.
    - Implements a Sequencer object, which contains the assembler program after compilation.

    :param cellID: A unique ID
    :raises RuntimeError: When the :python:`QiCell` is instantiated outside a `QiJob`
    """

    def __init__(self, cellID: int):
        if not isinstance(_QiJobReference, QiJob):
            raise RuntimeError("QiCell can't be used outside of QiJob.")

        self.cellID = cellID
        self.manipulation_pulses: List[QiPulse] = []
        self.digital_trigger_sets: List[digital_trigger.TriggerSet] = []
        self.flux_pulses: List[QiPulse] = []
        self.readout_pulses: List[QiPulse] = []
        self._result_container: Dict[str, QiResult] = {}
        # The order in which recorded values are assigned to which result container
        self._result_recording_order: List[QiResult] = []
        self._unresolved_property: Set[QiCellProperty] = set()
        self._job_ref = _QiJobReference
        self._relevant_vars: Set[_QiVariableBase] = set()

        # These attributes are determined by dataflow analyses
        self._initial_manip_freq: float = None
        self._initial_readout_freq: float = None
        self._initial_rec_offset: float = None

        self._rec_length: Union[int, float, QiCellProperty] = None

        self._properties: Dict[QiCellProperty, Any] = {}

    def __getitem__(self, key):
        if _QiJobReference != self._job_ref:
            raise RuntimeError(
                "Tried getting values for cells registered to other QiJob"
            )

        prop = self._properties.get(key, QiCellProperty(self, key))

        if isinstance(prop, QiCellProperty):
            self._unresolved_property.add(key)
        return prop

    def __setitem__(self, key, value):
        if _QiJobReference != self._job_ref:
            raise RuntimeError(
                "Tried setting values for cells registered to other QiJob"
            )
        self._properties[key] = value

    def __call__(self, qic):
        return qic.cell[self.qic_cell]

    def get_properties(self):
        return self._properties.copy()

    def add_pulse(self, pulse: QiPulse):
        if pulse not in self.manipulation_pulses:
            self.manipulation_pulses.append(pulse)

        if len(self.manipulation_pulses) > 13:
            raise RuntimeError("Too many pulses in use")

        return self.manipulation_pulses.index(pulse) + 1  # index 0 and 15 are reserved

    def add_digital_trigger(self, trig_set: digital_trigger.TriggerSet):
        if trig_set not in self.digital_trigger_sets:
            self.digital_trigger_sets.append(trig_set)

        if len(self.digital_trigger_sets) > 3:
            raise RuntimeError(
                "Too many digital trigger sets in use (Only three sets are available)"
            )

        return self.digital_trigger_sets.index(trig_set) + 1  # index 0 is reserved

    @property
    def initial_manipulation_frequency(self):
        if self._initial_manip_freq is None:
            if len(self.manipulation_pulses) > 0:
                warnings.warn(
                    "Manipulation pulses without frequency given, using 90 MHz."
                )
            return 90e6  # Default frequency
        freq = self._initial_manip_freq
        return freq() if isinstance(freq, QiCellProperty) else freq

    def add_recording_length(self, length):
        if self._rec_length is None:
            self._rec_length = length
        elif (
            not self._rec_length._equal_syntax(length)
            if isinstance(self._rec_length, QiExpression)
            else self._rec_length != length
        ):
            raise RuntimeError(
                f"Cell {self.cellID}: Multiple definitions of recording length used."
            )

    def add_readout_pulse(self, pulse: QiPulse):
        if pulse not in self.readout_pulses:
            self.readout_pulses.append(pulse)

        if len(self.readout_pulses) > 13:
            raise RuntimeError("Too many pulses in use")

        return self.readout_pulses.index(pulse) + 1  # index 0 and 15 are reserved

    @property
    def initial_readout_frequency(self):
        if self._initial_readout_freq is None:
            if len(self.readout_pulses) > 0:
                warnings.warn("Readout pulses without frequency given, using 30 MHz.")
            return 30e6  # Default frequency
        freq = self._initial_readout_freq
        return freq() if isinstance(freq, QiCellProperty) else freq

    @property
    def recording_length(self):
        """the length of the recording pulse"""
        if self._rec_length is not None:
            return (
                self._rec_length()
                if isinstance(self._rec_length, QiCellProperty)
                else self._rec_length
            )

        return 0

    @property
    def initial_recording_offset(self):
        """the recording offset in seconds"""
        if self._initial_rec_offset is not None:
            return (
                self._initial_rec_offset()
                if isinstance(self._initial_rec_offset, QiCellProperty)
                else self._initial_rec_offset
            )

        return 0

    def get_result_container(self, result: str) -> QiResult:
        if result in self._result_container:
            return self._result_container[result]  # was already added
        else:
            box = QiResult(result)
            box._cell = self
            self._result_container[result] = box
            return box

    def add_variable(self, var: _QiVariableBase):
        self._relevant_vars.add(var)

    def get_number_of_recordings(self):
        return len(self._result_recording_order)

    def set_default_readout(self, pulse):
        pass

    def reset(self):
        for container in self._result_container.values():
            container.data = []

    def data(
        self, name: Optional[str] = None
    ) -> Union[Dict[str, np.ndarray], np.ndarray]:
        """
        Returns the data after running an experiment.

        When calling this function without a name, i.e., calling :python:`cell.data()`,
        returns a dictionary containing the results as numpy arrays.

        When calling this function with a name, i.e., calling :python:`cell.data("result_name")`,
        returns the result referenced by :python:`name`

        :param name: The name of the data
        :return: A single result, or a dictionary of result names mapped to results.
        """
        if name is None:
            result_dict = {}
            for key, container in self._result_container.items():
                result_dict.update({key: container.get()})
            return result_dict

        else:
            return self._result_container[name].get()

    def _resolve_properties(self, len_dict: Dict[QiCellProperty, Any]):
        keys = list(self._unresolved_property)

        missing_keys = self._unresolved_property.difference(len_dict.keys())
        if missing_keys:
            raise RuntimeError(
                f"Cell {self.cellID}: Not all properties for job could be resolved. "
                f"Missing properties: {missing_keys}"
            )

        for key in keys:
            self._properties[key] = len_dict[key]

    @property
    def has_unresolved_properties(self):
        return len(self._unresolved_property) > 0

    def _get_unresolved_properties(self):
        return [
            key
            for key in list(self._unresolved_property)
            if self._properties.get(key) is None
        ]

    def __str__(self) -> str:
        return f"QiCell({self.cellID})"


class QiCells:
    """
    QiCells encapsulates multiple :class`QiCell` objects.
    It is a list-like object where the individual cells can be accessed using the
    index operator, i.e.

    .. code-block:: python

        cells = QiCells(5)
        cell0: QiCell = cells[0]
        cell3: QiCell = cells[3]


    :param num: The number of cells to create
    :raises RuntimeError: When the :python:`QiCells` object is instantiated outside a :python:`QiJob`
    """

    def __init__(self, num: int) -> None:
        if not isinstance(_QiJobReference, QiJob):
            raise RuntimeError(
                "QiCells can only be used within QiJob description. "
                + "If you try to create a sample object, use the new QiSample instead."
            )

        self.cells = [QiCell(x) for x in range(num)]
        _QiJobReference._register_cells(self.cells)

    def __getitem__(self, key):
        return self.cells[key]

    def __len__(self):
        return len(self.cells)


class QiCoupler:
    def __init__(self, associated_unit_cell: QiCell, coupling_index: int):
        self.associated_unit_cell = associated_unit_cell
        self.coupling_index = coupling_index
        self.coupling_pulses: List[QiPulse] = []

    def add_pulse(self, pulse: QiPulse):
        self.coupling_pulses.append(pulse)
        return len(self.coupling_pulses)


class QiCouplers:
    """
    Declares :py:`count` couplers.

    Couplers are capable of playing flux pulses.
    In the context of QiCode, flux Pulses are longer but do not have Digital Up-Conversion.

    You can instantiate up to twice the amount of digital Unit Cells.

    .. warning::
        You must first instantiate Digital Unit Cells before you can instantiate Couplers.

    .. code-block:: python

        with QiJob() as job:
            q = QiCells(6)
            c = QiCouplers(12)
    """

    def __init__(self, count: int):
        if not isinstance(_QiJobReference, QiJob):
            raise RuntimeError("QiCouplers can only be used within QiJob description.")

        if len(_QiJobReference.cells) == 0:
            raise RuntimeError(
                "No cells in the QiJob found."
                "Note that couplers must be instantiated after cells."
            )

        self._couplers = [
            QiCoupler(_QiJobReference.cells[i // 2], i % 2) for i in range(count)
        ]
        _QiJobReference._register_couplers(self._couplers)

    def __getitem__(self, key):
        return self._couplers[key]

    def __len__(self):
        return len(self._couplers)


class QiSampleCell:
    """QiSampleCell is the representation of a single qubit/cell and its properties.

    All necessary parameters to perform experiments can be stored here. For this
    purpose, the QiSampleCell can be used as a dictionary with user-defined keys.
    """

    def __init__(self, cellID: int, cells_ref: "QiSample"):
        self.cellID = cellID
        self._cells_ref = cells_ref
        self._relevant_vars: Set[_QiVariableBase] = set()

        self._properties: Dict[str, Any] = {}

    def __getitem__(self, key):
        return self._properties[key]

    def __setitem__(self, key, value):
        self._properties[key] = value

    def __call__(self, qic):
        return qic.cell[self.qic_cell]

    @property
    def qic_cell(self):
        return self._cells_ref.cell_map[self.cellID]

    def get_properties(self):
        return self._properties.copy()

    def __str__(self) -> str:
        return f"QiSampleCell({self.cellID})"

    def _export(self):
        return {"properties": self.get_properties()}

    def _import(self, prop_dict, index):
        if prop_dict is None:
            warnings.warn(
                f"Imported JSON string does not contain 'properties' for cell[{index}]."
            )
            return

        self._properties.update(prop_dict)


class QiSample:
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

        job.run(qic, sample) # Note that we pass the sample object here to make the value available in the job

    The :python:`QiSample` object is serializable to `JSON <https://www.json.org/>`_.
    Have a look at the :meth:`save` and :meth:`load` methods for more

    :param num: The number of cells/qubits this sample has.
    :param cell_map: On which QiController cells these are mapped, by default [0, 1, ..., num-1]
    :raises RuntimeError: When the Sample is used within a :class:`QiJob`
    """

    def __init__(self, num: int, cell_map: Optional[List[int]] = None) -> None:
        self._cell_map = None
        if _QiJobReference is not None:
            raise RuntimeError(
                "QiSample can only be used outside of QiJob to define sample "
                "properties. Inside a QiJob, use QiCells as placeholder for the "
                "qubits/cells instead."
            )

        self.cells: List[QiSampleCell] = []
        for x in range(num):
            self.cells.append(QiSampleCell(cellID=x, cells_ref=self))

        self.cell_map = cell_map or list(range(num))

    def __getitem__(self, key):
        return self.cells[key]

    def __len__(self):
        return len(self.cells)

    def __str__(self):
        return (
            f"QiSample({len(self.cells)}, cell_map=[{','.join(map(str, self.cell_map))}]):\n"
            + "\n".join(
                [
                    f"[{i}]: {json.dumps(props['properties'], indent=2)}"
                    for i, props in enumerate(self._export()["cells"])
                ]
            )
        )

    def _arrange_for_controller(self) -> List[Optional[QiSampleCell]]:
        inverse: List[Optional[QiSampleCell]] = [None] * (max(self.cell_map) + 1)
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

    def _export(self):
        properties = [cell._export() for cell in self.cells]
        return {"cells": properties, "cell_map": self.cell_map}

    def _import(self, jsn_string):
        jsn_loaded = json.loads(jsn_string)
        self._evaluate_import(jsn_loaded.get("cells", None))
        self.cell_map = jsn_loaded.get("cell_map", self.cell_map)

    def save(self, file_path: Union[str, os.PathLike], overwrite: bool = False):
        """
        Save the sample to a file denoted by the :python:`file_path` argument in JSON format.

        :param file_path: Where to store the file
        :param overwrite: When true, allow overwriting an existing file.
        :raise FileExistsError: When overwrite is False and the file exists.
        """
        mode = "w" if overwrite is True else "x"

        with open(file_path, mode, encoding="utf-8") as file:
            json.dump(self._export(), file)

    def load(self, file_path: Union[str, os.PathLike]):
        """
        Loads the file at :python:`file_path`
        and assigns all properties of the loaded file to this :class:`QiSample` object.

        :param file_path: Where to look for the file
        """
        with open(file_path, "r", encoding="utf-8") as file:
            self._import(file.read())

    def _evaluate_import(self, sample):
        if sample is None:
            warnings.warn("Imported JSON string does not contain 'cells'.")
            return
        if len(sample) != len(self):
            raise ValueError(
                f"Imported JSON contains {len(sample)} sample cells but {len(self)} "
                "expected."
            )

        for i in range(0, len(self)):
            self.cells[i]._import(sample[i].get("properties", None), i)


class _JobDescription:
    """Saves experiment descriptions and handles storage of commands"""

    def __init__(self):
        self._commands: List[QiCommand] = []
        self._ContextStack: List[List[QiCommand]] = []

    def __getitem__(self, key):
        return self._commands[key]

    def __len__(self):
        return len(self._commands)

    def add_command(self, command):
        """Checks current command for used cells and raises error, if cells are not defined for current QiJob"""
        if isinstance(command, QiCellCommand):
            if _QiJobReference != command.cell._job_ref:
                raise RuntimeError("Cell not defined for current job")

        self._commands.append(command)

    def open_new_context(self):
        """Saves current commands in a stack and clears command list"""
        self._ContextStack.append(self._commands.copy())
        self._commands = []

    def close_context(self) -> List[QiCommand]:
        """returns the current command list, and loads the commands from top of stack"""
        current_commands = self._commands.copy()
        self._commands = self._ContextStack.pop()

        return current_commands

    def reset(self):
        self._commands = []
        self._ContextStack = []


class QiCellCommand(QiCommand):
    """
    Cell commands are commands using only one cell, such as Play and Wait commands.

    :param cell: The target cell
    """

    def __init__(self, cell: QiCell):
        super().__init__()
        self.cell = cell
        self._relevant_cells.add(cell)

    def accept(self, visitor, *input):
        return visitor.visit_cell_command(self, *input)


class QiVariableCommand(QiCommand):
    """Base class of variable commands cQiDeclare and cQiAssign"""

    def __init__(self, var: _QiVariableBase):
        super().__init__()
        self.var = var

    def accept(self, visitor, *input):
        return visitor.visit_variable_command(self, *input)


class QiTriggerCommand(Protocol):
    """
    Common interface for all commands that can cause a trigger.
    """

    trigger_index: int


class cQiDigitalTrigger(QiCellCommand, QiTriggerCommand):
    """Command generated by :meth:`DigitalTrigger`"""

    def __init__(self, cell: QiCell, outputs: List[int], length: float):
        super().__init__(cell)
        self.cell = cell
        self.trigger_index = cell.add_digital_trigger(
            digital_trigger.TriggerSet(
                duration=length, outputs=outputs, continuous=False
            )
        )
        self.length = length

    def _stringify(self) -> str:
        return f"DigitalTrigger({self.cell}, {self.trigger_index}, {self.length})"


class cQiWait(QiCellCommand):
    """Command generated by :meth:`Wait`"""

    def __init__(self, cell, length: Union[QiExpression, QiCellProperty]):
        from .qi_types import _TypeDefiningUse

        super().__init__(cell)
        self._length = length

        if isinstance(length, _QiVariableBase):
            self.add_associated_variable(length)
        elif isinstance(length, _QiCalcBase):
            for variable in length.contained_variables:
                self.add_associated_variable(variable)

        if isinstance(length, QiExpression):
            length._type_info.set_type(QiType.TIME, _TypeDefiningUse.WAIT_COMMAND)

    @property
    def length(self):
        return (
            self._length() if isinstance(self._length, QiCellProperty) else self._length
        )

    def _stringify(self) -> str:
        return f"Wait({self.cell}, {self._length})"


class _cQiPlay_base(QiCellCommand, QiTriggerCommand):
    """Base class of Play commands.
    Saves pulses, trigger_index and adds pulse variables to associated variable set
    """

    def __init__(self, cell, pulse: QiPulse):
        super().__init__(cell)
        self.pulse = pulse

        # default False; Set True for certain commands when unrolling a loop with TimingVariable == 1 cycle
        self._var_single_cycle_trigger = False

        for variable in self.pulse.variables:
            self.add_associated_variable(variable)

        # length of command might differ from pulse length
        self._length: Union[float, _QiVariableBase, QiCellProperty] = self.pulse.length

        self.trigger_index = 0

    @property
    def length(self):
        return (
            self._length
            if not isinstance(self._length, QiCellProperty)
            else self._length()
        )

    @length.setter
    def length(self, value):
        self._length = value


class cQiPlay(_cQiPlay_base):
    """Command generated by Play()"""

    def __init__(self, cell, pulse: QiPulse):
        super().__init__(cell, pulse)
        self.trigger_index = cell.add_pulse(pulse)

    def _stringify(self) -> str:
        return f"Play({self.cell}, {self.pulse._stringify()})"


class cQiPlayFlux(_cQiPlay_base):
    """Command generated by PlayFlux()"""

    def __init__(self, coupler: QiCoupler, pulse: QiPulse) -> None:
        super().__init__(coupler.associated_unit_cell, pulse)
        self.coupler = coupler
        self.trigger_index = coupler.add_pulse(pulse)

    def _stringify(self) -> str:
        return f"PlayFlux({self.coupler}, {self.pulse._stringify()})"


class cQiPlayReadout(_cQiPlay_base):
    """Command generated by :meth:`PlayReadout`"""

    def __init__(self, cell, pulse) -> None:
        super().__init__(cell, pulse)
        self.recording: Union[None, cQiRecording] = None
        self.trigger_index = cell.add_readout_pulse(pulse)

    @property
    def length(self):
        length = (
            self._length
            if not isinstance(self._length, QiCellProperty)
            else self._length()
        )

        # if Recording is defined and length is not defined by variable, compare both lengths
        if isinstance(self.recording, cQiRecording) and not isinstance(
            self._length, _QiVariableBase
        ):
            return max(length, self.recording.length)
        return length

    @length.setter
    def length(self, value):
        self._length = value
        if isinstance(self.recording, cQiRecording):
            self.recording.length = value

    @property
    def uses_state(self):
        return self.recording is not None and self.recording.uses_state

    def _stringify(self) -> str:
        return f"PlayReadout({self.cell}, {self.pulse._stringify()})"


class cQiRotateFrame(_cQiPlay_base):
    """Command generated by :meth:`RotateFrame`"""

    def __init__(self, cell, angle: float):
        # Negate phase because frame needs to be shifted in the opposite direction
        # than pulses -> want to shift the state on bloch sphere but shift the frame
        pulse = QiPulse(0, phase=-1 * angle)
        pulse.shift_phase = True  # Special property to make phase offset persistant
        super().__init__(cell, pulse)
        self.trigger_index = cell.add_pulse(pulse)
        self.length = util.conv_cycles_to_time(1)  # command needs exactly one cycle
        self.angle = angle

    def _stringify(self) -> str:
        return f"RotateFrame({self.cell}, {self.angle})"


class cQiSync(QiCommand):
    """Command generated by :meth:`Sync`"""

    def __init__(self, cells: List[QiCell]):
        super().__init__()
        self._relevant_cells.update(cells)

    def accept(self, visitor, *input):
        return visitor.visit_sync_command(self, *input)

    def _stringify(self) -> str:
        return (
            "Sync("
            + ", ".join(
                [
                    f"{cell}"
                    for cell in sorted(self._relevant_cells, key=lambda c: c.cellID)
                ]
            )
            + ")"
        )


class cQiRecording(QiCellCommand):
    """Command generated by Recording()"""

    def __init__(
        self,
        cell: QiCell,
        save_to: Union[str, _QiVariableBase, None],
        state_to: Union[_QiVariableBase, None],
        length: Union[int, float, QiCellProperty],
        offset: Union[int, float, QiExpression],
        toggleContinuous: Optional[bool] = None,
    ):
        from .qi_types import _TypeDefiningUse

        super().__init__(cell)
        self.result_box = None
        self.var = None

        if (
            isinstance(length, QiExpression)
            and length.type == QiType.STATE
            or isinstance(offset, QiExpression)
            and offset.type == QiType.STATE
        ):
            raise RuntimeError("State variable can only be used at save_to parameter.")

        if isinstance(state_to, _QiVariableBase):
            state_to._type_info.set_type(
                QiType.STATE, _TypeDefiningUse.RECORDING_SAVE_TO
            )
            self.add_associated_variable(state_to)
            self.var = state_to

        self.save_to = save_to

        assert not isinstance(
            save_to, QiResult
        )  # support for QiResult as parameter was removed.
        if isinstance(save_to, _QiVariableBase):
            # TODO This should be deprecated and turned into new result variable
            # to handle I/Q values instead if necessary -> consistency
            if self.var is not None:
                raise RuntimeError("Cannot pass variable to state_to and save_to.")
            save_to._type_info.set_type(
                QiType.STATE, _TypeDefiningUse.RECORDING_SAVE_TO
            )
            self.add_associated_variable(save_to)
            self.var = save_to
        elif isinstance(save_to, str):
            self.result_box = cell.get_result_container(
                save_to
            )  # container might have been added to cell before
            self.save_to = save_to

        cell.add_recording_length(length)
        self._length = length
        if isinstance(self._length, QiExpression):
            self._length._type_info.set_type(
                QiType.TIME, _TypeDefiningUse.RECORDING_OFFSET_EXPRESSION
            )

        self._offset: QiExpression = QiExpression._from(offset)
        self._offset._type_info.set_type(
            QiType.TIME, _TypeDefiningUse.RECORDING_OFFSET_EXPRESSION
        )
        for var in self._offset.contained_variables:
            var._relevant_cells.add(cell)

        self.toggleContinuous = toggleContinuous

        self.follows_readout = False

        try:
            cmd = _QiJobReference.commands[-1]
            if (
                isinstance(cmd, cQiPlayReadout) and cmd.cell == self.cell
            ):  # Warning if previous cmd is readout but different cell
                self.follows_readout = True
                cmd.recording = self
                cmd._associated_variable_set.update(self._associated_variable_set)
        except IndexError:
            pass

    @property
    def uses_state(self):
        return len(self._associated_variable_set) > 0

    @property
    def length(self):
        return (
            self._length() if isinstance(self._length, QiCellProperty) else self._length
        )

    @length.setter
    def length(self, value):
        self._length = value

    @property
    def offset(self):
        return (
            self._offset() if isinstance(self._offset, QiCellProperty) else self._offset
        )

    def _stringify_args(self) -> str:
        """Determines non-default args to explicitly stringify"""
        arg_strings = [str(self.cell), str(self._length)]

        if not (
            isinstance(self._offset, _QiConstValue) and self._offset._given_value == 0
        ):
            arg_strings.append(f"offset={self._offset}")

        if self.result_box is not None:
            arg_strings.append(f'save_to="{self.result_box.name}"')

        if self.var is not None:
            arg_strings.append(f"state_to={self.var}")

        if self.toggleContinuous is not None:
            arg_strings.append(f"toggleContinuous={self.toggleContinuous}")

        return ", ".join(arg_strings)

    def _stringify(self) -> str:
        return f"Recording({self._stringify_args()})"


class cQiStore(QiCellCommand):
    """Command generated by :meth:`Store`"""

    def __init__(self, cell, store_var: _QiVariableBase, save_to: QiResult):
        super().__init__(cell)
        self.store_var = store_var
        self.save_to = save_to

        self.add_associated_variable(store_var)

    def _stringify(self) -> str:
        return f"Store({self.cell}, {self.store_var}, {self.save_to})"


class cQiAssign(QiVariableCommand):
    """Command generated by :meth:`Assign`"""

    def __init__(self, dst: _QiVariableBase, value: Union[QiExpression, int, float]):
        from .qi_types import (
            _TypeConstraintReasonQiCommand,
            _IllegalTypeReason,
            _add_equal_constraints,
        )

        if not isinstance(dst, _QiVariableBase):
            raise TypeError("Target of Assign can only be a QiVariable.")

        super().__init__(dst)

        self._value = QiExpression._from(value)

        dst._type_info.add_illegal_type(QiType.STATE, _IllegalTypeReason.ASSIGN)
        _add_equal_constraints(
            QiType.NORMAL, _TypeConstraintReasonQiCommand(cQiAssign), self._value, dst
        )
        _add_equal_constraints(
            QiType.TIME, _TypeConstraintReasonQiCommand(cQiAssign), self._value, dst
        )

        for variable in self.value.contained_variables:
            self.add_associated_variable(variable)

    @property
    def value(self):
        return self._value

    def accept(self, visitor, *input):
        return visitor.visit_assign_command(self, *input)

    def _stringify(self) -> str:
        return f"Assign({self.var}, {self._value})"


class cQiDeclare(QiVariableCommand):
    """Command generated by initialization of new QiVariable"""

    def __init__(self, dst: _QiVariableBase) -> None:
        super().__init__(var=dst)

    def accept(self, visitor, *input):
        return visitor.visit_declare_command(self, *input)

    def _stringify(self) -> str:
        return f"v{self.var.str_id} =  {self.var}"


class cQiASM(QiCommand):
    def __init__(self, cells: QiCell, instr: SequencerInstruction, cycles: int):
        super().__init__()
        self._relevant_cells.add(cells)
        self.asm_instruction = instr
        self.cycles = cycles

    def accept(self, visitor, *input):
        return visitor.visit_asm_command(self, *input)

    def _stringify(self) -> str:
        return f"ASM({self.asm_instruction.get_riscv_instruction()})"


class cQiMemStore(QiCommand):
    def __init__(self, cell: QiCell, addr: int, value):
        super().__init__()
        self._relevant_cells.add(cell)
        self.addr = addr
        self.value = value

    def accept(self, visitor, *input):
        return visitor.visit_mem_store_command(self, *input)

    def _stringify(self):
        cell_str = ", ".join(list(map(lambda x: f"{x}", self._relevant_cells)))
        return f"cQiMemStore({cell_str}, {self.addr}, {self.value})"


class QiContextManager(QiCommand):
    """Base Class for If, Else, ForRange and Parallel.
    Defines functions for storing commands."""

    def __init__(self) -> None:
        super().__init__()
        self.body: List[QiCommand] = []

    def __enter__(self):
        _QiJobReference._open_new_context()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.body = _QiJobReference._close_context()
        _QiJobReference._add_command(self)

    def accept(self, visitor, *input):
        return visitor.visit_context_manager(self, *input)


class If(QiContextManager):
    """
    Add conditional logic to the program.
    If multiple cells are used inside the body, a synchronization between the cells takes place before the If.

    :param condition: The condition to check

    Example
    -------

    .. code-block:: python

        with QiJob() as job:
            q = QiCells(1)
            x = QiIntVariable(1)
            with If(x > 1):
                ... # won't be executed

    The If statement is most commonly used to react to qubit states in real-time:

    .. code-block:: python

        from qiclib import jobs

        with QiJob() as job:
            q = QiCells(1)
            state = QiStateVariable()
            jobs.Readout(q[0], state_to=state)
            with If(state = 0):
                ... # Apply some conditional logic based on the qubit state
    """

    def __init__(self, condition: Optional[QiCondition] = None):
        super().__init__()
        self._else_body: List[QiCommand] = []
        if condition is None:
            raise RuntimeError("No QiCondition given")
        self.condition = condition

        for variable in condition.contained_variables:
            self.add_associated_variable(variable)

    def add_else_body(self, else_body):
        self._else_body = else_body.copy()

    def is_followed_by_else(self) -> bool:
        return len(self._else_body) != 0

    def accept(self, visitor, *input):
        return visitor.visit_if(self, *input)

    def _stringify(self) -> str:
        return f"If({self.condition})"


class Else(QiContextManager):
    """
    Adds Conditional logic if the preceding :class:`If` command evaluates to false.

    :raises RuntimeError: When the preceeding command is not an :python:`If` command

    Example
    -------
    .. code-block:: python

        from qiclib import jobs

        with QiJob() as job:
            q = QiCells(1)
            state = QiStateVariable()
            jobs.Readout(q[0], state_to=state)
            with If(state = 0):
                ... # Apply some conditional logic based on the qubit state
            with Else():
                ... # State is 1

    """

    def __enter__(self):
        self.if_cmd = _QiJobReference.commands[-1]

        if not isinstance(self.if_cmd, If):
            raise RuntimeError("Else is not preceded by If")

        _QiJobReference._open_new_context()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.if_cmd.add_else_body(_QiJobReference._close_context())


class Parallel(QiContextManager):
    """Pulses defined in body are united in one trigger command."""

    def __init__(self):
        super().__init__()
        self.entries: List[List[QiCommand]] = []

    def __exit__(self, exception_type, exception_value, traceback):
        temp = _QiJobReference._close_context()
        self.body += temp  # So visitors also find commands in Parallel blocks.
        self.entries.append(temp)

        containing_cells = QiCMContainedCellVisitor()
        for command in temp:
            if not isinstance(
                command,
                (
                    cQiPlay,
                    cQiPlayReadout,
                    cQiPlayFlux,
                    cQiRotateFrame,
                    cQiRecording,
                    cQiWait,
                    cQiDigitalTrigger,
                ),
            ):
                raise TypeError("Type not allowed inside Parallel()", command)
            if (
                isinstance(command, (cQiRecording, cQiPlayReadout))
                and command.uses_state
            ):
                raise RuntimeError("Can not save to state variable inside Parallel")

            try:
                if hasattr(command, "length") and isinstance(
                    command.length, _QiVariableBase
                ):
                    self._associated_variable_set.add(command.length)
            except KeyError:
                pass  # length was QiCellProperty
            command.accept(containing_cells)

        self._relevant_cells.update(containing_cells.contained_cells)

        # If previous command is also parallel, combine by adding another parallel entry at previous command
        try:
            cmd = _QiJobReference.commands[-1]
            if isinstance(cmd, Parallel) and len(cmd.entries) < 2:
                cmd.entries.append(temp)
                cmd._associated_variable_set.update(self._associated_variable_set)
            else:
                _QiJobReference._add_command(self)
        except IndexError:
            _QiJobReference._add_command(self)

    class CmdTuple:
        def __init__(self, cmd: QiCommand, start: int, end: int, choke: bool = False):
            self.cmd = cmd
            self.start = start
            self.end = end
            self.choke_cmd = choke

    class TimeSlot:
        def __init__(self, cmd_tuples: List[Any], start, end):
            self.cmd_tuples: List[Parallel.CmdTuple] = cmd_tuples
            self.start: int = start
            self.end: int = end
            self.duration: float = 0.0

    def _clear_wait_commands(self, cmd_tuples: List[CmdTuple]):
        """Clears cQiWait commands from cmd_tuples, if any trigger command is also in cmd_tuples"""
        contains_pulse = False

        for cmd_tuple in cmd_tuples:
            if isinstance(cmd_tuple.cmd, _cQiPlay_base):
                contains_pulse = True
                break

        return [
            cmd_tuple
            for cmd_tuple in cmd_tuples
            if isinstance(cmd_tuple.cmd, _cQiPlay_base) or contains_pulse is False
        ]

    def _clear_choke_commands(self, cmd_tuples: List[CmdTuple]):
        """Clears choke commands, if at the same slot another Play or Readout command is present."""

        contains_play = False
        contains_readout = False

        for cmd_tuple in cmd_tuples:
            if isinstance(cmd_tuple.cmd, cQiPlay) and cmd_tuple.choke_cmd is False:
                contains_play = True
            elif (
                isinstance(cmd_tuple.cmd, cQiPlayReadout)
                and cmd_tuple.choke_cmd is False
            ):
                contains_readout = True

        if contains_play is False and contains_readout is False:
            return cmd_tuples

        cleared_tuples = []

        for cmd_tuple in cmd_tuples:
            # if play command is present skip choke command for play
            if isinstance(cmd_tuple.cmd, cQiPlay):
                if cmd_tuple.choke_cmd is True and contains_play:
                    continue

            # if PlayReadout command is present skip choke command for PlayReadout
            elif isinstance(cmd_tuple.cmd, cQiPlayReadout):
                if cmd_tuple.choke_cmd is True and contains_readout:
                    continue

            cleared_tuples.append(cmd_tuple)

        return cleared_tuples

    def _create_time_slots(self, annotated_bodies: List[List[CmdTuple]], max_end: int):
        time_slot_list: List[Parallel.TimeSlot] = []
        for start in range(0, max_end):
            time_slot = self.TimeSlot([], start, start)

            # find tuples with start time == start
            for cmd_list in annotated_bodies:
                for cmd_tuple in cmd_list:
                    if cmd_tuple.start == start:
                        time_slot.cmd_tuples.append(cmd_tuple)
                        time_slot.end = max(cmd_tuple.end, time_slot.end)
                        cmd_list.remove(cmd_tuple)
                        break  # next cmd_list

            # next start value, if nothing was found
            if len(time_slot.cmd_tuples) == 0:
                continue

            time_slot.cmd_tuples = self._clear_wait_commands(time_slot.cmd_tuples)
            time_slot.cmd_tuples = self._clear_choke_commands(time_slot.cmd_tuples)

            # Add Wait command, if previous end value < start
            try:
                prev_time_slot = time_slot_list[-1]
                if prev_time_slot.end < start:
                    length = util.conv_cycles_to_time(start - prev_time_slot.end)
                    new_wait = self.CmdTuple(
                        cQiWait(list(self._relevant_cells)[0], length),
                        start=prev_time_slot.end,
                        end=start,
                    )
                    time_slot_list.append(
                        self.TimeSlot([new_wait], prev_time_slot.end, start)
                    )
            except IndexError:
                pass

            # Adjust previous end time, if previous.end > start
            try:
                prev_time_slot = time_slot_list[-1]
                prev_time_slot.end = min(prev_time_slot.end, start)
            except IndexError:
                pass

            time_slot_list.append(time_slot)

        # Add final wait, if previous.end != max_end
        try:
            prev_time_slot = time_slot_list[-1]
            if prev_time_slot.end < max_end:
                length = util.conv_cycles_to_time(max_end - prev_time_slot.end)
                new_wait = self.CmdTuple(
                    cQiWait(list(self._relevant_cells)[0], length),
                    start=prev_time_slot.end,
                    end=max_end,
                )
                time_slot_list.append(
                    self.TimeSlot([new_wait], prev_time_slot.end, max_end)
                )
        except IndexError:
            pass

        # calculate duration of time slot
        for slot in time_slot_list:
            slot.duration = util.conv_cycles_to_time(slot.end - slot.start)

        return time_slot_list

    def _generate_command_body(self, cell, sequencer):
        """Combines the parallel sequences to one command body."""

        parallel_bodies: List[List[Parallel.CmdTuple]] = []

        max_end = 0

        # Generate annotated list of commands with start and end cycle
        for cmd_list in self.entries:
            commands: List[Parallel.CmdTuple] = []
            start: int = 0
            end: int = 0
            for cmd in cmd_list:
                var_pulse = False

                if cell not in cmd._relevant_cells:
                    continue  # skip commands for other cells

                if isinstance(cmd.length, _QiVariableBase):
                    reg = sequencer.get_var_register(cmd.length)

                    if reg.valid is False or reg.value is None:
                        raise RuntimeError(
                            "Variable inside parallel not initialised or invalidated"
                        )

                    length = reg.value

                    if isinstance(cmd, (cQiPlay, cQiPlayReadout)):
                        var_pulse = True
                else:
                    length = util.conv_time_to_cycles(cmd.length, "ceil")

                if length == 0:
                    continue  # skip commands with length 0

                if isinstance(cmd, cQiRecording) or (
                    isinstance(cmd, cQiPlayReadout)
                    and isinstance(cmd.recording, cQiRecording)
                ):
                    end += length + util.conv_time_to_cycles(
                        sequencer.recording_delay, "ceil"
                    )
                else:
                    end += length

                cmd_duration = self.CmdTuple(cmd, start, end)
                commands.append(cmd_duration)

                if var_pulse:
                    # Add parallel choke command after current command, if variable length is used
                    parallel_choke = [self.CmdTuple(cmd, end, end + 1, choke=True)]
                    parallel_bodies.append(parallel_choke)

                    max_end = max(end + 1, max_end)  # +1 to account for choke command
                else:
                    max_end = max(end, max_end)

                start = end

            parallel_bodies.append(commands)

        return self._create_time_slots(parallel_bodies, max_end)

    def accept(self, visitor, *input):
        return visitor.visit_parallel(self, *input)

    def _stringify(self) -> str:
        return "Parallel"


class ForRange(QiContextManager):
    """Adds ForRange to program.
    If multiple cells are used inside body, a synchronisation between the cells is done before the ForRange as well as after the end of the body.
    If QiTimeVariable is used as var, loops starting at 0 are unrolled, to skip pulses/waits inside body using var as length.
    Raises exception if start, end and step are not set up properly."""

    def __init__(
        self,
        var: _QiVariableBase,
        start: Union[_QiVariableBase, int, float],
        end: Union[_QiVariableBase, int, float],
        step: Union[int, float] = 1,
    ):
        from .qi_types import (
            _TypeConstraintReasonQiCommand,
            _IllegalTypeReason,
            _add_equal_constraints,
        )

        super().__init__()

        if not isinstance(var, _QiVariableBase):
            raise RuntimeError(
                "Can only use QiVariables as control variable in ForRanges."
            )

        start_expr = QiExpression._from(start)
        end_expr = QiExpression._from(end)
        step_expr = QiExpression._from(step)

        var._type_info.add_illegal_type(QiType.STATE, _IllegalTypeReason.FOR_RANGE)
        start_expr._type_info.add_illegal_type(
            QiType.STATE, _IllegalTypeReason.FOR_RANGE
        )
        end_expr._type_info.add_illegal_type(QiType.STATE, _IllegalTypeReason.FOR_RANGE)
        step_expr._type_info.add_illegal_type(
            QiType.STATE, _IllegalTypeReason.FOR_RANGE
        )

        _add_equal_constraints(
            QiType.TIME,
            _TypeConstraintReasonQiCommand(ForRange),
            var,
            start_expr,
            end_expr,
            step_expr,
        )
        _add_equal_constraints(
            QiType.FREQUENCY,
            _TypeConstraintReasonQiCommand(ForRange),
            var,
            start_expr,
            end_expr,
            step_expr,
        )
        _add_equal_constraints(
            QiType.NORMAL,
            _TypeConstraintReasonQiCommand(ForRange),
            var,
            start_expr,
            end_expr,
            step_expr,
        )

        if not isinstance(start, _QiVariableBase) and not isinstance(
            end, _QiVariableBase
        ):
            if (start > end and step >= 0) or (start < end and step <= 0):
                raise ValueError("Definition of ForRange faulty")

        self.var = var
        self.start = start_expr
        self.end = end_expr
        self.step = step_expr

        self.add_associated_variable(var)

        if isinstance(start, _QiVariableBase):
            self.add_associated_variable(start)

            if start.id == var.id:
                raise RuntimeError("Loop variable can not be used as start value")

        if isinstance(end, _QiVariableBase):
            self.add_associated_variable(end)

            if end.id == var.id:
                raise RuntimeError("Loop variable can not be used as end value")

    def __exit__(self, exception_type, exception_value, traceback):
        super().__exit__(exception_type, exception_value, traceback)
        check_variable = QiVarInForRange(self.var)
        self.accept(check_variable)

    def accept(self, visitor, *input):
        return visitor.visit_for_range(self, *input)

    @property
    def is_step_positive(self) -> bool:
        return self.step > 0

    def _stringify(self) -> str:
        return f"ForRange({self.var}, {self.start}, {self.end}, {self.step})"


class QiVariable(_QiVariableBase):
    """Used as variables for use in program.
    If no type is provided as an argument, it will infer its type.
    """

    def __init__(
        self,
        type: Union[QiType, Type[int], Type[float]] = QiType.UNKNOWN,
        value=None,
        name=None,
    ) -> None:
        if type == int:
            type = QiType.NORMAL
        elif type == float:
            type = QiType.TIME

        super().__init__(type, value, name=name)
        _add_cmd_to_job(cQiDeclare(self))
        if self.value is not None:
            val = _QiConstValue(value)
            val._type_info.set_type(type, _TypeDefiningUse.VARIABLE_DEFINITION)
            _add_cmd_to_job(cQiAssign(self, val))


class QiJob:
    """
    Container holding program, cells and qi_result containers for execution of program.
    Builds the job with its properties

    :param skip_nco_sync: if the NCO synchronization at the beginning should be skipped
    :param nco_sync_length: how long to wait after the nco synchronization
    """

    def __init__(
        self,
        skip_nco_sync=False,
        nco_sync_length=0,
    ):
        self.qi_results: List[QiResult] = []
        self.cells = []
        self.couplers = []
        self.skip_nco_sync = skip_nco_sync
        self.nco_sync_length = nco_sync_length

        self._description = _JobDescription()

        # Build
        self._performed_analyses = False
        self._build_done = False
        self._arranged_cells: List[Optional[QiCell]] = []
        self._var_reg_map: Dict[_QiVariableBase, Dict[QiCell, int]] = {}

        # Run
        self._custom_processing = None
        self._custom_data_handler = None

    def __enter__(self):
        # pylint: disable=global-statement
        global _QiJobReference
        _QiJobReference = self
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        for cmd in self.commands:
            cmd.accept(QiTypeFallbackVisitor())

        for cmd in self.commands:
            cmd.accept(QiPostTypecheckVisitor())

        _QiVariableBase.reset_str_id()

        # pylint: disable=global-statement
        global _QiJobReference
        _QiJobReference = None

    def _open_new_context(self):
        self._description.open_new_context()

    def _close_context(self):
        return self._description.close_context()

    def _add_command(self, command):
        self._description.add_command(command)

    @property
    def commands(self):
        """returns the commands of the job"""
        return self._description._commands

    def _register_cells(self, cells: List[QiCell]):
        if len(self.cells) > 0:
            raise RuntimeError("Can only register one set of cells at a QiJob.")

        self.cells = cells

    def _register_couplers(self, couplers: List[QiCoupler]):
        if len(self.couplers) > 0:
            raise RuntimeError("Can only register one set of couplers at a QiJob.")

        self.couplers = couplers

    def _run_analyses(self):
        """
        Executes needed (dataflow) analyses.
        These mutate the commands in QiJob by inserting additional instructions, therefore
        they should only run once, in order to avoid duplicate instructions.
        """
        from .analysis.qi_insert_mem_parameters import (
            insert_recording_offset_store_commands,
            insert_manipulation_pulse_frequency_store_commands,
            insert_readout_pulse_frequency_store_commands,
        )

        if not self._performed_analyses:
            insert_recording_offset_store_commands(self)
            insert_manipulation_pulse_frequency_store_commands(self)
            insert_readout_pulse_frequency_store_commands(self)

        self._performed_analyses = True

    def _simulate_recordings(self) -> Dict[Any, List[cQiRecording]]:
        """
        Simulates the order cQiRecording executions.
        The result of this simulation is used to disentangle the recordings buffer
        and reassociate the individual recording results with their corresponding Recording commands.
        It might return more elements than are recorded during the real execution.
        """

        # We first check if there are Recording commands at positions which we can not simulate.
        # i.e. If-Else, ForRanges with start or end that are neither constant nor other loop variables.
        # If this is the case we cannot simulate the order.
        visitor = QiResultCollector()
        for cmd in self.commands:
            cmd.accept(visitor)

        if len(visitor.found_qi_results) == 0:
            return {cell: [] for cell in self.cells}
        elif visitor.recording_in_if:
            raise RuntimeError("Recording command within If-Else statement.")

        # Next we simulate all loops and collect the respective Recording commands inside.
        from .qi_simulate import Simulator

        simulator = Simulator(self.cells)
        simulator._simulate(self.commands)

        return simulator.cell_recordings

    def _build_program(
        self, sample: Optional[QiSample] = None, cell_map: Optional[List[int]] = None
    ):
        if sample is not None and cell_map is not None:
            sample = sample._arrange_for_controller()
            sample = [sample[m] if m < len(sample) else None for m in cell_map]

        if cell_map is None:
            cell_map = list(range(len(self.cells)))

        # TODO Check that this works with None and right order now
        self._resolve_properties(sample)

        for cell in self.cells:
            if len(cell._get_unresolved_properties()) > 0:
                raise RuntimeError(
                    f"Unresolved properties {cell._get_unresolved_properties()} at cell {cell}"
                )

        self._run_analyses()

        sim_result = self._simulate_recordings()
        for cell in self.cells:
            cell._result_recording_order = list(
                map(
                    lambda x: x.result_box,
                    filter(lambda x: x.result_box is not None, sim_result[cell]),
                )
            )

        prog_builder = QiProgramBuilder(
            self.cells,
            cell_map,
            self._description._commands.copy(),
            self.skip_nco_sync,
            self.nco_sync_length,
        )

        self.cell_seq_dict = prog_builder.build_program()
        self._var_reg_map = prog_builder.get_all_variables()
        self._build_done = True

    def _get_sequencer_codes(self):
        return [
            [
                instr.get_riscv_instruction()
                for instr in self.cell_seq_dict[cell].instruction_list
            ]
            for cell in self.cells
        ]

    def create_experiment(
        self,
        controller,
        sample: Optional[QiSample] = None,
        averages: int = 1,
        cell_map: Optional[List[int]] = None,
        coupling_map: Optional[List[int]] = None,
        data_collection=None,
        use_taskrunner=False,
    ):
        from ..experiment.qicode.base import QiCodeExperiment

        exp = QiCodeExperiment(
            *self._prepare_experiment_params(
                controller,
                sample,
                averages,
                cell_map,
                coupling_map,
                data_collection,
                use_taskrunner,
            )
        )

        if data_collection is None:
            if self._custom_processing is not None:
                exp._taskrunner.update(self._custom_processing)
            if self._custom_data_handler is not None:
                exp._data_handler_factory = DataHandler.get_custom_wrapper_factory(
                    self._custom_data_handler
                )

        # Provide a human-readable description of the execution
        if cell_map is None:
            cell_map = list(range(len(self.cells)))
        str_map = ", ".join([f"q[{i}] -> sample[{m}]" for i, m in enumerate(cell_map)])
        exp._job_representation = f"{self}\n\nmapped as {str_map} to\n\n{sample}"

        return exp

    def _prepare_experiment_params(
        self,
        controller,
        sample: Optional[QiSample] = None,
        averages: int = 1,
        cell_map: Optional[List[int]] = None,
        coupling_map: Optional[List[int]] = None,
        data_collection=None,
        use_taskrunner=False,
    ):
        if len(self.cells) > len(controller.cell):
            raise IndexError(
                f"This job requires {len(self.cells)} cells but only "
                f"{len(controller.cell)} are available in the QiController."
            )

        if data_collection is None:
            if self._custom_processing is None:
                data_collection = "average"
            else:
                data_collection = "custom"

        # If float, convert averages to int
        averages = int(averages)

        if sample is None:
            sample = QiSample(len(controller.cell))
        elif len(sample) < len(self.cells):
            raise ValueError(
                "Need to submit a QiSample with at least as many cells as the job "
                f"has ({len(self.cells)}), but only {len(sample)} provided."
            )

        if cell_map is None:
            # Use the first cells of the sample
            cell_map = list(range(len(self.cells)))
        else:
            if len(cell_map) != len(self.cells):
                raise ValueError(
                    "cell_map needs to have as many entries as the job has cells, but "
                    f"{len(cell_map)} entries given and {len(self.cells)} required!"
                )
            if len(set(cell_map)) != len(cell_map):
                raise ValueError("Duplicate values not allowed in cell_map!")
            if any(m < 0 or m >= len(sample) for m in cell_map):
                raise IndexError(
                    "cell_map values can only point to valid indices within the passed"
                    f" QiSample object, i.e. values between 0 and {len(sample) - 1}."
                )

        if coupling_map is None:
            coupling_map = list(range(len(self.couplers)))

        # Translate cell_map from sample cells ("cells") to QiController cells
        cell_map = [sample.cell_map[c] for c in cell_map]

        if any(c < 0 or c >= len(controller.cell) for c in cell_map):
            raise ValueError(
                "The QiSample cell_map can only reference available QiController "
                f"cells, i.e. between 0 and {len(controller.cell) - 1}."
            )

        self._build_program(sample, cell_map)

        for_range_list = []

        for cell in self.cells:
            for_range_list.append(self.cell_seq_dict[cell]._for_range_list)

        return (
            controller,
            self.cells,
            self.couplers,
            self._get_sequencer_codes(),
            averages,
            for_range_list,
            cell_map,
            coupling_map,
            self._var_reg_map,
            data_collection,
            use_taskrunner,
        )

    def run(
        self,
        controller,
        sample: Optional[QiSample] = None,
        averages: int = 1,
        cell_map: Optional[List[int]] = None,
        coupling_map: Optional[List[int]] = None,
        data_collection=None,
        use_taskrunner=False,
    ):
        """executes the job and returns the results

        :param controller: the QiController on which the job should be executed
        :param sample: the QiSample object used for execution of pulses and extracts parameters for the experiment
        :param averages: the number of executions that should be averaged, by default 1
        :param cell_map: A list containing the indices of the cells
        :param cell_map: A list containing the indices of the couplers
        :param data_collection: the data_collection mode for the result, by default "average"
        :param use_taskrunner: if the execution should be handled by the Taskrunner
            Some advanced schemes and data_collection modes are currently only supported
            by the Taskrunner and not yet by a native control flow.
        """
        exp = self.create_experiment(
            controller,
            sample,
            averages,
            cell_map,
            coupling_map,
            data_collection,
            use_taskrunner,
        )
        exp.run()

    def run_with_data_callback(self, on_new_data: Callable[[dict], None]):
        pass

    def run_streamed(self):
        pass

    def set_custom_data_processing(
        self,
        file: str,
        params: Optional[List] = None,
        converter: Optional[Callable[[List], List]] = None,
        mode: Union[TaskRunner.DataMode, str] = TaskRunner.DataMode.INT32,
        data_handler: Optional[Callable[[List[QiCell], DataProvider], None]] = None,
    ):
        from qiclib.experiment.qicode.base import _TaskrunnerSettings

        if isinstance(mode, str):
            mode = TaskRunner.DataMode[mode.upper()]

        self._custom_processing = _TaskrunnerSettings(
            file, "QiCode[Custom]", params, mode, converter
        )
        self._custom_data_handler = data_handler

    def print_assembler(
        self,
        cells: Optional[QiCells] = None,
        cell_index=0,
        cell_map: Optional[List[int]] = None,
    ):
        """
        Prints the commands as assembler code

        :param cells: the QiCells object for execution of pulses and saving result
        :param cell_index: the index of the cell in QiCells
        """
        print(f"Print program for cell index {cell_index}")
        self._build_program(cells, cell_map)

        cell = self.cells[cell_index]

        self.cell_seq_dict[cell].print_assembler()

    def _resolve_properties(self, sample: QiSample):
        # Check if any job cell has unresolved properties -> if not, return
        if not any(cell.has_unresolved_properties for cell in self.cells):
            return

        if sample is None:
            raise ValueError("QiSample needs to be passed to resolve job properties!")

        for i, cell in enumerate(self.cells):
            if cell.has_unresolved_properties:
                if i < len(sample) and sample[i] is not None:
                    cell._resolve_properties(sample[i]._properties)
                else:
                    raise ValueError(
                        f"Cell {i} of the job has unresolved properties but no QiSample "
                        "cell is specified for it! Check your cell_map."
                    )

    def __str__(self) -> str:
        from .qi_visitor import QiStringifyJob

        stringify_job = QiStringifyJob()
        return stringify_job.stringify(self)


def Sync(*cells: QiCell):
    """Synchronize cells. Currently implemented by comparing cycle times and adding wait commands. Cannot Sync after If/Else, or load/store to time variables"""
    _add_cmd_to_job(cQiSync(list(cells)))


def Play(cell: QiCell, pulse: QiPulse):
    """Add Manipulation command and pulse to cell

    :param cell: the cell that plays the pulse
    :param pulse: the pulse to play
    """
    _add_cmd_to_job(cQiPlay(cell, pulse))


def PlayReadout(cell: QiCell, pulse: QiPulse):
    """Add Readout command and pulse to cell

    :param cell: the cell that plays the readout
    :param pulse: the readout to play
    """
    _add_cmd_to_job(cQiPlayReadout(cell, pulse))


def PlayFlux(coupler: QiCoupler, pulse: QiPulse):
    """
    Add Flux Pulse command to cell

    :param coupler: The coupler that plays the pulse
    :param pulse: The pulse to play
    """
    _add_cmd_to_job(cQiPlayFlux(coupler, pulse))


def RotateFrame(cell: QiCell, angle: float):
    """Rotates the reference frame of the manipulation pulses played with :python:`Play()`.
    This corresponds to an instantaneous, virtual Z rotation on the Bloch sphere.

    :param cell: the cell for the rotation
    :param angle: the angle of the rotation
    """
    _add_cmd_to_job(cQiRotateFrame(cell, angle))


def Recording(
    cell: QiCell,
    duration: Union[int, float, QiCellProperty],
    offset: Union[int, float, QiCellProperty, QiExpression] = 0,
    save_to: Optional[str] = None,
    state_to: Optional[_QiVariableBase] = None,
    toggleContinuous: Optional[bool] = None,
):
    """Add Recording command to cell

    :param cell: the QiCell for the recording
    :param duration: the duration of the recording window in seconds
    :param offset: the offset of the recording window in seconds
    :param save_to: the name of the QiResult where to save the result data
    :param state_to: the variable in which the obtained qubit state should be stored
    :param toggleContinuous: whether the recording should be repeated continously and seemlessly
        Value True will start the recording, False will stop it (None is for normal mode)
    """
    rec = cQiRecording(
        cell,
        save_to,
        state_to,
        length=duration,
        offset=offset,
        toggleContinuous=toggleContinuous,
    )
    # When True, cQiRecording is added to the readout command
    if rec.follows_readout is False:
        _add_cmd_to_job(rec)


def DigitalTrigger(
    cell: QiCell,
    length: float,
    outputs: Iterable[int],
):
    """
    Adds a digital trigger command to the cell.

    Digital triggers are visible at auxiliary outputs and can be used, for example, to trigger external electronics
    simultaneously to outputting a pulse.
    The time resolution of digital triggers is 4 ns.

    =======
    Example
    =======

    The following QiJob Generates a 12 ns long pulse at digital outputs 3 and 6:

    .. code-block:: python

        with QiJob() as job:
            q = QiCells(1)
            DigitalTrigger(q[0], length=12e-9, outputs=(3, 6))

    ===================================================
    Combining the output of multiple Digital Unit Cells
    ===================================================

    Each Digital Unit Cell can trigger each output.
    To combine multiple outputs to multiple inputs, all digital outputs are combined using a logical OR operation.

    ================
    Delaying outputs
    ================

    A static delay can be added to each output using
    :python:`QiController.digital_trigger.set_delay(output_number, delay_in_seconds)`.
    To add a variable amount of time, use :python:`Wait(cell, duration)` before calling :python:`DigitalTrigger`

    :param cell: The cell that is responsible for the outputting the digital trigger
    :param length: The duration of the pulse in seconds. Should be a multiple of four ns
    :param outputs: The outputs to trigger. This can also be an expression like :python:`range(0, 8)`
        to trigger all outputs.
    """
    _add_cmd_to_job(cQiDigitalTrigger(cell, list(outputs), length))


def Wait(cell: QiCell, delay: Union[int, float, _QiVariableBase, QiCellProperty]):
    """Add Wait command to cell. delay can be int or QiVariable

    :param cell: the QiCell that should wait
    :param delay: the time to wait in seconds
    """
    _add_cmd_to_job(cQiWait(cell, delay))


def Store(cell: QiCell, variable: _QiVariableBase, save_to: QiResult):
    """Not implemented yet. Add Store command to cell."""
    _add_cmd_to_job(cQiStore(cell, variable, save_to))


def Assign(dst: _QiVariableBase, calc: Union[QiExpression, float, int]):
    """Assigns a calculated value to a destination

    :param dst: the destination
    :param calc: the calculation to perform
    """
    _add_cmd_to_job(cQiAssign(dst, calc))


def ASM(cell: QiCell, instr: SequencerInstruction, cycles=1):
    """Insert assembly instruction"""
    _add_cmd_to_job(cQiASM(cell, instr, cycles))


def QiGate(func):
    """decorator for using a function in a QiJob

    :raises RuntimeError: if QiGate inside QiGate
    """

    @functools.wraps(func)
    def wrapper_QiGate(*args, **kwargs):
        start = len(_QiJobReference.commands)

        func(*args, **kwargs)

        end = len(_QiJobReference.commands)

        find_cells = QiCMContainedCellVisitor()

        for cmd in _QiJobReference.commands[start:end]:
            cmd.accept(find_cells)

            if isinstance(cmd, cQiAssign):
                raise RuntimeError(
                    "Assign inside QiGate might result in unwanted side effects."
                )

        if len(find_cells.contained_cells) > 1:
            _QiJobReference.commands.insert(
                start, cQiSync(list(find_cells.contained_cells))
            )

    return wrapper_QiGate


class QiTimeVariable(QiVariable):
    def __init__(self, value=None, name=None):
        super().__init__(type=QiType.TIME, value=value, name=name)


class QiStateVariable(QiVariable):
    def __init__(self, name=None):
        super().__init__(type=QiType.STATE, name=name)


class QiIntVariable(QiVariable):
    def __init__(self, value=None, name=None):
        super().__init__(type=QiType.NORMAL, value=value, name=name)
