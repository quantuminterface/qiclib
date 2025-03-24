# Copyright© 2017-2023 Quantum Interface (quantuminterface@ipe.kit.edu)
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
"""This module contains the drivers to interface with the digital unit cells and the
cell coordinator on the QiController.

Different FPGA modules exist to generate and analyze microwave pulses, to persist data,
and to coordinate their execution in a well-defined sequence of operations with the
required precision and timing accuracy. These are bundled inside so-called digital unit
cells. Each of them contains all functionality required to interface a single
superconducting qubit. The microwave signals are digitally represented in the
complex-valued baseband as in-phase and quadrature (I/Q) components with 16 bit
resolution each. This enables arbitrary pulse shaping and full phase and sideband
control of the (later) up-converted signal. The FPGA processes four samples each cycle
(4 ns) to obtain a converter data rate of 1 GS/s (1 ns resolution).

.. image:: unitcell.png

The digital unit cell is structured as follows: Two signal generators create the
required pulses to control and read out the qubit. A signal recorder takes the digitized
signal from the ADC and demodulates it to obtain the qubit state. A dedicated data
storage collects the resulting data from the signal recorder and the sequencer. A
digital trigger block can generate digital signals to address and trigger external lab
equipment. All modules are controlled and activated by the sequencer which orchestrates
their execution in single-cycle steps (4 ns). For fast conditional responses, the signal
recorder directly reports all measured qubit states back to the sequencer which can then
act accordingly. In all other cases, the modules communicate exclusively via a Wishbone
bus that connects them. This also applies for trigger signals from the sequencer to
control the execution of the other modules.

For more information on the different modules within the digital unit cell, refer to:

* Sequencer: `qiclib.hardware.sequencer`
* Signal generator: `qiclib.hardware.pulsegen`
* Signal recorder: `qiclib.hardware.recording`
* Data storage: `qiclib.hardware.storage`

Each QiController contains multiple digital unit cells, so multi-qubit experiments can
be easily performed. The generated signals from the digital unit cells can be flexibly
routed to the DAC channels. It is possible to combine signals from multiple cells onto
the same DAC channel for frequency-division-multiplexed readout and control.

.. todo:: Add information on how this signal routing is performed / configured.

"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from typing import TYPE_CHECKING

import numpy as np

import qiclib.packages.grpc.datatypes_pb2 as dt
import qiclib.packages.grpc.qic_unitcell_pb2 as proto
import qiclib.packages.grpc.qic_unitcell_pb2_grpc as grpc_stub
from qiclib.hardware.digital_trigger import DigitalTrigger
from qiclib.hardware.platform_component import PlatformComponent
from qiclib.hardware.pulsegen import PulseGen
from qiclib.hardware.recording import Recording
from qiclib.hardware.sequencer import Sequencer
from qiclib.hardware.storage import Storage
from qiclib.packages.servicehub import ServiceHubCall

if TYPE_CHECKING:
    from qiclib.hardware.controller import QiController


class UnitCell:
    """A single digital unit cell containing its internal modules as properties.
    The index serves as identifier in a List of UnitCells.

    This class is not created by the user. Instead, existing instances of it can be
    accessed using the `qiclib.hardware.controller.QiController` and its
    `qiclib.hardware.controller.QiController.cell` list property.

    Example:

    .. code-block:: python

        qic = QiController("ip-address")
        qic.cell[5].busy  # if the 6th digital unit cell in the QiController is busy
        qic.cell[3].sequencer.start_at(0)  # start the sequencer in the 4th cell

    """

    def __init__(self, index: int, cells: UnitCells, info: proto.CellInfo):  # type: ignore
        self._index = index
        self._cells = cells
        controller: QiController = cells._qip
        connection = controller._conn

        self._sequencer = Sequencer(
            f"Cell {index} Sequencer", connection, controller, index=info.sequencer
        )
        self._readout = PulseGen(
            f"Cell {index} Readout PG", connection, controller, index=info.readout
        )

        self._manipulation = PulseGen(
            f"Cell {index} Control PG", connection, controller, index=info.manipulation
        )
        self._recording = Recording(
            f"Cell {index} Recording", connection, controller, index=info.recording
        )
        self._storage = Storage(
            f"Cell {index} Storage", connection, controller, index=info.storage
        )
        self._digital_trigger = DigitalTrigger(
            f"Cell {index} Digital Trigger",
            connection,
            controller,
            index=info.digital_trigger,
        )

    def start(self):
        self._cells.start([self._index])

    @property
    def sequencer(self) -> Sequencer:
        """Sequencer of this digital unit cell.

        It controls and orchestrates the execution of the other modules within the cell
        with nanosecond precision.
        """
        return self._sequencer

    @property
    def manipulation(self) -> PulseGen:
        """Manipulation/control signal generator of this digital unit cell.

        It creates the required manipulation pulses to control the qubit state.
        """
        return self._manipulation

    @property
    def readout(self) -> PulseGen:
        """Readout signal generator of this digital unit cell.

        It creates the required readout pulses to measure the qubit state.
        """
        return self._readout

    @property
    def recording(self) -> Recording:
        """Signal recorder of this digital unit cell.

        It processes returning readout pulses to extract the measured qubit state.
        """
        return self._recording

    @property
    def storage(self) -> Storage:
        """Data storage of this digital unit cell.

        It contains the data which was obtained and persisted during an experiment.
        """
        return self._storage

    @property
    def digital_trigger(self) -> DigitalTrigger:
        """Digital trigger capabilities of this digital unit cell.

        Enables manual trigger and trigger-set overrides.
        """
        return self._digital_trigger

    @property
    def busy(self) -> bool:
        """If the cell is currently busy.

        This returns true if any of the internal modules is currently busy.
        """
        return self._index in self._cells.busy_cells


class UnitCells(PlatformComponent, Mapping):
    """The list of all digital unit cells plus access to the cell coordinator.

    Individual unit cells can be accessed using the index operator.
    Additional commands are provided to interact with the cell coordinator.

    The cell coordinator synchronizes the execution of the digital unit cells. When
    started externally, the sequencers within the digital unit cells run independently.
    However, for experiments requiring multiple cells, the execution needs to be aligned
    in time. This is achieved by the cell coordinator which is connected to all digital
    unit cells in a star point architecture. Using this structure, the cell coordinator
    can synchronously start the sequencers of any subset of the available digital unit
    cells. It also aggregates their busy flags and makes them accessible (`busy_cells`).
    """

    def __init__(
        self,
        name: str,
        connection,
        controller,
        qkit_instrument=True,
    ):
        super().__init__(name, connection, controller, qkit_instrument)
        self._stub = grpc_stub.UnitCellServiceStub(self._conn.channel)
        self._cells: list[UnitCell] = []
        self._update_cells()

    def __iter__(self):
        return iter(self._cells)

    def __len__(self) -> int:
        return self.count

    def __getitem__(self, key: int) -> UnitCell:
        return self._cells[int(key)]

    @ServiceHubCall(errormsg="Could not obtain digital unit cell information.")
    def _update_cells(self):
        info = self._stub.GetAllCellInfo(dt.Empty())
        self._cells = []
        for i, cell in enumerate(info.cells):
            self._cells.append(UnitCell(i, self, cell))

    @property
    def count(self):
        """The number of digital unit cells available in the QiController."""
        return len(self._cells)

    @ServiceHubCall
    def start_all(self):
        """Start the sequencers of all digital unit cells synchronously.

        If only a subset of all cells should be started, use `UnitCells.start` instead.

        .. note::
            The start address of the sequencers will be left untouched, so these need to be
            configured beforehand (in most cases, leaving them at 0 is sufficient), see
            :func:`qiclib.hardware.sequencer.Sequencer.start_address`.
        """
        self._stub.StartCells(proto.StartCellInfo(all_cells=True))

    @ServiceHubCall
    def start(self, cells: list[int]):
        """Starts the sequencers of the given digital unit cells synchronously.

        If you want to start all cells, you can use `UnitCells.start_all` instead.

        :param cells:
            A list of the indices of all digital unit cells that should be started.

        .. note::
            The start address of the sequencers will be left untouched, so these need to be
            configured beforehand (in most cases, leaving them at 0 is sufficient), see
            `qiclib.hardware.sequencer.Sequencer.start_address`.
        """
        self._stub.StartCells(proto.StartCellInfo(cells=cells))

    def start_at(self, addresses: dict[int, int]):
        """Starts the given cells (keys) at the given sequencer addresses (values).

        If you us the same sequencer start addresses every time, you can set them once
        and then simply use `UnitCells.start_all` or `UnitCells.start`.

        :param addresses:
            A dictionary containing the sequencer start addresses (values) for all cells
            that should be started (keys)
        """
        # Set start addresses for all relevant cells
        for cell, pos in addresses.items():
            self[cell].sequencer.start_address = pos
        # Start the execution of these cells simulataneously
        self.start(list(addresses.keys()))

    def stop_all(self):
        """Stops the execution of all cells and their sequencers."""
        for cell in self._cells:
            cell.sequencer.stop()

    @property
    @ServiceHubCall
    def busy(self) -> bool:
        """If any of the digital unit cells is currently busy."""
        return self._stub.GetBusyCells(dt.Empty()).busy

    @property
    @ServiceHubCall
    def busy_cells(self) -> list[int]:
        """A list with the indices of all digital unit cells that are currently busy."""
        return self._stub.GetBusyCells(dt.Empty()).cells

    @ServiceHubCall
    def check_status(self, raise_exceptions=True):
        """Check if a converter reported an error and if so, forward it to the user."""
        response = self._stub.GetConverterStatus(dt.Empty())
        status_report = response.report
        status_ok = not response.error

        if not status_ok:
            self.clear_status_report()
            status_report = (
                "The converters reported the following issue(s):\n" + status_report
            )
            if raise_exceptions:
                raise Warning(status_report)
            sys.stderr.write(status_report)

        return status_ok

    @ServiceHubCall
    def get_status_report(self) -> str:
        """Retrieve a status report from the converters."""
        return self._stub.GetConverterStatus(dt.Empty()).report

    @ServiceHubCall
    def clear_status_report(self):
        """Resets the status report so old error messages will be discarded."""
        self._stub.ClearConverterStatus(dt.Empty())

    @ServiceHubCall
    def run_experiment(
        self,
        averages: int,
        cells: list[int],
        recordings: list[int],
        data_collection: str = "average",
        progress_callback=None,
    ):
        """
        Runs the experiment on the hardware.
        Returns an array of the results.
        The return type of each result depends on the data collection mode:

        - Average, Amplitude & Phase, Raw: A tuple containing the I/Q values as numpy arrays (float type)
        - IQ Cloud: A tuple containing the I/Q values as numpy arrays (signed integer type)
        - States, Quantum Jumps, State Count: A single numpy array containing the states (unsigned integer type)
        """
        switch_dict = {
            "average": proto.AVERAGE,
            "amp_pha": proto.AMPLITUDE_PHASE,
            "iqcloud": proto.IQCLOUD,
            "raw": proto.RAW_TRACE,
            "states": proto.STATES,
            "counts": proto.STATE_COUNT,
            "quantum_jumps": proto.QM_JUMPS,
        }
        mode = switch_dict.get(data_collection)
        if mode is None:
            raise Warning("Unknown data collection mode " + data_collection)
        experiment_results = None
        for progress in self._stub.RunExperiment(
            proto.ExperimentParameters(
                mode=mode,
                shots=averages,
                cells=cells,
                recordings=recordings,
            )
        ):
            experiment_results = progress
            if progress_callback:
                progress_callback(progress.progress)
        results = experiment_results.results
        mode = experiment_results.mode
        # Convert the proto messages to appropriate arrays
        if mode in {proto.AVERAGE, proto.AMPLITUDE_PHASE, proto.RAW_TRACE}:
            return [
                (
                    np.array(single_result.data_double_1, dtype=float),  # I
                    np.array(single_result.data_double_2, dtype=float),  # Q
                )
                for single_result in results
            ]
        elif mode == proto.IQCLOUD:
            return [
                (
                    np.array(single_result.data_sint32_1, dtype=np.int32),
                    np.array(single_result.data_sint32_2, dtype=np.int32),
                )
                for single_result in results
            ]
        elif mode in {proto.STATES, proto.QM_JUMPS, proto.STATE_COUNT}:
            return [
                np.array(single_result.data_uint32, dtype=np.uint32)
                for single_result in results
            ]
        else:
            raise AssertionError("Unknown data collection mode")
