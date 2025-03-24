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
"""Module providing a base class for experiments with the QiController.

The base class offers rich functionality that can be utilized by child classes
implementing the experiments. This also includes integration with Qkit.

.. note::
    If you plan on implementing your own experiment, check out the existing ones
    and have a look at the source code of `BaseExperiment` to learn about the
    private methods and capabilities it offers.

"""

from __future__ import annotations

import time
import warnings
from typing import TYPE_CHECKING

import numpy as np

import qiclib.packages.utility as util
from qiclib.coding.sequencercode import SequencerCode
from qiclib.hardware.taskrunner import TaskRunner
from qiclib.packages.qkit_polyfill import QKIT_ENABLED, Progress_Bar

if TYPE_CHECKING:
    from qiclib.hardware.controller import QiController


class BaseExperiment:
    """Base class to create experiments with the QiController.

    It already provides some extra functionality that can be used to adapt
    experiments (like qubit state initialization using active reset, taskrunner
    support, existing pulse dictionary etc.).
    Every method can be overwritten by child classes in order to achieve the
    desired experiment procedure.

    When executed on the QiController, this experiment will perform a single
    readout operation (pulse + recording) and return the demodulated result as
    amplitude and phase tuple.

    :param controller:
        The QiController instance on which the experiment shall be executed.
    :param cell: int
        On which cell to perform the experiment, defaults to 0 (i.e. first cell).

    :ivar show_progress_bar:
        Enable/disable the Qkit progress bar for the experiment
        (defaults to True).
    :ivar drag_amplitude:
        If given, rectangular pulses will be replaced by DRAG ones with
        given drag_amplitude.
    :ivar use_taskrunner:
        If the experimental sequence should be controlled by taskrunner
        (defaults to False).
    :ivar iteration_averages:
        Amount of experiment repetitions for averaging when `use_taskrunner`
        is `True` (defaults to 1, so no repetitions).
    :ivar sleep_delay_while_busy:
        How long to wait between repeated queries of the experiment status from
        the Taskrunner. Only relevant when `use_taskrunner = True`.
        (defaults to 0.2, thus queries the status every 200ms)
    """

    def __init__(self, controller: QiController, cell=0):
        self._name = self.__class__.__name__
        self.qic = controller
        self.cell_index = cell

        # Option to enable/disable the Qkit progress bar
        self.show_progress_bar = True

        # Possibility to define a DRAG amplitude. This will convert rectangular pulses to DRAG ones.
        self.drag_amplitude = None  # type: float

        # Options to perform an experiment on the Taskrunner in order to speed it up
        # and enable the reduction of per point averages (controller.sequencer.averages)
        # in favor of more iteration_averages (per line/experiment run averages) on the Taskrunner.
        self.use_taskrunner = False
        self.iteration_averages = 1
        self.sleep_delay_while_busy = 0.2

        # Internal attributes
        self._pc_dict: dict[str, int] = {}
        self._code = SequencerCode(self._pc_dict)
        self._progress_bar: dict[str, Progress_Bar] = {}

        self._initial_state = None
        self._initial_delay = 0
        self._repetition_time = None
        self._initial_phase_reset = False

        # If this experiment supports streaming of databoxes
        self._databox_streaming = False
        self._databoxes: list[list[int]] = []  # Fetched databoxes

        # check if configure was called
        self._configure_called = False

    #############################################
    # Public methods and properties
    #############################################

    @property
    def cell(self):
        """The QiController cell on which this experiment acts.

        It can be changed by overwriting `cell_index` property or by passing
        the `cell` parameter to the constructor (if available).
        """
        return self.qic.cell[self.cell_index]

    @property
    def readout(self):  # Py3.7: -> ExperimentReadout:
        """A readout object for Qkit's Measure_td class.

        See `ExperimentReadout` for more information.
        """
        return ExperimentReadout(self)

    def run(self, start_lo: bool = True):
        """Start the execution of the experiment.

        It first loads everything onto the QiController by calling
        `BaseExperiment.configure` and then performs the measurement part by
        executing `BaseExperiment.record`.

        If specified, it also takes care of external local oscillators.

        :param start_lo:
            If external LOs should be turned on and off for the experiment
            (defaults to True).
            External LOs can be defined in the pulse generators (see
            `qiclib.hardware.pulsegen.PulseGen` for more information):

            - `qic.readout.local_oscillator`
            - `qic.manipulation.local_oscillator`

            If they are undefined, turning them on and off will be skipped.

        :return:
            The measurement data collected during the experiment as returned
            by the `BaseExperiment._recording_internal` method.

            The general structure should always be a list of tuples, with
            every tuple in the list corresponding to one readout frequency
            respective qubit.

            In the `BaseExperiment` implementation, the return value is of the
            following structure:

            `[ ( amplitude value , phase value ) ]`

            Experiments with 1D parameter variations typically return arrays
            instead of single values inside the tuple.

        """
        self.configure()

        if start_lo:
            # turn on the output for every module
            try:
                self.cell.readout.local_oscillator.on()
                self.cell.manipulation.local_oscillator.on()
            except AttributeError:
                pass

        try:
            result = self.record()
        finally:
            if start_lo:
                # turn off the output for every module
                try:
                    self.cell.readout.local_oscillator.off()
                    self.cell.manipulation.local_oscillator.off()
                except AttributeError:
                    pass

        return result

    def configure(self):
        """Configure the experimental procedure on the QiController.

        Prepares everything for the execution of the experiment including:

        - Creating pulse envelopes and loading them into the pulse generators
        - Generating sequencer code and writing it onto the sequencer
        - Setting all necessary registers including delays etc.
        - Configuring the taskrunner (if necessary)

        In the default implementation, a range of standard pulses is loaded.
        Child experiments can use these pulses in their own sequence by
        overwriting the `_configure_sequences` method.

        To gain more fine-granular control over the configuration process,
        the following internal methods can be overwritten:

        - :meth:`_configure_readout`: Configures recording module and readout pulse
        - :meth:`_configure_drive_pulses`: Configures the manipulation pulses
        - :meth:`_configure_sequences`: Configures the experiment sequences
        - :meth:`_configure_taskrunner`: Configures the taskrunner if necessary
        """
        # check if this method was called
        self._configure_called = True

        # All methods can be overwritten depending on the needs of the actual experiments
        self._configure_readout()
        self._configure_drive_pulses()
        self._configure_sequences()
        self._configure_taskrunner()
        self._configure_digital_triggers()
        self._configure_couplers()

    def record(self):
        """Starts the experiment recording and returns the result.

        .. note::
            This method does not configure the QiController. It expects that
            :meth:`BaseExperiment.configure` has been called in advance. If you are
            unsure if to use this method or :meth:`BaseExperiment.run`, the latter one is
            probably the right option.

        :return:
            The measurement data collected during the experiment as returned
            by the :meth:`BaseExperiment._recording_internal` method.

            See :meth:`BaseExperiment.run` for a more detailed description.

        """
        if not self._configure_called:
            raise RuntimeError(
                "When calling record(), configure() has to be called independently before (otherwise use run())."
            )
        if self.use_taskrunner and not self.qic.taskrunner_available:
            raise NotImplementedError("This experiment requires the Taskrunner to work")
        # Clear all errors that might be existing from previous experiments
        self.qic.clear_errors()

        self.cell.readout.nco_enable(True)
        self.cell.manipulation.nco_enable(True)

        try:
            result = self._record_internal()
        finally:
            self.cell.readout.nco_enable(False)
            self.cell.manipulation.nco_enable(False)

        # To prevent any further measurements before qubit is in ground state
        # we ensure we wait long enough
        while self.cell.busy:
            pass

        # Check if some errors have been missed but do not raise an exception
        self.qic.check_errors(raise_exceptions=False)

        return result

    def configure_readout_pulse(
        self,
        length: float,
        recording_window: float | None = None,
        no_warn: bool = False,
    ):
        """Configures a readout pulse with a given length.

        .. note::
            This does not adjust for the delay of the readout pulse through the
            setup (:meth:`qiclib.hardware.recording.Recording.trigger_offset`). The delay
            has to be adjusted separately.
            To perform an automatic calibration, see e.g. the
            :meth:`qiclib.experiment.autoconf_readout.AutoconfReadout` experiment.

        :param length:
            The pulse length of the standard readout pulse in seconds.
        :param recording_window:
            The duration of the recording window in seconds
            (defaults to be the same as the pulse length).
        :param no_warn:
            If warnings should be suppressed when default parameters are used
            in the case the sample object has no corresponding value present
            (defaults to False, i.e. warnings will be displayed).

        """
        if recording_window is None:
            recording_window = length

        self.qic.sample.rec_pulselength = length
        self.qic.sample.rec_duration = recording_window

        # If unset, initialize values by some defaults
        try:
            self.qic.sample.rec_offset
        except AttributeError:
            self.qic.sample.rec_offset = 0
            if not no_warn:
                warnings.warn(
                    "Recording offset was unset and initialized to 0. Do not forget to adapt!"
                )

        try:
            self.qic.sample.rec_shift_offset
        except AttributeError:
            self.qic.sample.rec_shift_offset = 0
            if not no_warn:
                warnings.warn(
                    "Recording value shift offset was unset and initialized to 0."
                )

        try:
            self.qic.sample.rec_shift_average
        except AttributeError:
            self.qic.sample.rec_shift_average = 0
            if not no_warn:
                warnings.warn(
                    "Recording average shift was unset and initialized to 0. "
                    + "For experiments with more than 60k averages this might cause overflow!"
                )

        if self.cell.recording.interferometer_mode:
            try:
                self.qic.sample.rec_ref_delay
            except AttributeError:
                self.qic.sample.rec_ref_delay = util.conv_cycles_to_time(4)
            if not no_warn:
                warnings.warn(
                    "Reference delay for interferometer mode was unset and initialized to 4 cycles. "
                    + "Do not forget to adapt!"
                )

        # Load everything onto the platform
        self._configure_readout(no_warn=no_warn)

    def set_qubit_initialization(
        self,
        state: int | None = 0,
        delay: float = 0,
        repetition_time: float | None = None,
        phase_reset: bool = False,
    ):
        """Enables an active reset operation prior to the regular experiment
        execution.

        .. note::
            This requires single-shot readout and sufficient state discrimination
            in order to work. The configuration for the state detection
            (:meth:`qiclib.hardware.recording.Recording.state_config`) needs to be
            configured and checked beforehand.

        :param state:
            The state in which the qubit should be initialized.
            None disables the reset sequence.
        :type state: 0 | 1 | None, optional
        :param delay:
            The delay after the active reset initialization and before the
            actual experiment routine starts, in seconds
            (defaults to 0, i.e. no extra delay).
        :param repetition_time: float
            The delay after the experiment for the qubit state to relax in
            seconds (defaults to the standard `T_rep` time as given in the
            `qiclib.hardware.controller.QiController.sample`).

            As a reset operation can drastically speed up this process, this
            can be reduced as far as desired.

            .. note:: Physical restrictions might become relevant
                Be aware that physical effects in your sample might set a lower
                limit on this value, e.g. if the ringdown of the readout
                resonator is taking longer than the reset operation.
        :param phase_reset: bool, optional
            If the phase of manipulation and readout pulses should be synced
            again after the active reset (defaults to False).

            This results in an additional NCO Sync operation right before the
            regular experiment sequence starts.

        """
        if state is not None and state != 0 and state != 1:
            raise ValueError("Parameter `state` needs to be either 0, 1 or None.")
        if not isinstance(delay, (float, int)) or delay < 0:
            raise ValueError(
                "Parameter `delay` needs to be a non-negative time in seconds."
            )
        if repetition_time is not None and (
            not isinstance(repetition_time, (float, int)) or repetition_time < 0
        ):
            raise ValueError(
                "Parameter `repetition_time` needs to be None or a non-negative time in seconds."
            )

        self._initial_state = state
        self._initial_delay = delay
        self._repetition_time = repetition_time
        self._initial_phase_reset = phase_reset

    ################################################
    # Internal properties to access specific stuff
    ################################################

    @property
    def _readout_delay(self):
        """The duration a readout operation will take until the result is calculated on the QiController."""
        return (
            self.cell.recording.trigger_offset
            + self.cell.recording.recording_duration
            + util.conv_cycles_to_time(8)
        )

    @property
    def _p(self):
        """Dictionary of manipulation pulses.

        Alias for `controller.manipulation.pulses`..."""
        return self.cell.manipulation.pulses

    @property
    def _r(self):
        """Dictionary of readout pulses.

        Alias for `controller.readout.pulses`..."""
        return self.cell.readout.pulses

    ################################################
    # Internal configuration of the experiment
    ################################################

    def _configure_readout(self, pulses=None, no_warn=False):
        # Test if values to configure the readout are in the sample object
        try:
            self.qic.sample.rec_pulselength
        except AttributeError as e:
            raise AttributeError(
                "Readout pulse length has to be defined in the sample object! Please configure the readout"
            ) from e

        # If phase offset is unset initialize by default value
        try:
            self.qic.sample.rec_phase
        except AttributeError:
            self.qic.sample.rec_phase = 0

        self.cell.readout.load_pulses(
            pulses
            or {
                "Pulse": {"trigger": 1, "length": self.qic.sample.rec_pulselength},
                "Tone on": {
                    "trigger": 13,
                    "length": util.conv_cycles_to_time(1),
                    "hold": True,
                },
                "Tone off": {
                    "trigger": 14,
                    "length": util.conv_cycles_to_time(1),
                    "amplitude": 0,
                },
            }
        )

        try:
            self.cell.readout.if_frequency = self.qic.sample.rec_if_frequency
        except AttributeError as e:
            if not no_warn:
                warnings.warn(
                    "Recording IF frequency is not set in sample object. "
                    + "The current settings will be used. Be aware."
                    + f"\n({e})"
                )

        self.cell.recording.load_configuration(self.qic.sample, no_warn=no_warn)

    def _configure_drive_pulses(self, pulses=None, no_warn=False):
        # If pulses is None, then set default configuration suitable for most experiments
        self.cell.manipulation.load_pulses(
            pulses
            or {
                "Rx pi": {
                    "trigger": 1,
                    "length": self.qic.sample.tpi,
                    "amplitude": 1,
                    "phase": 0,
                },
                "Rx pi/2": {
                    "trigger": 2,
                    "length": self.qic.sample.tpi2,
                    "amplitude": 1,
                    "phase": 0,
                },
                "Ry pi": {
                    "trigger": 3,
                    "length": self.qic.sample.tpi,
                    "amplitude": 1,
                    "phase": np.pi / 2,
                },
                "Ry pi/2": {
                    "trigger": 4,
                    "length": self.qic.sample.tpi2,
                    "amplitude": 1,
                    "phase": np.pi / 2,
                },
                "Rx -pi": {
                    "trigger": 5,
                    "length": self.qic.sample.tpi,
                    "amplitude": -1,
                    "phase": 0,
                },
                "Rx -pi/2": {
                    "trigger": 6,
                    "length": self.qic.sample.tpi2,
                    "amplitude": -1,
                    "phase": 0,
                },
                "Ry -pi": {
                    "trigger": 7,
                    "length": self.qic.sample.tpi,
                    "amplitude": -1,
                    "phase": np.pi / 2,
                },
                "Ry -pi/2": {
                    "trigger": 8,
                    "length": self.qic.sample.tpi2,
                    "amplitude": -1,
                    "phase": np.pi / 2,
                },
                "Drive on": {
                    "trigger": 13,
                    "length": util.conv_cycles_to_time(1),
                    "hold": True,
                },
                "Drive off": {
                    "trigger": 14,
                    "length": util.conv_cycles_to_time(1),
                    "amplitude": 0,
                },
            }
        )

        try:
            self.cell.manipulation.if_frequency = self.qic.sample.manip_if_frequency
        except AttributeError as e:
            if not no_warn:
                warnings.warn(
                    "Manipulation IF frequency is not set in sample object. "
                    + "The current settings will be used. Be aware."
                    + f"\n({e})"
                )

    def _configure_sequences(self):
        """This function implements experiment specific pulse sequences.

        Method _build_code_from_sequences() can be used here.
        """
        self._built_code_from_sequences(
            {"default": lambda code: None}  # Everything will be added by wrapper
        )

    def _configure_digital_triggers(self):
        pass

    def _configure_couplers(self):
        pass

    def _configure_taskrunner(self):
        """This method configures the taskrunner for the experiment.

        In it's default configuration, a versatile standard task to use with `use_taskrunner=True` is loaded.
        """
        if self.use_taskrunner:
            if self.qic.taskrunner is not None:
                self.qic.taskrunner.load_task_source(
                    "base_experiment_task.c", "base-task"
                )
            else:
                raise NotImplementedError("Taskrunner is not available on this system")

    def _built_code_from_sequences(
        self, code_factories, add_readout=True, add_sync=True
    ):
        """Creates the SequencerCode based on the code factories describing the experiment."""
        # Create a SequencerCode object that child classes can write to
        self._pc_dict = {}
        code = SequencerCode(self._pc_dict)

        for key in code_factories:
            # Add reference with key as name
            code.reference(key)
            self._add_code_sequence(code, code_factories[key], add_readout, add_sync)

        # The final code is loaded onto the QiController
        self.cell.sequencer.load_program(code, self._name)

    def _add_code_sequence(self, code, code_factory, add_readout=True, add_sync=True):
        """Adds the sequence described in `code_factory` to the SequencerCode `code`"""
        if add_sync:
            code.trigger_nco_sync()

        # If the user wants it, the initial state can be prepared
        if self._initial_state is not None:
            pi_pulse = self._p["Rx pi"]
            code.trigger_active_reset(
                pi_pulse["trigger"], pi_pulse["length"], self._initial_state
            )
            if self._initial_delay > 0:
                if self._initial_delay < (1 << 15) * 1e-9:
                    code.trigger_immediate(delay=self._initial_delay)
                else:
                    # Too large for TRI command, have to sacrifice a delay register
                    self.cell.sequencer.set_delay_register(29, self._initial_delay)
                    code.trigger_registered(29)
            if self._initial_phase_reset:
                code.trigger_nco_sync()

        # Factory adds instructions to SequencerCode object
        code_factory(code)

        if add_readout:
            # No final readout is configured, so it will be configured here including an appropriate delay
            code.trigger_readout(self._readout_delay)

        # For experiments deriving from this base class, END command is appended here
        repetition_time = self._repetition_time
        if repetition_time is None:
            repetition_time = self.qic.sample.T_rep
        code.end_of_experiment(repetition_time)

    ################################################
    # Internal recording of the experiment
    ################################################

    def _record_internal(self):
        """This method describes the experimental procedure on the measurement pc.

        Here, it provides a standard measurement procedure sufficient for simple experiments.
        If more complex work flows are needed, overwrite in concrete experiment class.
        """
        # Start the experiment at the first sequencer command
        self.cell.sequencer.start_at(self._pc_dict.get("default", 0))

        return self._measure_amp_pha()

    def _record_internal_1d(self, variable, name, inner_function):
        """Template for generic experiment looping over one *variable* calling *inner_function* each time.

        :param variable:
            Array with the variable values to loop over. Will be passed to inner_function.
        :param name:
            What the variable should be called, e.g. "Durations".
        :param inner_function:
            Function that is called in the loop
            and has to perform the single experiment execution excluding reading the result.
            It should contain the sequencer.start_at(...) command or similar.
        :type inner_function: ((value: any) => void)

        :return: *(amplitudes, phases)* as arrays with an entry for each element of *variable*.
        """
        count = len(variable)
        delay_regs_used = len(inner_function(variable[0]).get("delay_registers", []))

        if self.iteration_averages != 1 and not self.use_taskrunner:
            raise ValueError(
                "Iteration averages can only be set when using the taskrunner!"
            )

        if self.use_taskrunner:
            if self.qic.taskrunner.loaded_task != "base-task":
                raise RuntimeError(
                    "The experiment needs to be configured! (Esp. if use_taskrunner option changed.)"
                )

            # Write parameters of the task to the taskrunner
            seq_pc = []
            durations = []

            for value in variable:
                experiment_settings = inner_function(value)
                seq_pc.append(experiment_settings["sequencer_start"])
                for delay_reg in range(delay_regs_used):
                    durations.append(
                        util.conv_time_to_cycles(
                            experiment_settings["delay_registers"][delay_reg]
                        )
                    )

            parameters = [
                self.iteration_averages,
                count,
                delay_regs_used,
                self.cell_index,
                *seq_pc,
                *durations,
            ]
            self.qic.taskrunner.set_param_list(parameters)

            data = np.asarray(
                self._record_internal_taskrunner(count * self.iteration_averages, name)
            )

            data_complex = data[0] + 1j * data[1]
            amp = np.abs(data_complex) / (
                1.0 * self.iteration_averages * self.cell.sequencer.averages
            )
            pha = np.angle(data_complex)

            return [(amp, pha)]
        else:
            sig_amp = np.zeros(count)
            sig_pha = np.zeros(count)

            # Looping through the different values of the variable
            self._create_progress(count, name)
            for idx, value in enumerate(variable):
                experiment_settings = inner_function(value)

                try:
                    for delay_reg in range(delay_regs_used):
                        self.cell.sequencer.set_delay_register(
                            (delay_reg + 1),
                            experiment_settings["delay_registers"][delay_reg],
                        )  # delay_reg + 1, so reg0 is not used
                except AttributeError:
                    pass

                self.cell.sequencer.start_at(experiment_settings["sequencer_start"])

                amp, pha = self._measure_amp_pha()[0]
                sig_amp[idx] = amp
                sig_pha[idx] = pha

                # Waiting until sequencer is finished
                while self.cell.busy:
                    pass

                self._iterate_progress(name)

            return [(sig_amp, sig_pha)]

    def _record_internal_taskrunner(
        self,
        count,
        name,
        allow_partial_data=False,
        start_callback=None,
        data_mode=TaskRunner.DataMode.INT32,
    ):
        self._create_progress(count, name)
        try:
            self.qic.taskrunner.start_task()

            if start_callback is not None:
                start_callback()

            while self.qic.taskrunner.busy:
                time.sleep(self.sleep_delay_while_busy)
                # Test if errors happened during execution
                self.qic.check_errors()
                # Update the progress bar
                self._set_progress(self.qic.taskrunner.task_progress, name)

            self._set_progress(count, name)
        except KeyboardInterrupt:
            msg = (
                "Interrupted while data collection. "
                + f"Only obtained {self.qic.taskrunner.task_progress} results."
            )
            warnings.warn(msg)
            if not allow_partial_data:
                raise
        finally:
            if self.qic.taskrunner.busy:
                self.qic.taskrunner.stop_task()

            self.cell.sequencer.stop()

        return self.qic.taskrunner.get_databoxes_with_mode(
            mode=data_mode, require_done=(not allow_partial_data)
        )

    def _record_databox_start(self, count, name="Databoxes"):
        if not self._databox_streaming:
            raise Warning("Experiment does not support databox streaming!")
        self._databoxes = []
        self.qic.taskrunner.start_task()
        self._create_progress(count, name)

    def _record_databox_fetch(
        self, data_mode=TaskRunner.DataMode.INT32, name="Databoxes"
    ):
        try:
            if not self._databoxes:
                # No remaining data from last call -> get new one
                while self.qic.taskrunner.databoxes_available == 0:
                    if self.qic.taskrunner.task_done:
                        raise Warning(
                            "Task already finished but no more data. Is Qkit Iteration count right?"
                        )
                    # Test if errors happened during execution
                    self.qic.check_errors()
                    # Update the progress bar
                    self._set_progress(self.qic.taskrunner.task_progress, name)
                    # Wait before retrying
                    time.sleep(self.sleep_delay_while_busy)
                # Retrieve new databoxes
                self._databoxes = self.qic.taskrunner.get_databoxes_with_mode(
                    mode=data_mode, require_done=False
                )
        except KeyboardInterrupt:
            # TODO Make sure that already fetched data is stored?
            if self.qic.taskrunner.busy:
                self.qic.taskrunner.stop_task()

            self.cell.sequencer.stop()
            raise

        # Update progress bar (at least once each method call)
        self._set_progress(self.qic.taskrunner.task_progress, name)
        return self._record_databox_extract()

    def _record_databox_extract(self):
        if not self._databoxes:
            raise ValueError("No databoxes available to extract data from...")
        # By default just remove and return the first databox in the list
        return self._databoxes.pop(0)

    def _record_databox_finish(self, name="Databoxes"):
        if self.qic.taskrunner.busy:
            self.qic.taskrunner.stop_task()
            warnings.warn(
                "Recording finished but taskrunner still busy. Stopped the task."
            )
        if self._databoxes:
            warnings.warn("Not all collected data was fetched!")
        self._finish_progress(name)

    def _measure_amp_pha(self, wait_for_ready=True):
        # Wait until all commands are triggered
        # TODO shouldnt we also wait for RecModule here?
        if wait_for_ready:
            try:
                while self.cell.busy:
                    pass
            except KeyboardInterrupt:
                self.cell.sequencer.stop()
                raise

        # Read the fourier coefficients for I and Q (summed up)
        read_i, read_q = self.cell.recording.get_averaged_result()

        # Calculate amplitude and phase from complex IQ signal
        # Sequencer only causes RecModule to add up all measurement results
        # So to get real results we need to divide amplitude by the number of repetitions
        sig_amp = np.abs(read_i + 1j * read_q) / (1.0 * self.cell.sequencer.averages)
        sig_pha = np.angle(read_i + 1j * read_q)

        return [(sig_amp, sig_pha)]

    ################################################
    # Internal QKIT progress bar handling
    ################################################

    def _create_progress(self, count: int, name: str = "Progress"):
        if QKIT_ENABLED and self.show_progress_bar:
            if name not in self._progress_bar:
                self._progress_bar[name] = Progress_Bar(count, name=name)
            else:
                self._progress_bar[name].reset(count)

    def _set_progress(self, progress: int, name: str = "Progress"):
        if QKIT_ENABLED and self.show_progress_bar:
            pb = self._progress_bar[name]
            # Only update when value changes for better timing estimation
            if pb.progr != progress:
                pb.set(progress)

    def _iterate_progress(self, name: str = "Progress"):
        if QKIT_ENABLED and self.show_progress_bar:
            self._progress_bar[name].iterate()

    def _finish_progress(self, name: str = "Progress"):
        self._set_progress(self._progress_bar[name].max_it, name)


class ExperimentReadout:
    """Readout object to be passed to the Qkit Timedomain measurement class.

    The readout object can be passed when initializing the Qkit measurement. It
    provides neatless integration of `qiclib`'s experiment structure with
    Qkit's data measurement mechanisms.

    .. note::
        This class is not intended to be used stand-alone but only in combination
        and generated by an experiment class derived from `BaseExperiment`.

    Example
    -------
    .. code-block:: python

        from qkit.measure.timedomain.measure_td import Measure_td

        # ...
        exp = BaseExperiment(qic)
        mtd = Measure_td(qic.sample, exp.readout)
        # ...

    """

    def __init__(
        self,
        experiment: BaseExperiment,
        tones: int | list[float] | None = None,
    ):
        self.experiment = experiment

        from qiclib.experiment.qicode.base import QiCodeExperiment

        if not isinstance(experiment, QiCodeExperiment):
            warnings.warn(
                "Using legacy experiment readout setup. "
                "Please use the QiCode syntax, i.e. use a QiJob to create your experiment"
            )
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=FutureWarning)
                self._legacy_init(tones)
        else:
            if not tones:
                # Default set it to this frequency
                self._tones = []
                for cell in experiment.cell_list:
                    if cell.get_number_of_recordings() > 0:
                        self._tones.append(cell.initial_readout_frequency)
                if not self._tones:
                    for _, _, qic_cell in experiment.cell_iterator():
                        self._tones.append(qic_cell.recording.internal_frequency)
            else:
                self._tones = tones

            # Enable local oscillators
            try:
                for cell in self.experiment.qic.cell:
                    cell.readout.local_oscillator.on()
                    cell.manipulation.local_oscillator.on()
            except AttributeError:
                pass

        # Set up the QiController for the experiment
        self.experiment.configure()

    def _legacy_init(self, tones):
        """
        Legacy way of initializing the `ExperimentReadout` class
        FIXME: remove on the next major version

        The legacy method calls `QiController.readout` directly without utilizing the cell object,
        i.e. using `qic.readout` instead of `qic.cell[0].readout`.
        """
        if not tones:
            # Default set it to this frequency
            tones = [self.experiment.qic.readout.frequency]
        elif isinstance(tones, int) and tones > 0:
            # If it is no list, then it gives the number of tones
            tones = [self.experiment.qic.readout.frequency] * tones
        self._tones = tones

        # Enable local oscillators
        try:
            self.experiment.qic.readout.local_oscillator.on()
            self.experiment.qic.manipulation.local_oscillator.on()
        except AttributeError:
            pass

    def cleanup(self):
        # Turn off the local oscillators again
        try:
            for cell in self.experiment.qic.cell:
                cell.readout.local_oscillator.off()
                cell.manipulation.local_oscillator.off()
        except AttributeError:
            pass

    def get_tone_freq(self):
        """Returns the frequency at which we probe the resonators."""
        # We only have one frequency<
        return self._tones

    def readout(self, timeTrace=False, **kwargs):
        """Performs a readout and returns a tuple of amplitude and phase arrays."""
        if timeTrace:
            raise Warning("timeTrace for QiController is currently not supported.")
        # Obtain Data as List of (I, Q) values/lists
        data = self.experiment.record()

        # Format for Qkit and return
        return self._data_to_qkit_format(data)

    def _data_to_qkit_format(self, data):
        # data: []
        # Aggregate amplitudes and phases of one or more tones
        # Convert it into Qkit format
        amp = np.atleast_2d([np.atleast_1d(val[0]) for val in data]).T
        pha = np.atleast_2d([np.atleast_1d(val[1]) for val in data]).T
        return amp, pha

    def _json(self):
        """
        This function is called within Qkit.
        """
        return {"dtype": "qkitInstrument", "content": "Readout adapter"}


class TaskrunnerReadout(ExperimentReadout):
    """Readout object for continuous data streaming which has to be passed to
    the Qkit Timedomain measurement class.

    This object uses the taskrunner databox functionality to provide
    continuous result streaming during experiment execution. All nicely
    integrated with Qkit featuring data storage and live data viewing using
    the qviewkit data viewer.

    Apart from that, its usage is equivalent to `ExperimentReadout`. See there
    for more information.

    .. note::
        An instance of this class will be returned via the `BaseExperiment.readout`
        attribute by supported experiments. It is not intended for stand-alone usage.
    """

    def __init__(
        self, experiment, count, name, data_mode=TaskRunner.DataMode.INT32, tones=None
    ):
        super().__init__(experiment, tones)
        self._experiment_started = False
        self._count = count
        self._name = name
        self._data_mode = data_mode

        if not self.experiment._databox_streaming or not self.experiment.use_taskrunner:
            raise ValueError(
                "TaskrunnerReadout only works with compatible experiments!"
            )

    def start(self):
        self.experiment.qic.clear_errors()
        self.experiment.qic.readout.nco_enable(True)
        self.experiment.qic.manipulation.nco_enable(True)
        self.experiment._record_databox_start(self._count, self._name)
        self._experiment_started = True

    def cleanup(self):
        self.experiment._record_databox_finish(self._name)
        self.experiment.qic.readout.nco_enable(False)
        self.experiment.qic.manipulation.nco_enable(False)
        super().cleanup()
        # Check if some errors have been missed but do not raise an exception
        self.experiment.qic.check_errors(raise_exceptions=False)

    def readout(self, timeTrace=False, **kwargs):
        """Performs a readout and returns a tuple of amplitude and phase arrays."""
        if timeTrace:
            raise Warning("timeTrace for QiController is currently not supported.")

        if not self._experiment_started:
            raise Warning(
                "TaskrunnerReadout relies on newest Qkit Measure_td class. "
                "start() needs to be called prior to readout()."
            )

        data = self.experiment._record_databox_fetch(self._data_mode, self._name)
        # Convert it into Qkit format and return
        return self._data_to_qkit_format(data)
