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
"""This module contains the drivers to interface with the QiController.

A general introduction into the QiController architecture is given in `qiclib.hardware`.

The `QiController` class is the interface to the platform and enables the user to
control it to any extend possible. This ranges from direct low-level access to the
different components up to high-level access using QiCode (see :mod:`qiclib.code`) and even
integration in other frameworks like Qiskit and Qkit.

A connection to the platform can be established by creating an instance of this class
and passing the ip address of the QiController. The class instance then provides access
to all the functionality of the platform.

.. todo:: Image with structure of QiController class.

.. image:: qicontroller.png

The QiController class contains multiple submodules, one for the Taskrunner, another one
for general status information by the platform information and management core (PIMC),
and a third one to represent the digital unit cells of the platform. Each unit cell
contains submodules for sequencer and signal recorder (called ``recording``), as well as
for the data storage and both signal generators (called ``readout`` and ``manipulation``
to distinguish between their intended usage).

Most accesses to the platform are realized using the getter/setter pattern where one
does not call any method explicitly but just assigns the values to the appropriate
property which will be transparently propagated to the QiController. Likewise, reading
out a value happens by simply accessing the property which will cause a network request
in the background whose result is then returned as value of the property. Only more
complex operations are implemented as methods to indicate that these operations might
cause some considerable overhead. The same applies for operations that not just
configure the modules but trigger an action, like starting or resetting a module.

Example
-------
Setting the pulse duration of the manipulation pulse stored in trigger set 12 of the
fifth digital unit cell is accomplished by:

.. code-block:: python

    qic = QiController("ip-address")  # Only needed once when initializing the board
    qic.cell[4].manipulation.triggerset[12].duration = 80e-9  # seconds (80 ns)

The assignment will then be handled within the :class:`qiclib.hardware.pulsegen.TriggerSet`
class where it is translated to a remote procedure call of the
:class:`qiclib.hardware.pulsegen.PulseGen` class that communicates with the QiController.

"""

from __future__ import annotations

import json
import sys
import warnings
from contextlib import suppress

import qiclib
import qiclib.packages.constants as const
from qiclib.hardware.direct_rf import DirectRf
from qiclib.hardware.direct_rf_addon import DirectRfAddon
from qiclib.hardware.pimc import PIMC
from qiclib.hardware.platform_component import (
    PlatformComponent,
    platform_attribute,
    platform_attribute_collector,
)
from qiclib.hardware.pulse_player import PulsePlayer
from qiclib.hardware.pulsegen import PulseGen
from qiclib.hardware.recording import Recording
from qiclib.hardware.rfdc import RFDataConverter
from qiclib.hardware.sequencer import Sequencer
from qiclib.hardware.servicehub import ServiceHub
from qiclib.hardware.storage import Storage
from qiclib.hardware.taskrunner import TaskRunner
from qiclib.hardware.unitcell import UnitCells
from qiclib.packages.qkit_polyfill import SampleObject
from qiclib.packages.servicehub import Connection


@platform_attribute_collector
class QiController(PlatformComponent):
    """The QiController driver class.

    All components of the platform can be accessed via the properties of this class.

    :param ip:
        The IP address of the QiController where it can be reached over the network
    :param port:
        The port for the network connection. It only needs to be changed if you use
        port forwarding of the platform port 50058 to another one.
    :param silent:
        If print messages from QiController should be suppressed
    """

    def __init__(self, ip: str, port: int = 50058, silent: bool = False):
        self._silent = silent
        print(f"qiclib version: {qiclib.__version__}")

        # Connection to the Platform
        connection = Connection(ip=ip, port=port, silent=True)
        super().__init__("QiController", connection, self)
        self._print(f"Establishing remote connection to {self._conn.ip}...")

        self._servicehub = ServiceHub(
            "ServiceHub", connection, self, qkit_instrument=False
        )
        self._pimc = PIMC("PIMC", connection, self, qkit_instrument=False)
        self._read_board_info()

        if self._servicehub.taskrunner_available:
            self._taskrunner = TaskRunner("Taskrunner", connection, self)
        else:
            self._taskrunner = None

        if self._servicehub.has_rfdc:
            self._rfdc = RFDataConverter("RF Data Converter", connection, self)
        else:
            self._rfdc = None
        self._cell = UnitCells("UnitCells", connection, self, qkit_instrument=False)
        self._print(f"Firmware with {self.cell.count} digital unit cells detected.")

        if self.cell.count == 0:
            raise ValueError(
                "No digital unit cells found on QiController! "
                "Please update the board firmware."
            )
        self._pulse_players = []
        for endpoint in self._servicehub.get_endpoints_of_plugin("PulsePlayerPlugin"):
            index = self._servicehub.get_endpoint_index_from_plugin(
                "PulsePlayerPlugin", endpoint
            )
            self._pulse_players.append(
                PulsePlayer(
                    "Pulse Player", connection, self, index, qkit_instrument=False
                )
            )

        if self._servicehub.has_direct_rf:
            self._direct_rf_board = DirectRfAddon(
                "DirectRf Addon Card", connection, self
            )

            self._direct_rf = DirectRf("Direct RF", connection, self)
            self._output_channels = [
                self._direct_rf.output_channel(i) for i in range(16)
            ]
            self._input_channels = [self._direct_rf.input_channel(i) for i in range(8)]
        else:
            self._direct_rf_board = None
            self._direct_rf = None
            self._output_channels = None
            self._input_channels = None

        # TODO Deprecated, remove in next major version
        # Preconfigure some standard values
        warnings.filterwarnings("ignore", category=FutureWarning)
        self._sample = SampleObject()
        self._init_sample_object()
        self.update_modules()
        warnings.filterwarnings("default", category=FutureWarning)

        # Remove old error messages
        self.clear_errors()

        self._last_qijob = "<Nothing loaded yet>"

    def __str__(self):
        return f"QiController({self._conn.ip}:{self._conn.port})"

    def _read_board_info(self):
        """Prints the used FPGA platform and the build date

        :raises Exception:
            If the project id is not supported by the drivers
        :raises Exception:
            If the board id is not supported by the drivers
        """
        # Read out QiController parameters
        self._project_id = self.pimc.project_id
        self._platform_id = self.pimc.platform_id
        self._revision = self.pimc.project_revision
        self._build_time = self.pimc.build_time
        self._project_name = self.pimc.project
        self._platform_name = self.pimc.platform

        if self.project_id != 0x3:
            raise RuntimeError(
                f"Project ID {self.project_id} ({self.project_name}) is not supported "
                "by this driver version"
            )

        self._platform_name = {
            0x23: "ZCU111",
            0x38: "ZRF8",
            0x41: "ZCU216",
            0x51: "ZCU208",
        }.get(self.platform_id)

        if self.platform_name is None:
            raise RuntimeError(
                f"Board ID {self.platform_id} ({self.platform_name}) is not supported "
                "by this driver version"
            )

        self._print(
            f"Detected {self.project_name} running on {self.platform_name} board"
        )
        self._print(
            f"Firmware build time: {self.build_time} (Revision {self.revision})"
        )

    @property
    def cell(self) -> UnitCells:
        """The digital unit cells of the QiController.

        More information can be found here: :class:`qiclib.hardware.unitcell`
        """
        return self._cell

    @property
    def pimc(self) -> PIMC:
        """The platform information and management core of the QiController.

        This component provides general information of the version and status of the
        QiController. Normally, one does not need to access it explicitly, as all
        relevant information is also exposed directly using the :class:`QiController` class.
        """
        return self._pimc

    @property
    def rfdc(self) -> RFDataConverter | None:
        """The RF data converters (ADCs/DACs) of the QiController.

        This component provides configuration access to the data converters of the board
        and can be used to query status information like overvoltage conditions.
        """
        return self._rfdc

    @property
    def pulse_players(self) -> list[PulsePlayer]:
        """
        The pulse players of the platform.

        Each :class:`qiclib.hardware.pulse_player.PulsePlayer`
        is similar to the `qiclib.hardware.pulse_player.PulseGen` component,
        however, pulse players do not have digital upconversion but instead  more memory.
        """
        return self._pulse_players

    @property
    def taskrunner(self) -> TaskRunner | None:
        """The Taskrunner framework of the QiController.

        This subsystem can be used to run arbitrary C code on a processor of the
        QiController to perform custom online data processing and aggregation.

        More information can be found here: :class:`qiclib.hardware.taskrunner`
        """
        return self._taskrunner

    @property
    @platform_attribute
    def project_name(self):
        """The name of the project running on the platform."""
        return self._project_name

    @property
    @platform_attribute
    def platform_name(self):
        """The name of the platform board on which the QiController is running."""
        return self._platform_name

    @property
    @platform_attribute
    def project_id(self):
        """The ID of the project running on the platform."""
        return self._project_id

    @property
    @platform_attribute
    def platform_id(self):
        """The ID of the platform board on which the QiController is running."""
        return self._platform_id

    @property
    @platform_attribute
    def revision(self):
        """The revision number of the QiController firmware."""
        return self._revision

    @property
    @platform_attribute
    def build_time(self):
        """The time when the QiController firmware was created."""
        return self._build_time

    @property
    def ready(self):
        """If the QiController is ready to be used."""
        return self.pimc.is_ready

    @property
    def busy(self):
        """If the QiController is currently busy."""
        return self.pimc.is_busy

    @property
    def output_channels(self):
        if self._output_channels is None:
            raise AttributeError("DirectRf not available for this platform")
        return self._output_channels

    @property
    def input_channels(self):
        if self._input_channels is None:
            raise AttributeError("DirectRf not available for this platform")
        return self._input_channels

    @property
    @platform_attribute
    def ip_address(self):
        """The IP address used to access the QiController."""
        return self._conn.ip

    @property
    @platform_attribute
    def taskrunner_available(self) -> bool:
        """If the Taskrunner subsystem is available on the QiController."""
        return self._taskrunner is not None

    @property
    @platform_attribute
    def cell_count(self):
        """The number of unit cells implemented on the QiController."""
        return self.cell.count

    @property
    def last_qijob(self):
        """String representation of the last QiJob loaded onto the QiController.

        See :mod:`qiclib.code` for details on QiCode.

        The string contains the following information:

        - QiCode that was compiled and loaded
        - cell mapping between QiCode and QiCells sample object used
        - QiCells sample object with the parameter values
        """
        return self._last_qijob

    def stop(self):
        """Stops the current execution on the QiController."""
        # Stop taskrunner (if running)
        if self.taskrunner is not None and self.taskrunner.busy:
            self.taskrunner.stop_task()
            self._print_warning("Stopped running execution of the Taskrunner.")
        if self.cell.busy:
            self.cell.stop_all()
            self._print_warning("Cells were busy and have been stopped.")

    def check_errors(self, raise_exceptions=True, stop_on_error=True):
        """Checks if errors occurred on the platform and throws an Exception if so.

        :param raise_exceptions:
            If the script execution should be interrupted by an exception, by default True
        :param stop_on_error:
            If the QiController should be stopped when an error is detected, by default True

        :return:
            True if no errors have been detected (so False if any errors have been found)

        :raises Warning:
            When errors have been detected, the error message is shown as exception
        """
        errors = self._get_errors()

        if errors:
            status_report = (
                "The following errors happened on the platform:\n\n{}".format(
                    "\n\n".join(errors)
                )
            )
            if stop_on_error:
                self.stop()
                self.clear_errors(silent=True)
            if raise_exceptions:
                raise Warning(status_report)
            self._print_warning(status_report)
            return False
        return True

    def clear_errors(self, silent=False):
        """Deletes all present error messages (typically used at the beginning of a new
        experiment).

        Existing error messages will be printed as warning.

        :param silent:
            If existing error messages should not be printed to stderr, be default False
        """
        errors = self._get_errors()
        if self.rfdc is not None:
            # Also reset ADC over range & voltage detection
            self.rfdc.reset_status()
        # Afterwards can reset flags of converters
        self.cell.clear_status_report()
        if errors and not silent:
            self._print_warning(
                "The following previous platform errors were ignored and cleared:"
                + "\n\n{}".format("\n\n".join(errors))
            )

    def _get_errors(self) -> list[str]:
        """Collects all error messages and returns them as list of strings.

        :return:
            A list of all error messages that have been obtained
        """
        status_msgs = []

        for cell in self.cell:
            for part in [cell.readout, cell.manipulation, cell.recording]:
                try:
                    part.check_status()
                except Warning as e:
                    status_msgs.append(
                        f"{part.name} returned the following warning:\n{e}"
                    )

        if self.taskrunner is not None:
            try:
                self.taskrunner.check_task_errors()
            except Warning as e:
                status_msgs.append(
                    f"The Taskrunner returned the following warning:\n{e}"
                )

        try:
            # TODO Replace by rfdc.check_status once this is properly working
            self.cell.check_status()
        except Warning as e:
            status_msgs.append(str(e))

        return status_msgs

    def export_configuration_dicts(self, filename):
        """Exports the configuration of the QiController as JSON dictionary.

        :param filename:
            Name of the JSON file where the configuration should be written to
        """
        cells_export_list = []
        for cell in self.cell:
            cell_export_dict = {
                "recording": cell.recording.get_configuration_dict(),
                "readout": cell.readout.get_configuration_dict(),
                "manipulation": cell.manipulation.get_configuration_dict(),
                "sequencer": cell.manipulation.get_configuration_dict(),
                "storage": cell.storage.get_configuration_dict(),
            }
            cells_export_list.append(cell_export_dict)
        with open(f"{filename}.json", "w", encoding="utf-8") as exportfile:
            json.dump(cells_export_list, exportfile)

    def load_configuration_dicts(self, filename):
        """Loads an existing JSON configuration into the QiController.

        :param filename:
            Name of the JSON file containing the configuration settings to load
        """
        with open(f"{filename}.json", encoding="utf-8") as config_file:
            cells_list = json.load(config_file)
        for index, cell_dict in enumerate(cells_list):
            for hardwaremodule, value_dict in cell_dict.items():
                module = getattr(self.cell[index], hardwaremodule)
                for key, value in value_dict.items():
                    setattr(module, key, value)

    def _print(self, *msg):
        if not self._silent:
            print("[QiController]", *msg)

    def _print_warning(self, msg: str):
        sys.stderr.write(f"[QiController] WARNING: {msg}\n")

    #####################################
    # TODO Remove in next major version #
    #####################################

    @property
    def sequencer(self) -> Sequencer:
        """The sequencer of the first digital unit cell of the QiController.

        .. deprecated::
            `sequencer` will be removed in a future version. Please use the new cell
            structure and `cell[0].sequencer` instead. The old syntax is a leftover
            from the time when the QiController had only one sequencer.
        """
        warnings.warn(
            "QiController.sequencer will be removed in future. Please use the new cell "
            "structure instead, i.e.: QiController.cell[0].sequencer",
            FutureWarning,
        )
        return self.cell[0].sequencer

    @property
    def readout(self) -> PulseGen:
        """The readout signal generator of the first digital unit cell of the
        QiController.

        .. deprecated::
            `readout` will be removed in a future version. Please use the new cell
            structure and `cell[0].readout` instead. The old syntax is a leftover
            from the time when the QiController had only one readout signal generator.
        """
        warnings.warn(
            "QiController.readout will be removed in future. Please use the new cell "
            "structure instead, i.e.: QiController.cell[0].readout",
            FutureWarning,
        )
        return self.cell[0].readout

    @property
    def manipulation(self) -> PulseGen:
        """The control/manipulation signal generator of the first digital unit cell of
        the QiController.

        .. deprecated::
            `manipulation` will be removed in a future version. Please use the new cell
            structure and `cell[0].manipulation` instead. The old syntax is a leftover
            from the time when the QiController had only one control signal generator.
        """
        warnings.warn(
            "QiController.manipulation will be removed in future. Please use the new "
            "cell structure instead, i.e.: QiController.cell[0].manipulation",
            FutureWarning,
        )
        return self.cell[0].manipulation

    @property
    def recording(self) -> Recording:
        """The signal recorder of the first digital unit cell of the QiController.

        .. deprecated::
            `recording` will be removed in a future version. Please use the new cell
            structure and `cell[0].recording` instead. The old syntax is a leftover
            from the time when the QiController had only one signal recorder.
        """
        warnings.warn(
            "QiController.recording will be removed in future. Please use the new cell "
            "structure instead, i.e.: QiController.cell[0].recording",
            FutureWarning,
        )
        return self.cell[0].recording

    @property
    def storage(self) -> Storage:
        """The data storage of the first digital unit cell of the QiController.

        .. deprecated::
            `storage` will be removed in a future version. Please use the new cell
            structure and `cell[0].storage` instead. The old syntax is a leftover
            from the time when the QiController had only one data storage.
        """
        warnings.warn(
            "QiController.storage will be removed in future. Please use the new cell "
            "structure instead, i.e.: QiController.cell[0].storage",
            FutureWarning,
        )
        return self.cell[0].storage

    @property
    def direct_rf_board(self):
        if self._direct_rf_board is None:
            raise AttributeError("DirectRf not available for this platform")
        return self._direct_rf_board

    @property
    def sample(self):
        """The sample object containing relevant information for experiments.

        .. deprecated::
            `sample` will be removed in the future. Please use the new QiCode syntax
            (see `qiclib.code`) and the `qiclib.code.qi_jobs.QiSample` object instead.
        """
        warnings.warn(
            "QiController.sample is deprecated and will be removed in future. Please "
            "use the new QiCode syntax instead, i.e. create a `QiSample` object.",
            FutureWarning,
        )
        return self._sample

    @sample.setter
    def sample(self, sample):
        warnings.warn(
            "QiController.sample is deprecated and will be removed in future. Please "
            "use the new QiCode syntax instead, i.e. create a `QiSample` object.",
            FutureWarning,
        )
        self._sample = sample
        self.update_modules()

    def _init_sample_object(self):
        # helper function to initialize values only once after system power-on
        def siz(var, default):  # set (to default) if zero
            return default if var == 0 else var

        self.sample.manip_if_frequency = siz(self.manipulation.if_frequency, 80e6)
        self.sample.rec_if_frequency = siz(
            max(
                self.readout.internal_frequency,
                self.recording.reference_frequency
                if self.recording.interferometer_mode
                else self.recording.internal_frequency,
            ),
            62.5e6,
        )
        if self.recording.interferometer_mode:
            self.sample.rec_ref_delay = siz(self.recording.reference_delay, 16e-9)

        self.sample.rec_duration = siz(self.recording.recording_duration, 400e-9)
        self.sample.rec_offset = self.recording.trigger_offset
        self.sample.rec_phase = self.recording.phase_offset

        self.sample.expected_highest_signal_amplitude = (
            self.recording.expected_highest_signal_amplitude
        )
        self.sample.rec_shift_average = self.recording.average_shift

        # This is more a good guess than a guarantee
        self.sample.rec_pulselength = siz(self.readout.triggerset[1].duration, 400e-9)

        self.sample.clock = const.CONTROLLER_SAMPLE_FREQUENCY_IN_HZ

    def update_modules(self):
        """Updates some module settings based on the values set in the sample file."""
        # Ignore if sample property is undefined
        with suppress(AttributeError):
            self.manipulation.if_frequency = self.sample.manip_if_frequency
        with suppress(AttributeError):
            self.readout.if_frequency = self.sample.rec_if_frequency
            self.recording.internal_frequency = self.sample.rec_if_frequency
            if self.recording.interferometer_mode:
                self.recording.reference_frequency = self.sample.rec_if_frequency
        with suppress(AttributeError):
            self.recording.reference_delay = self.sample.rec_ref_delay
        with suppress(AttributeError):
            self.recording.recording_duration = self.sample.rec_duration
        with suppress(AttributeError):
            self.recording.expected_highest_signal_amplitude = (
                self.sample.expected_highest_signal_amplitude
            )
        with suppress(AttributeError):
            self.recording.average_shift = self.sample.rec_shift_average
        with suppress(AttributeError):
            self.recording.trigger_offset = self.sample.rec_offset
        with suppress(AttributeError):
            self.recording.phase_offset = self.sample.rec_phase
        with suppress(AttributeError):
            self.manipulation.frequency = self.sample.f01
        with suppress(AttributeError):
            self.readout.frequency = self.sample.fr
