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
from __future__ import annotations

import math
import time
from dataclasses import dataclass, fields
from typing import Callable

import numpy as np

from qiclib.code.qi_jobs import QiCell, QiCoupler
from qiclib.code.qi_pulse import QiPulse
from qiclib.code.qi_sequencer import ForRangeEntry, Sequencer
from qiclib.code.qi_types import QiType
from qiclib.code.qi_var_definitions import _QiVariableBase
from qiclib.experiment.base import BaseExperiment, ExperimentReadout
from qiclib.experiment.qicode.data_handler import DataHandler
from qiclib.experiment.qicode.data_provider import DataProvider
from qiclib.hardware.controller import QiController
from qiclib.hardware.pulsegen import TriggerSet
from qiclib.hardware.taskrunner import TaskRunner
from qiclib.packages import utility as util
from qiclib.packages.constants import CONTROLLER_SAMPLE_FREQUENCY_IN_HZ as samplerate
from qiclib.packages.qkit_polyfill import SampleObject


@dataclass
class _TaskrunnerSettings:
    taskfile: str
    taskname: str
    params: list | None
    data_mode: TaskRunner.DataMode | str
    data_converter: Callable[[list], list] | None

    @property
    def task(self) -> tuple[str, str]:
        return self.taskfile, self.taskname

    def update(self, other: _TaskrunnerSettings):
        """
        Updates these settings with the other settings,
        replacing all values in `self` that are not `None`.
        """
        for field in fields(other):
            if value := getattr(other, field.name):
                setattr(self, field.name, value)


class QiCodeExperiment(BaseExperiment):
    """Experiment generating Pulses after the pattern of a predefined QiCode instruction List.

    :param controller: First parameter is the QiController itself

    :raises Exception: If more than 16 parameterized pulses are present
    """

    def __init__(
        self,
        controller: QiController,
        cell_list: list[QiCell],
        couplers: list[QiCoupler],
        sequencer_codes,
        averages: int = 1,
        for_range_list=[],
        cell_map: list[int] | None = None,
        coupler_map: list[int] | None = None,
        var_reg_map: dict[_QiVariableBase, dict[QiCell, int]] = {},
        data_collection="average",
        use_taskrunner=False,
    ):
        self.cell_list = cell_list
        self.couplers = couplers
        # The Variables for calculating a parametrized Pulse.
        super().__init__(controller)
        self._seq_instructions = sequencer_codes
        self.averages = averages
        self.for_range_list = for_range_list
        self.cell_map = cell_map
        self.coupler_map = coupler_map
        self._var_reg_map = var_reg_map
        self._data_collection = data_collection
        self.use_taskrunner = use_taskrunner
        self._data_handler_factory: (
            Callable[[DataProvider, list[QiCell], int], DataHandler] | None
        ) = None

        self._job_representation = "Unknown QiCodeExperiment"

        self._taskrunner: _TaskrunnerSettings | None = None
        self._update_taskrunner_settings_and_data_handler()

    def _update_taskrunner_settings_and_data_handler(self):
        self._update_taskrunner_settings()
        self._update_data_handler()

    def _update_taskrunner_settings(self):
        if not self.use_taskrunner:
            return

        params = (
            [
                self.averages,  # how many repetitions
                len(self.cell_list),  # number of cells
            ]
            # cells to address
            + self.cell_map
            # how many recordings for each cell
            + [cell.get_number_of_recordings() for cell in self.cell_list]
        )

        def converter_pass_through(boxes):
            return boxes

        def converter_averages(boxes):
            return [np.array(data) / self.averages for data in boxes]

        def converter_amp_pha(boxes):
            data = []
            for i in range(len(boxes) // 2):
                cplx = np.array(boxes[2 * i]) + 1j * np.array(boxes[2 * i + 1])
                data.append((np.abs(cplx) / self.averages, np.angle(cplx)))
            return data

        available_settings = {
            "average": _TaskrunnerSettings(
                "qicode/averaging.c",
                "QiCode[Avg]",
                params,
                TaskRunner.DataMode.INT32,
                converter_averages,
            ),
            "amp_pha": _TaskrunnerSettings(
                "qicode/averaging.c",
                "QiCode[Avg]",
                params,
                TaskRunner.DataMode.INT32,
                converter_amp_pha,
            ),
            "iqcloud": _TaskrunnerSettings(
                "qicode/iq_collect.c",
                "QiCode[IQ]",
                params,
                TaskRunner.DataMode.INT16,
                converter_pass_through,
            ),
            "raw": _TaskrunnerSettings(
                "qicode/timetrace.c",
                "QiCode[Raw]",
                params,
                TaskRunner.DataMode.INT32,
                converter_averages,
            ),
            "states": _TaskrunnerSettings(
                "qicode/state_collect.c",
                "QiCode[States]",
                params,
                TaskRunner.DataMode.UINT32,
                converter_pass_through,
            ),
            "counts": _TaskrunnerSettings(
                "qicode/state_count.c",
                "QiCode[Counts]",
                params,
                TaskRunner.DataMode.UINT32,
                converter_pass_through,
            ),
            "custom": _TaskrunnerSettings(
                "",
                "QiCode[Custom]",
                params,
                TaskRunner.DataMode.INT32,
                converter_pass_through,
            ),
        }
        if self._data_collection not in available_settings:
            options = ", ".join(available_settings.keys())
            raise RuntimeError(
                f"Invalid data collection option: '{self._data_collection}' (possible settings: {options})"
            )
        self._taskrunner = available_settings[self._data_collection]

    def _update_data_handler(self):
        self._data_handler_factory = DataHandler.get_factory_by_name(
            self._data_collection
        )
        if self._data_handler_factory is None:
            options = ", ".join(DataHandler.names())
            raise RuntimeError(
                f"Invalid data collection option: '{self._data_collection}' (possible settings: {options})"
            )

    def cell_iterator(self):
        for idx, sample_cell in enumerate(self.cell_list):
            yield idx, sample_cell, self.qic.cell[self.cell_map[idx]]

    def coupling_iterator(self):
        for idx, coupler in enumerate(self.couplers):
            yield coupler, self.qic.pulse_players[self.coupler_map[idx]]

    def _configure_readout(self, no_warn=False):
        """Overwrites the _configure_readout method of BaseExperiment class.
        Loads readout pulses of a sequence in successive readout triggersets.

        :param no_warn: currently not used here

        :raises Exception: if one uses more than 13 different readout pulses within the sequence.
        """
        for _, cell, qic_cell in self.cell_iterator():
            if len(cell.readout_pulses) > 13:
                raise RuntimeError(
                    "Number of readouts exceeded 13. Your program uses too many different pulses."
                )

            qic_cell.readout.reset_env_mem()
            for triggerset, pulse in enumerate(cell.readout_pulses):
                self.load_pulse(
                    pulse,
                    qic_cell.readout.triggerset[triggerset + 1],
                )  # loads the readout pulses in triggersets

                if pulse.is_variable_length:
                    # special pulse to end a parametrized readout
                    self.load_pulse(
                        QiPulse(4e-09, amplitude=0),
                        qic_cell.readout.triggerset[Sequencer.CHOKE_PULSE_INDEX],
                    )

            try:
                qic_cell.readout.if_frequency = cell.initial_readout_frequency
                qic_cell.recording.internal_frequency = cell.initial_readout_frequency
            except AttributeError:
                pass  # No readout pulses present -> just leave the current setting

            qic_cell.recording.recording_duration = cell.recording_length
            qic_cell.recording.trigger_offset = cell.initial_recording_offset

    def _configure_drive_pulses(self):
        """Overwrites the _configure_drive_pulses method of BaseExperiment class.
        loads manipulation pulses of the QiCell in successive manipulation triggersets.

        :raises Exception: if one uses more than 13 different manipulation pulses within the sequence.
        """
        for _, cell, qic_cell in self.cell_iterator():
            if len(cell.manipulation_pulses) > 13:
                raise RuntimeError(
                    "Number of pulses exceeded 13. Your program uses too many different pulses."
                )
            qic_cell.manipulation.reset_env_mem()
            for triggerset, pulse in enumerate(cell.manipulation_pulses):
                self.load_pulse(
                    pulse,
                    qic_cell.manipulation.triggerset[triggerset + 1],
                )  # loads manipulation pulses in triggersets
                if pulse.is_variable_length:
                    # special pulse to end a parametrized readout
                    self.load_pulse(
                        QiPulse(4e-09, amplitude=0),
                        qic_cell.manipulation.triggerset[Sequencer.CHOKE_PULSE_INDEX],
                    )

            try:
                qic_cell.manipulation.if_frequency = cell.initial_manipulation_frequency
            except AttributeError:
                pass  # No manipulation pulses present -> just leave the current setting

    def _configure_digital_triggers(self):
        for _, cell, qic_cell in self.cell_iterator():
            qic_cell.digital_trigger.clear_trigger_sets()
            for index, trig_set in enumerate(cell.digital_trigger_sets):
                # In the array, triggers are indexed starting from 0. However, index 0 is reserved and cannot be used.
                # Therefore, we start at index # 1. This is also accounted for in QiCell.add_digital_trigger()
                qic_cell.digital_trigger.set_trigger_set(index + 1, trig_set)

    def _configure_couplers(self):
        for coupler, pulse_player in self.coupling_iterator():
            pulse_player.reset()
            for index, pulse in enumerate(coupler.coupling_pulses):
                # In the array, triggers are indexed starting from 0. However, index 0 is reserved and cannot be used.
                pulse_player.pulses[index + 1] = pulse(pulse_player.sample_rate)

    def _configure_sequences(self):
        """Overwrites the _configure_sequences method of BaseExperiment class.
        This function generates the assembler code for the sequencer and loads it on the platform.
        """
        for index, _, qic_cell in self.cell_iterator():
            qic_cell.sequencer.load_program_code(self._seq_instructions[index])

        # Update the string representation of the last job in the QiController
        self.qic._last_qijob = self._job_representation

    def _configure_taskrunner(self):
        """This method configures the taskrunner for the experiment."""
        if self.use_taskrunner:
            if self.qic.taskrunner is not None:
                self.qic.taskrunner.load_task_source(*self._taskrunner.task)
                self.qic.taskrunner.set_param_list(self._taskrunner.params)
            else:
                raise NotImplementedError("Taskrunner is not available on this system")

    def init_variable(self, name: str, value: float | int):
        """
        Initializes a variable to a certain value at any point in the execution cycle.

        Example
        -------
        .. code-block:: python

            qic: QiController = ...
            with QiJob() as job:
                q = QiCells(1)
                hold = QiVariable(int, name="hold")
                with If(hold == 1):
                    Play(q[0], QiPulse(length="cw", frequency=30e6))
                with Else():
                    Play(q[0], QiPulse(length="off", frequency=30e6))

            exp = job.create_experiment(qic)
            exp.init_variable("hold", 1)
            exp.run()  # plays a continuous pulse
            exp.init_variable("hold", 0)
            exp.run()  # stops

        :param name: The name of the variable. Is the same name that was used when creating the variable
        :param value: The value of the variable.
        """
        counter = 0
        for var, cells in self._var_reg_map.items():
            if var.name != name:
                continue
            for var_cell, reg in cells.items():
                for _, cell, qic_cell in self.cell_iterator():
                    if cell != var_cell:
                        continue
                    if var.type == QiType.NORMAL:
                        if math.floor(value) != value:
                            raise ValueError(
                                f"Cannot set variable {name} to {value} because '{name}' is of type int and '{value}'"
                                " cannot be converted to an integer without loosing precision"
                            )
                        qic_cell.sequencer.register[reg] = math.floor(value)
                    elif var.type == QiType.TIME:
                        qic_cell.sequencer.register[reg] = util.conv_time_to_cycles(
                            value
                        )
                    elif var.type == QiType.FREQUENCY:
                        qic_cell.sequencer.register[reg] = (
                            util.conv_freq_to_nco_phase_inc(value)
                        )
                    else:
                        raise RuntimeError(
                            f"Variable {name} is unknown. Is the program not compiled?"
                        )
                    counter += 1
        if counter == 0:
            raise ValueError(
                "Variable could not be initialized! Check if it exists and is used."
            )

    def get_current_loop(self):
        """Generates the current loop counter for cell_0,
        by comparing current register and program counter values to the saved ForRangeEntries.
        TODO implement Progress calculation for all cells."""
        if len(self.cell_map) < 1:
            raise RuntimeError("No cells provided")
        cid = self.cell_map[0]  # Use first cell in job to calculate progress
        registers = self.qic.cell[cid].sequencer.register.get_all()
        pc = self.qic.cell[cid].sequencer.program_counter

        return ForRangeEntry.calculate_current_loop(
            self.for_range_list[0], registers, pc
        )

    def _record_internal_taskrunner(
        self,
        count,
        name,
        start_callback=None,
        data_mode=TaskRunner.DataMode.INT32,
    ):
        if self.qic.taskrunner is None:
            raise NotImplementedError("Taskrunner is not available on this system")
        self._create_progress(count, "Averages")

        total = ForRangeEntry.get_total_loops(self.for_range_list[0])
        if total > 1:
            self._create_progress(total, name)

        try:
            self.qic.taskrunner.start_task()

            if start_callback is not None:
                start_callback()

            while self.qic.taskrunner.busy:
                time.sleep(self.sleep_delay_while_busy)
                # Test if errors happened during execution
                self.qic.check_errors()

                # Update the progress bar
                self._set_progress(self.qic.taskrunner.task_progress, "Averages")
                if total > 1:
                    self._set_progress(self.get_current_loop(), name)

            # Finish progress bar
            self._set_progress(count, "Averages")
            if total > 1:
                self._set_progress(total, name)
        finally:
            if self.qic.taskrunner.busy:
                self.qic.taskrunner.stop_task()

            for _, _, qic_cell in self.cell_iterator():
                qic_cell.sequencer.stop()

        # TODO: Better always fetch data boxes and change the empty data check inside...
        if sum(cell.get_number_of_recordings() for cell in self.cell_list) > 0:
            return self.qic.taskrunner.get_databoxes_with_mode(mode=data_mode)
        else:
            return []  # Empty (no recordings requested)

    def _record_internal_plugin(self, averages, cells, recordings, data_collection):
        self._create_progress(averages, "Averages")

        def progress_callback(progress):
            self._set_progress(progress, "Averages")

        result = self.qic.cell.run_experiment(
            averages=averages,
            cells=cells,
            recordings=recordings,
            data_collection=data_collection,
            progress_callback=progress_callback,
        )
        # Last progress update already sets it to max, so finish is not necessary

        return result

    def _record_internal(self):
        for _, _, qic_cell in self.cell_iterator():
            qic_cell.sequencer.averages = 1
            qic_cell.sequencer.start_address = 0

        if self.use_taskrunner:
            result = self._record_internal_taskrunner(
                self.averages,
                name="QiCode",
                data_mode=self._taskrunner.data_mode,
            )

            return self._taskrunner.data_converter(result)

        result = self._record_internal_plugin(
            averages=self.averages,
            cells=self.cell_map,
            recordings=[cell.get_number_of_recordings() for cell in self.cell_list],
            data_collection=self._data_collection,
        )

        return result

    def load_pulse(self, pulse: QiPulse, triggerset: TriggerSet):
        """loads qkit pulse() in the triggerset of the QiController

        :param pulse: The qkit Pulse() instance.
        :param triggerset: Instance of class TriggerSet of the Pulsegenerator.

        :raises Exception: if IQ_frequency is given. Thus it has to be modified in the pulse_generator
        """

        envelope = pulse(samplerate)
        # check if holding the last value of the amplitude array.
        hold = pulse.is_variable_length or pulse.hold

        if len(envelope) % 4 != 0:
            # adds fill values to the end of the pulse if its not multiple of 4
            fill = envelope[-1] if hold else 0.0
            envelope = np.append(envelope, [fill] * (4 - len(envelope) % 4))

        # If phase is a constant phase = pulse.phase, otherwise phase = 0
        if isinstance(pulse.phase, _QiVariableBase):
            phase = 0
        else:
            phase = pulse.phase

        triggerset.load_pulse(  # if const=pulse.phase, dyn =0
            envelope, hold=hold, shift_phase=pulse.shift_phase, phase=phase
        )

    def run(self, start_lo: bool = True):
        self.configure()

        if start_lo:
            # turn on the output for every module
            try:
                for _, _, qic_cell in self.cell_iterator():
                    qic_cell.readout.local_oscillator.on()
                    qic_cell.manipulation.local_oscillator.on()
            except AttributeError:
                pass

        try:
            result = self.record()
        finally:
            if start_lo:
                # turn off the output for every module
                try:
                    for _, _, qic_cell in self.cell_iterator():
                        qic_cell.readout.local_oscillator.off()
                        qic_cell.manipulation.local_oscillator.off()
                except AttributeError:
                    pass

        return result

    def record(self):
        """Starts the experiment recording and returns the result.

        Notes
        -----
        This method does not configure the QiController. It expects that
        `BaseExperiment.configure` has been called in advance. If you are
        unsure if to use this method or `BaseExperiment.run`, the latter one is
        probably the right option.

        :returns:
            The measurement data collected during the experiment as returned
            by the `BaseExperiment._recording_internal` method.

            See :meth:`.BaseExperiment.run` for a more detailed description.

        """
        if not self._configure_called:
            raise RuntimeError(
                "When calling record(), configure() has to be called independently before (otherwise use run())."
            )
        # Clear all errors that might be existing from previous experiments
        self.qic.clear_errors()

        for _, _, qic_cell in self.cell_iterator():
            qic_cell.readout.nco_enable(True)
            qic_cell.manipulation.nco_enable(True)

        try:
            result = self._record_internal()
        finally:
            for _, _, qic_cell in self.cell_iterator():
                qic_cell.sequencer.stop()
                qic_cell.readout.nco_enable(False)
                qic_cell.manipulation.nco_enable(False)

        # To prevent any further measurements before qubit is in ground state
        # we ensure we wait long enough
        while self.qic.cell.busy:
            pass

        # Check if some errors have been missed but do not raise an exception
        self.qic.check_errors(raise_exceptions=False)

        data_provider = DataProvider.create(result, self.use_taskrunner)
        data_handler: DataHandler = self._data_handler_factory(
            data_provider, self.cell_list, self.averages
        )
        data_handler.process_results()

        return result

    def time_range(self, min: float, max: float, step: float):
        return list(
            map(
                util.conv_cycles_to_time,
                np.arange(
                    util.conv_time_to_cycles(min),
                    util.conv_time_to_cycles(max),
                    util.conv_time_to_cycles(step),
                ),
            )
        )

    @property
    def readout(self):
        """A readout object obtaining data of two recording modules
        simultaneously for Qkits Measure_td class.

        See :class:`ExperimentReadout` for more information.
        """
        if self._data_collection in ["amp_pha", "average"]:
            # Same experiment, but Qkit expects the data as amplitude & phase values
            self._data_collection = "amp_pha"
            self._update_taskrunner_settings_and_data_handler()
        else:
            raise NotImplementedError(
                "Currently only normal averaging is supported with QiCode and Qkit"
            )
        return ExperimentReadout(self)

    @property
    def qkit_sample(self):
        """This object mimics a qkit sample to neatlessly interface with the Qkit
        measurement classes. Just pass this sample to the class. It contains everything
        Qkit needs to perform the experiment.
        """
        sample = SampleObject()
        sample.readout = self.readout
        return sample

    def configure_task(
        self,
        file: str,
        params: list,
        data_converter: Callable[[list], list],
        data_handler: Callable[[list[QiCell], DataProvider], None],
        data_mode=TaskRunner.DataMode.INT32,
    ):
        """Loads custom file for taskrunner

        :param file: your c-File containing the desired measurement process
        :param params: your parameters for the measuremnt
        :param data_converter: function that formats the returned data
        :param data_handler: function that processes the recording data, usually splitting it up and assigning
            it to the correct box.
        """
        if isinstance(data_mode, str):
            data_mode = TaskRunner.DataMode[data_mode.upper()]

        self.use_taskrunner = True
        self._taskrunner = _TaskrunnerSettings(
            file, "QiCode[Custom]", params, data_mode, data_converter
        )
        if data_handler is not None:
            self._data_handler_factory = DataHandler.get_custom_wrapper_factory(
                data_handler
            )
        self._data_collection = "custom"

        self.configure()
