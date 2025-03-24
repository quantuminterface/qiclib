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
"""Bundle of different functions and classes used for QiController experiments"""

from __future__ import annotations

import math
import warnings

import numpy as np

import qiclib.packages.constants as const


def conv_cycles_to_time(clock_cycles):
    """Converts a given number of clock cycles to time in seconds."""
    return float(clock_cycles) / const.CONTROLLER_FREQUENCY_IN_HZ


def conv_time_to_cycles(time: float, mode="round"):
    """Converts a given time in seconds to the equivalent number of clock cycles.
    Depending on the mode either an upper limit (ceil) is given or the nearest clock cycle count (round).
    """
    # TODO check where ceil is needed...
    if mode == "ceil":
        return math.ceil(time * const.CONTROLLER_FREQUENCY_IN_HZ)
    else:  # round
        return round(time * const.CONTROLLER_FREQUENCY_IN_HZ)


def time_is_integer_clock_cycles(time):
    """Checks if a given time is exactly an integer number of clock cycles."""
    modulo = time % const.CONTROLLER_CYCLE_TIME
    diff = min(modulo, const.CONTROLLER_CYCLE_TIME - modulo)
    # Floating point number comparison... diff should be less than 1 ppm
    return diff / const.CONTROLLER_CYCLE_TIME < 1e-6


def conv_amplitude_to_int(amplitude):
    return int(amplitude * (2**15 - 1))


def conv_freq_to_nco_phase_inc(frequency):
    """Converts a given frequency to the phase increment of the NCO."""
    if frequency >= 500e6:
        raise ValueError(f"Frequency of {frequency:.2g} Hz is too high")
    if frequency < -500e6:
        raise ValueError(f"Frequency of {frequency:.2g} Hz is too low")
    return int(round(frequency * const.CONTROLLER_NCO_PHASE_INCREMENT_PER_HZ, 0))


def conv_nco_phase_inc_to_freq(phase_increment):
    """Converts a given NCO phase increment to a frequency in Hz."""
    return float(phase_increment) / const.CONTROLLER_NCO_PHASE_INCREMENT_PER_HZ


def conv_phase_to_nco_phase(phase):
    """Converts a given phase in radian to the equivalent phase counter value of the NCO."""
    return int(round(phase * const.CONTROLLER_NCO_PHASE_VALUE_PER_PHASE, 0))


def conv_nco_phase_to_phase(phase_counter):
    """Converts a given NCO phase counter value to a phase in radian."""
    return float(phase_counter) / const.CONTROLLER_NCO_PHASE_VALUE_PER_PHASE


def conv_time_to_samples(time, round_cycles=True):
    """Converts a given time to a number of samples."""
    if round_cycles:
        clock_cycles = conv_time_to_cycles(time)
        return clock_cycles * const.CONTROLLER_SAMPLES_PER_CYCLE
    else:
        return int(
            round(
                time
                * const.CONTROLLER_FREQUENCY_IN_HZ
                * const.CONTROLLER_SAMPLES_PER_CYCLE,
                0,
            )
        )


def conv_samples_to_time(samples):
    """Converts a given number of samples to a time."""
    return conv_cycles_to_time(float(samples) / const.CONTROLLER_SAMPLES_PER_CYCLE)


def conv_samples_to_cycles(samples):
    """Converts a given number of samples to a matching number of cycles."""
    return math.ceil(samples / (1.0 * const.CONTROLLER_SAMPLES_PER_CYCLE))


def conv_cycles_to_samples(cycles):
    """Converts a given number of cycles to a matching number of samples."""
    return int(cycles * const.CONTROLLER_SAMPLES_PER_CYCLE)


def conv_time_to_cycle_time(time, mode="ceil"):
    """Converts a given time to the next bigger time equivalent to a whole number of clock cycles."""
    return conv_cycles_to_time(conv_time_to_cycles(time, mode))


def conv_time_to_sample_time(time):
    """Converts a given time to the next rounded time equivalent to a whole number of samples."""
    return conv_samples_to_time(conv_time_to_samples(time, False))


def conv_amplitude_factor_to_register(factor):
    """Converts a given amplitude factor in [0, 1] to the representing register value."""
    return round(factor * const.CONTROLLER_AMPLITUDE_MAX_VALUE)


def conv_amplitude_register_to_factor(register):
    """Converts a given amplitude calibration register value to to the representing factor in [0, 1]."""
    return float(register) / const.CONTROLLER_AMPLITUDE_MAX_VALUE


def generate_pulseform(
    duration: float, align="start", drag_amplitude: float | None = None
):
    """Generates a square shaped pulse with a given *duration*.
    If *drag_amplitude* is given, a DRAG pulse is generated instead.

    Returns an array consisting of (number of clock cycles) * (samples per clock cycle) entries.
    If duration is not equal to a whole number of clock cycles, the alignment within these
    clock cycles can be specified using *align*.

    Args:
    :param duration: The duration of the square pulse in seconds.
    :param align: Alignment of the pulse within the array consisting of whole number of clock cycles.
    :type align: 'start' | 'center' | 'end'
    :param drag_amplitude: The amplitude of the DRAG pulse if given.

    :return: (float[]) containing the samples of the pulse envelope
    """
    length = conv_time_to_cycle_time(duration)
    duration = conv_time_to_sample_time(duration)
    alignments = {"start": duration, "center": (duration + length) / 2, "end": length}
    if align not in alignments:
        warnings.warn(
            f'Pulseform alignment "{align}" not recognized. Using default "start"'
        )
        align = "start"
    pulse_end = alignments[align]
    pulse_start = pulse_end - duration
    rect = np.vectorize(
        lambda t: 1
        * (
            (
                t > pulse_start
                or np.isclose(
                    t, pulse_start, atol=0.1 / const.CONTROLLER_SAMPLE_FREQUENCY_IN_HZ
                )
            )
            and t < pulse_end
        )
    )

    if drag_amplitude is None:
        shape = rect
    else:
        # TODO Evaluate if this is correct (adapted shape from Qkit)
        def gauss(t):
            return np.exp(
                -((t - pulse_start - duration / 2.0) ** 2)
                / (2.0 * (duration / 5.0) ** 2)
            )

        def diff(t):
            return (
                -(5.0 / duration / 2.0)
                * (t - pulse_start - duration / 2.0)
                * gauss(t)
                * drag_amplitude
            )

        shape = np.vectorize(lambda t: (gauss(t) + 1j * diff(t)) * rect.pyfunc(t))

    time = np.arange(0, length, 1.0 / const.CONTROLLER_SAMPLE_FREQUENCY_IN_HZ)
    if len(time) == 0:
        return np.zeros(0)
    return shape(time)


def calculate_stater_config(state0_I, state0_Q, state1_I, state1_Q):
    # We assume Cov = 1
    warnings.warn(
        "Use the new qiclib.state_estimation.LinearDiscriminator class",
        DeprecationWarning,
    )
    config_a_I = state1_I - state0_I
    config_a_Q = state1_Q - state0_Q
    config_b = (state0_I**2 + state0_Q**2 - state1_I**2 - state1_Q**2) / 2
    return config_a_I, config_a_Q, config_b


def calculate_stater_state(data_I, data_Q, config):
    warnings.warn(
        "Use the new qiclib.state_estimation.LinearDiscriminator class",
        DeprecationWarning,
    )
    return np.where(data_I * config[0] + data_Q * config[1] + config[2] >= 0, 1, 0)


def flatten(list):
    return [item for sublist in list for item in sublist]
