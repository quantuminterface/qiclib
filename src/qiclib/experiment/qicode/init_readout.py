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
"""Module providing methods to calibrate the readout with the QiController."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import numpy as np

import qiclib.packages.utility as util
from qiclib.code import *  # pylint: disable=unused-wildcard-import, wildcard-import
from qiclib.experiment.qicode.collection import Readout
from qiclib.hardware.unitcell import UnitCell

from .fit_utils import compute_custom_piecewise_linear_fit

if TYPE_CHECKING:
    from qiclib import QiController


def calibrate_readout(
    qic: QiController,
    sample: QiSample,
    averages: int,
    make_plots: bool = True,
    set_sample: bool = True,
    signal_strength: bool = True,
    reset_phase: bool = False,
    phase_avgs: int = 5000,
    trace_avgs: int = 1000,
    cell: int = 0,
):
    """Autoconfigures the readout pulse

    :param qic: The instance of the QiController
    :param sample: Sample object containing qubit and setup properties
    :param averages: The number of averages
    :param make_plots: If plots should be made
    :param set_sample: If the sample should be set automatically
    :param signal_strength: If the recorded signal should be optimized
    :param reset_phase: If a phase reset should be made (not possible in interferometer mode)
    :param phase_avgs: number of averages for phase measurement
    :param trace_avgs: number of averages for the plot, if plotting is set to `True`
    :param cell: The Index of the cell to use from the sample object

    :return: the offset with maximum electrical delay
    """

    qic_cell = sample[cell](qic)

    if qic_cell.recording.interferometer_mode:
        raise NotImplementedError("Interferometer mode is currently not supported")
        # _init_interferometer_readout(sample, averages, set_sample, make_plots, cell)

    # calibrate electrical delay
    max_offset = calibrate_electrical_delay(  # electrical delay call
        qic, sample, averages, make_plots, set_sample, cell
    )
    # check sideband
    check_sidebands(qic, sample, averages, cell)

    # Shift offset
    if signal_strength:
        optimize_signal_strength(qic, sample, averages, cell)

    # reset phase
    if reset_phase:
        calibrate_readout_phase(qic, sample, phase_avgs, set_sample, cell)

    # plot recording window
    if make_plots:
        import matplotlib.pyplot as plt

        raw_sig, raw_ref = record_timetrace(
            qic, sample, trace_avgs, offset=max_offset, cell=cell
        )
        label_i = "I"
        label_q = "Q"

        plt.plot(np.arange(len(raw_sig)), raw_sig, label=label_i)
        plt.plot(np.arange(len(raw_ref)), raw_ref, label=label_q)
        plt.title(f"Recording window preview at {max_offset*1e9:.1f}ns offset")
        plt.xlabel("Recording time (ns)")
        plt.ylabel("ADC signal level (arb. unit)")
        plt.legend()
        plt.show()


def calibrate_electrical_delay(
    qic: QiController,
    sample: QiSample,
    averages: int,
    make_plots: bool,
    set_sample: bool,
    cell: int = 0,
):
    """calibrates electrical delay

    :param qic: The QiController instance
    :param sample: Sample object containing qubit and setup properties
    :param averages: The number of averages used to run the measurement
    :param make_plots: Whether plots should be made
    :param set_sample: Whether the sample should be set automatically
    :param cell: The Index of the cell to use from the sample object, by default 0

    :return: the offset with maximum electrical delay
    """
    with QiJob() as calib_offset:
        q = QiCells(1)
        offset = QiVariable()
        with ForRange(offset, 0, 1024e-9, 4e-9):
            PlayReadout(
                q[0], QiPulse(q[0]["rec_pulse"], frequency=q[0]["rec_frequency"])
            )
            Recording(q[0], q[0]["rec_length"], offset, save_to="result")
            Wait(q[0], 2e-6)

    calib_offset.run(qic, sample, cell_map=[cell], averages=averages)
    data = calib_offset.cells[0].data("result")
    amplitude = np.abs(data[0] + 1j * data[1])
    offsets = 4e-9 * np.arange(len(amplitude))

    fit_params = compute_custom_piecewise_linear_fit(offsets, amplitude)
    if fit_params is not None:
        t1, t2, A1, A2 = fit_params
        max_offset = t1
    else:
        max_offset = None

    # plot electrical delay
    if make_plots:
        import matplotlib.pyplot as plt

        plt.plot(4 * np.arange(len(amplitude)), amplitude)
        plt.vlines(max_offset * 1e9, 0, np.max(amplitude), "red")
        plt.title("Electrical delay calibration")
        plt.xlabel("Recording window offset (ns)")
        plt.ylabel("Signal amplitude (arb. unit)")
        plt.show()

    if 0.7 * np.max(amplitude) < np.min(amplitude) or np.max(amplitude) < 10:
        raise ValueError(
            "No clear signal could be detected. Are you sure that everything is"
            " connected right?"
        )

    print(f"Optimal offset: {max_offset*1e9:.1f} ns")
    if set_sample:
        sample[cell]["rec_offset"] = max_offset

    return max_offset


def check_sidebands(qic: QiController, sample: QiSample, averages: int, cell: int = 0):
    """After an I/Q mixer, the signal should ideally be in only one sideband. However,
    in some cases, the cabling is swapped or the input signal has bad quality. This
    check looks at both sidebands and calculates the signal suppression in decibel.
    If it is below a 5dB threshold, a warning is issued for the user.

    :param qic: The QiController instance
    :param sample: Sample object containing qubit and setup properties
    :param averages: The number of averages to perform in order to determine the sideband suppression
    :param cell: The index of the cell that should be used from the sample object, by default 0

    :return: the sideband suppression in decibel
    """
    qic_cell = sample[cell](qic)
    with QiJob() as job:
        q = QiCells(1)
        Readout(q[0], save_to="result")
        Wait(q[0], 2e-6)
    exp = job.create_experiment(
        qic, sample, averages, cell_map=[cell], data_collection="amp_pha"
    )
    exp.configure()
    exp.record()
    [amp_1], _ = np.abs(job.cells[0].data("result"))
    qic_cell.recording.internal_frequency *= -1
    exp.record()
    [amp_2], _ = np.abs(job.cells[0].data("result"))
    qic_cell.recording.internal_frequency *= -1
    amp_factor = np.round(20 * np.log10(amp_1 / amp_2), 2)
    print(f"Mirror sideband is {amp_factor:.1f} dB suppressed at recording input")
    if amp_factor < 5:
        sys.stderr.write(
            f"Mirror sideband is {-1*amp_factor} dB stronger than the actual signal at"
            " the recording input. Are maybe I and Q components swapped at the mixer?"
        )
    return amp_factor


def calibrate_readout_phase(
    qic: QiController,
    sample: QiSample,
    averages: int,
    set_sample: bool = False,
    cell: int = 0,
):
    """The readout phase is normally at some arbitrary phase depending on the electrical
    delay. To simplify measurements and have the phase values always at a similar range,
    the phase can be calibrated and reset to zero by applying a rotation onto the data.

    The determined phase offset value will be stored inside the recording module of the
    relevant cell. By default, it will not be overwritten by QiJobs later on.

    :param qic: The QiController instance
    :param sample: Sample object containing qubit and setup properties
    :param averages: The number of averages to perform in order to determine the signal's phase
    :param set_sample: If the sample should be updated with the new value, by default False
    :param cell: The index of the cell that should be used from sample object, by default 0

    :return: the calibrated phase offset value (rotation angle of the data)
    """
    qic_cell = sample[cell](qic)

    if qic_cell.recording.interferometer_mode:
        raise SystemError("Resetting the phase is not possible in interferometer mode.")

    with QiJob() as job:
        q = QiCells(1)
        Readout(q[0], save_to="result")
        Wait(q[0], 2e-6)
    job.run(qic, sample, averages, cell_map=[cell], data_collection="amp_pha")
    _, [pha_old] = job.cells[0].data("result")

    pha_old_calib = qic_cell.recording.phase_offset
    pha_calib = pha_old_calib - pha_old
    qic_cell.recording.phase_offset = pha_calib + 2 * np.pi
    if set_sample:
        sample[cell]["rec_phase"] = pha_calib

    job.run(qic, sample, averages, cell_map=[cell], data_collection="amp_pha")
    _, [pha_new] = job.cells[0].data("result")
    print(f"Phase was {pha_old:.5f} and is now calibrated to {pha_new:.5f}.")
    return pha_calib


def optimize_signal_strength(
    qic: QiController,
    sample: QiSample,
    averages: int,
    cell: int = 0,
    buffer: float = 0.1,
) -> int:
    """Signals are processed with 16bit precision by the platform. When integrating the
    incoming signals after down-conversion, the integration can exceed these value
    range. Therefore, the values are shifted to always stay within a valid range.
    For small ADC input signals, this can result in low signal strengths.
    To correct this, the value shift can be reduced. This method calculates the optimal
    value shift offset and sets it in the recording module.

    The determined value shift offset value will be stored inside the recording module
    of the relevant cell. By default, it will not be overwritten by QiJobs later on.

    :param qic: The QiController instance
    :param sample: Sample object containing qubit and setup properties
    :param averages: The number of averages to perform in order to determine the optimal value shift
    :param cell: The index of the cell that should be used from sample
    :param buffer: Safety buffer. For example, 0.1 means to use 10% more than measured

    :return: The optimized value shift offset
    """
    qic_cell: UnitCell = sample[cell](qic)
    # Reset to highest possible value
    qic_cell.recording.expected_highest_signal_amplitude = 2**15 - 1
    with QiJob() as job:
        q = QiCells(1)
        Readout(q[0], save_to="result")
        Wait(q[0], 2e-6)
    job.run(qic, sample, cell_map=[cell], averages=averages, data_collection="iqcloud")
    ii, qq = np.abs(job.cells[0].data("result"))
    # TODO: These calculations should be move to the ServiceHub
    # TODO: Currently, the ServiceHub just outputs some arbitrary values that are dependent on
    # TODO: the value_factor and the recording length. This makes it hard to compare
    # TODO: values obtained from recordings with different lengths.
    max_amplitude = (max(np.max(ii), np.max(qq)) * qic_cell.recording.value_factor) / (
        sample[cell]["rec_length"] / 4e-9
    )
    max_amplitude = int(max_amplitude * (1 + buffer))
    qic_cell.recording.expected_highest_signal_amplitude = max_amplitude
    print(f"Expected highest signal amplitude in ADC units: {max_amplitude}")
    return max_amplitude


def record_timetrace(
    qic: QiController,
    sample: QiSample,
    averages: int,
    duration: float | None = None,
    offset: float | None = None,
    pulse_length: float | None = None,
    cell: int = 0,
) -> list[list[float]]:
    """performs are readout and gathers the raw data. If the optional parameters are not given
    they will be taken from the sample.

    :param qic:
        The QiController itself
    :param sample:
        Sample object containing qubit and setup properties
    :param averages:
        The number of averages
    :param duration:
        The duration of the recording, by default None
    :param offset:
        The offset of the recording, by default None
    :param pulse_length:
        The length of the recording pulse, by default None
    :param cell:
        The Index of the cell to use from sample object, by default the first one

    :return: The Raw I and Q data in two sublists
    """
    with QiJob() as job:
        q = QiCells(1)
        length = pulse_length or q[0]["rec_pulse"]
        rec_duration = duration or q[0]["rec_length"]
        if offset is None:
            rec_offset = q[0]["rec_offset"]
        else:
            rec_offset = offset
        PlayReadout(q[0], QiPulse(length=length, frequency=q[0]["rec_frequency"]))
        Recording(q[0], duration=rec_duration, offset=rec_offset, save_to="result")
        Wait(
            q[0], 2e-6
        )  # Wait a bit before repeating -> resonator excitation can decay (ringdown)

    job.run(qic, sample, cell_map=[cell], averages=averages, data_collection="raw")
    return job.cells[0].data("result")


def crop_recording_window(
    qic: QiController, sample: QiSample, averages: int = 1, cell: int = 0
):
    """widget for cropping the recording window by hand.

    :param qic: The QiController itself
    :param sample: Sample object containing qubit and setup properties
    :param averages: The number of averages.
    :param cell: The Index of the cell to use from sample object, by default the first one
    """
    offset = 0
    duration = 1024e-09
    sig, ref = record_timetrace(
        qic,
        sample=sample,
        averages=averages,
        duration=duration,
        offset=offset,
        cell=cell,
    )

    import ipywidgets as widgets
    import matplotlib.pyplot as plt

    def pltfunc(start: float, end: float, done: bool):
        """Plots the Raw timetrace of the readout and sets the values
        of the widgets in the sample if the done tickbox ist ticked.

        :param start: first value on the x-axis
        :param end: last value on the x-axis
        :param done: tickbox if setting the window with the widgets is done.
        """
        if done:
            offset = start
            duration = end - start
            _sw.disabled = True
            _ew.disabled = True
            _dw.disabled = True
            _dw.description = (
                f"offset = {offset} ns, " + f"recording length = {duration} ns"
            )
            sample[cell]["rec_offset"] = offset * 1e-09
            sample[cell]["rec_length"] = duration * 1e-09
            # return cell
        else:
            plt.figure(figsize=(15, 5))
            plt.plot(range(len(sig)), sig)
            plt.plot(range(len(ref)), ref)
            plt.axvspan(0, start, color="k", alpha=0.2)
            plt.axvspan(end, len(sig), color="k", alpha=0.2)
            plt.xlim(0, len(sig))
            plt.show()

    style = {"description_width": "initial"}
    _sw = widgets.IntSlider(
        min=0,
        max=len(sig),
        step=4,
        value=0,
        continuous_update=True,
        description="offset in ns",
        style=style,
    )
    _ew = widgets.IntSlider(
        min=0,
        max=len(sig),
        step=4,
        value=0,
        continuous_update=True,
        description="end of recording in ns",
        style=style,
    )
    _dw = widgets.Checkbox(value=False, description="Done!", indent=True, style=style)
    _wgt = widgets.interact(pltfunc, start=_sw, end=_ew, done=_dw)


def _init_interferometer_readout(
    qic: QiController,
    sample: QiSample,
    averages: int,
    set_sample: bool,
    make_plots: bool,
    cell: int = 0,
):
    """autoconfigure the readout pulse in the interferometer mode

    :param qic: The QiController
    :param sample: Sample object containing qubit and setup properties
    :param averages: he number of averages
    :param set_sample: whether the sample should be set
    :param make_plots: whether plots should be made
    :param cell: The Index of the cell to use from sample object, by default the first one
    """

    # Helper function
    def find_pulse_start(pulse):
        pulse_detection_treshold = 0.5
        pulse_abs = np.abs(pulse)
        pulse_max = np.max(pulse_abs)
        return np.min(np.argwhere(pulse_abs > pulse_detection_treshold * pulse_max))

    length = sample[cell]["rec_pulse"]
    rec_duration = sample[cell]["rec_length"]
    rec_offset = sample[cell]["rec_offset"]
    qic_cell = sample[cell](qic)

    with QiJob() as job:
        q = QiCells(1)
        PlayReadout(q[0], QiPulse(length=length, frequency=q[0]["rec_frequency"]))
        Recording(q[0], duration=rec_duration, offset=rec_offset, save_to="result")
        Wait(
            q[0], 2e-6
        )  # Wait a bit before repeating -> resonator excitation can decay (ringdown)

    job.run(qic, sample, averages=averages, cell_map=[cell], data_collection="raw")
    # Perform the recording and determine pulse start of signal and ref
    raw_sig, raw_ref = job.cells[0].data("result")
    sig_start = util.conv_samples_to_time(find_pulse_start(raw_sig))
    ref_start = util.conv_samples_to_time(find_pulse_start(raw_ref))

    # Calculate the necessary delay
    reference_delay = util.conv_time_to_sample_time(
        sig_start - ref_start + qic_cell.recording.reference_delay
    )
    if reference_delay < 0:
        print(
            f"Optimal reference delay was detected to be {reference_delay * 1e9:.0f} ns. "
            + "Negative delays are not possible so 0 will be set. "
            + "Please check that reference and signal are not swapped."
        )
        reference_delay = 0
    # plot the raw IQ- signal
    if make_plots:
        import matplotlib.pyplot as plt

        plt.plot(2 * np.arange(len(raw_sig)), raw_sig, label="Signal")
        plt.plot(2 * np.arange(len(raw_ref)), raw_ref, label="Reference")
        plt.xlabel("Recording time (ns)")
        plt.axvline(x=1e9 * sig_start, linestyle="dashed")
        plt.axvline(x=1e9 * ref_start, color="r", linestyle="dashed")
        plt.legend()
        plt.show()

    if set_sample:
        sample[cell]["rec_ref_delay"] = reference_delay
    qic_cell.recording.reference_delay = reference_delay
    print(f"Reference Delay set to {qic_cell.recording.reference_delay * 1e9:.2f} ns")
