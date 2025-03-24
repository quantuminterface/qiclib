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
"""This file contains the rabi experiment description for the QiController."""

import sys
import warnings
from math import floor, log2

import numpy as np

import qiclib.packages.utility as util
from qiclib.experiment.readout import IQFtReadout, IQRawReadout

STEPS_COARSE = 100e-9
STEPS_MIDDLE = 24e-9
STEPS_FINE = 4e-9


class AutoconfReadout(IQFtReadout):
    """Experiment that automatically configures the readout offset.

    :param controller:
        The QiController driver
    :type controller: qiclib.hardware.controller.QiController
    :param pulse_length:
        The length of the readout pulse in seconds (the default is 500ns)
    :type pulse_length: float, optional
    :param recording_length:
        The length of the recording window (the default is 400ns)
    :type recording_length: float, optional
    :param offset_min:
        The minimum recording offset to test (the default is 0ns)
    :type offset_min: float, optional
    :param offset_max:
        The maximum recording offset to test (the default is 2000ns)
    :type offset_max: float, optional
    :param trace_avgs:
        How many averages should be performed for displaying the final time trace
        (the default is 200)
    :type trace_avgs: int, optional
    :param phase_avgs:
        How many averages should be performed to determine the phase
        (the default is 5000)
    :type phase_avgs: int, optional
    :param set_sample:
        If the experiment should save the optimized configuration into the sample object
        (the default is True)
    :type set_sample: bool, optional
    :param reset_phase:
        If the experiment should also reset the phase to be 0 without manipulation pulses
        (the default is False)
    :type reset_phase: bool, optional
    :param set_shifts:
        If the value_shift from the recording module should be adapted (the default is True)
    :type set_shifts: bool optional
    :param make_plots:
        If the experiment should output plots. Requires matplotlib (the default is True)
    :type make_plots: bool, optional
    :param repetition_delay:
        The delay to wait between each single measurement (relaxation time, T_rep)
        (the default is to use controller.sample.T_rep)
    :type repetition_delay: float, optional

    .. deprecated:: 0.2.0
        AutoconfReadout is deprecated. Please use the new QiCode syntax instead,
        i.e. utilize the new :meth:`qiclib.init.calibrate_readout`.
    """

    def __init__(
        self,
        controller,
        pulse_length=418e-9,
        recording_length=400e-9,
        offset_min=0,
        offset_max=1e-6,
        cell=0,
        trace_avgs=200,
        phase_avgs=5000,
        set_sample=True,
        reset_phase=False,
        optimize_shift=False,
        make_plots=True,
        repetition_delay=None,
    ):
        super().__init__(controller, cell)

        self.pulse_length = pulse_length
        self.offset_max = offset_max
        self.offset_min = offset_min
        self.recording_length = recording_length
        self.trace_avgs = trace_avgs
        self.phase_avgs = phase_avgs
        self.set_sample = set_sample
        self.reset_phase = reset_phase
        self.optimize_shift = optimize_shift
        self.plots = make_plots
        self.pulse_detection_treshold = 0.2
        self._repetition_time = repetition_delay

        self.use_taskrunner = True

        warnings.warn(
            "AutoconfReadout is deprecated. Please use the new QiCode syntax instead,"
            "i.e. utilize the new `qiclib.init.calibrate_readout()`.",
            FutureWarning,
        )
        if not self.qic.taskrunner_available:
            raise NotImplementedError("This experiment requires the Taskrunner to work")

    def configure(self):
        """Prepares everything for the execution of the experiment."""
        # This experiment also configures the readout pulse
        self.configure_readout_pulse(
            self.pulse_length, self.recording_length, no_warn=True
        )
        # After that we can perform the normal configuration
        super().configure()

    def _configure_taskrunner(self):
        # Load the task to taskrunner
        self.qic.taskrunner.load_task_source("optimize_rec_offset.c", "AutoconfReadout")

        # Set task parameters
        self.qic.taskrunner.set_param_list(
            [
                self.cell_index,
                util.conv_time_to_cycles(self.offset_min),
                util.conv_time_to_cycles(self.offset_max),
                self._pc_dict["default"],
            ]
        )

    def _single_execution(self, offset):
        self.cell.recording.trigger_offset = offset
        return {"sequencer_start": self._pc_dict["default"], "delay_registers": []}

    def _record_internal(self):
        """This method describes the experimental procedure on the measurement pc."""
        if self.plots:
            try:
                import matplotlib.pyplot as plt
            except ImportError:
                sys.stderr.write(
                    "The matplotlib package is needed in order to plot measurement results."
                )
                self.plots = False

        # Create Experiment for raw readout (same configuration as this one)
        raw_experiment = IQRawReadout(
            self.qic, self.trace_avgs, 0, self.recording_length, self.cell_index
        )

        if self.optimize_shift:
            self.cell.recording.value_shift_offset = 0

        # First determine the necessary reference delay (for interferometer mode)
        if self.cell.recording.interferometer_mode:
            # Helper function
            def find_pulse_start(pulse):
                pulse_abs = np.abs(pulse)
                pulse_max = np.max(pulse_abs)
                return np.min(
                    np.argwhere(pulse_abs > self.pulse_detection_treshold * pulse_max)
                )

            raw_experiment.length = 2e-6
            raw_experiment.offset = 0

            # Perform the recording and determine pulse start of signal and ref
            raw_sig, raw_ref = raw_experiment._record_internal()[0]
            sig_start = util.conv_samples_to_time(find_pulse_start(raw_sig))
            ref_start = util.conv_samples_to_time(find_pulse_start(raw_ref))

            # Calculate the necessary delay
            reference_delay = util.conv_time_to_sample_time(
                sig_start - ref_start + self.cell.recording.reference_delay
            )
            if reference_delay < 0:
                print(
                    f"Optimal reference delay was detected to be { reference_delay * 1e9:.0f} ns. "
                    + "Negative delays are not possible so 0 will be set. "
                    + "Please check that reference and signal are not swapped."
                )
                reference_delay = 0

            if self.plots:
                plt.plot(2 * np.arange(len(raw_sig)), raw_sig, label="Signal")
                plt.plot(2 * np.arange(len(raw_ref)), raw_ref, label="Reference")
                plt.xlabel("Recording time (ns)")
                plt.axvline(x=1e9 * sig_start, linestyle="dashed")
                plt.axvline(x=1e9 * ref_start, color="r", linestyle="dashed")
                plt.legend()
                plt.show()

            if self.set_sample:
                self.qic.sample.rec_ref_delay = reference_delay
            self.cell.recording.reference_delay = reference_delay
            print(
                f"Reference Delay set to {self.cell.recording.reference_delay * 1e9:.2f} ns"
            )

        # Electrical Delay Calibration
        offsets = np.arange(
            util.conv_time_to_cycle_time(self.offset_min, "round"),
            util.conv_time_to_cycle_time(self.offset_max, "round"),
            util.conv_cycles_to_time(1),
        )
        data = self._record_internal_taskrunner(len(offsets), "TriggerOffset")[0]
        data_complex = np.array(data[::2]) + 1j * np.array(data[1::2])
        amplitudes = np.abs(data_complex)
        idx = np.argmax(amplitudes)
        max_offset = offsets[idx]

        if self.plots:
            _, axis = plt.subplots()
            axis.plot(offsets * 1e9, amplitudes)
            axis.vlines(max_offset * 1e9, 0, amplitudes[idx], "red")
            plt.title("Electrical delay calibration")
            plt.xlabel("Recording window offset (ns)")
            plt.ylabel("Signal amplitude (arb. unit)")
            plt.show()

        # Update the Trigger Offset
        self.cell.recording.trigger_offset = max_offset
        print(f"Optimal offset set to {max_offset*1e9:.1f}ns")
        if self.set_sample:
            self.qic.sample.rec_offset = max_offset

        # Check mirror sideband (to see if maybe I/Q have been swapped at the mixer)
        amp1, _ = super()._record_internal()[0]
        self.qic.recording.internal_frequency = -1 * self.qic.sample.rec_if_frequency
        amp2, _ = super()._record_internal()[0]
        self.qic.recording.internal_frequency = self.qic.sample.rec_if_frequency
        amp_factor = np.round(20 * np.log10(amp1 / amp2), 2)
        print(f"Mirror sideband is {amp_factor} dB supressed at recording input")
        if amp_factor < 5:
            raise RuntimeError(
                f"Mirror sideband is {-1*amp_factor} dB stronger than the actual signal"
                " recording input. Are maybe I and Q components swapped at the mixer?"
            )

        # Update the Value Shift Offset
        if self.optimize_shift:
            # 15 + log2(0.9) is bit count of 90% of the maximum possible value (2^15)
            # log2(max(amplitudes)) is the number of bits the amplitude currently needs
            # by flooring the difference we end up with a value between 45% and 90% of
            # the maximum possible range
            shift_offset = floor(15 + log2(0.9) - log2(max(amplitudes)))
            # No overflow can happen with offset of 0, so we can leave it like this
            # if really that much of the signal input is used (not realistic in
            # experiments due to normal noise levels which will clip at the ADCs...)
            shift_offset = max(0, shift_offset)
            self.cell.recording.value_shift_offset = shift_offset
            print(f"Value Shift offset set to {shift_offset}")
            if self.set_sample:
                self.qic.sample.rec_shift_offset = shift_offset

        # Remember average count
        averages_original = self.cell.sequencer.averages
        # Reset phase
        if self.reset_phase:
            self.cell.sequencer.averages = self.phase_avgs
            _, pha_old = super()._record_internal()[0]
            if self.cell.recording.interferometer_mode:
                print(f"Phase is {pha_old} and cannot be reset in interferometer mode.")
                warnings.warn(
                    "Resetting the phase is not possible in interferometer mode."
                )
            else:
                pha_old_calib = self.cell.recording.phase_offset
                pha_calib = pha_old_calib - pha_old
                if self.set_sample:
                    self.qic.sample.rec_phase = pha_calib
                self.cell.recording.phase_offset = pha_calib + 2 * np.pi
                _, pha_new = super()._record_internal()[0]
                print(f"Phase was {pha_old} and is now calibrated to {pha_new}.")

        if self.plots:
            # Perform a time trace readout
            raw_experiment.length = self.recording_length
            raw_experiment.offset = max_offset
            raw_experiment._configure_taskrunner()
            raw_i, raw_q = raw_experiment._record_internal()[0]

            if self.cell.recording.interferometer_mode:
                label_i = "Signal"
                label_q = "Reference"
            else:
                label_i = "I"
                label_q = "Q"

            plt.plot(np.arange(len(raw_i)), raw_i, label=label_i)
            plt.plot(np.arange(len(raw_q)), raw_q, label=label_q)
            plt.title(f"Recording window preview at {max_offset*1e9:.1f}ns offset")
            plt.xlabel("Recording time (ns)")
            plt.ylabel("ADC signal level (arb. unit)")
            plt.legend()
            plt.show()

        # Set back the pre averaging count to the original value
        self.cell.sequencer.averages = averages_original

        return max_offset
