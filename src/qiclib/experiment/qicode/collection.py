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
"""Collection of common experiments written in the QiCode language."""

import numpy as np

# pylint: disable=unused-wildcard-import, wildcard-import
from qiclib.code import *

###
### Some useful gate descriptions
###


@QiGate
def Readout(cell: QiCell, save_to=None, state_to=None):
    """Outputs a readout pulse and triggers the recording module to process the result."""
    PlayReadout(
        cell, QiPulse(length=cell["rec_pulse"], frequency=cell["rec_frequency"])
    )
    Recording(cell, cell["rec_length"], cell["rec_offset"], save_to, state_to)


@QiGate
def PiPulse(cell: QiCell, phase: float = 0.0, detuning: float = 0.0):
    """Outputs a manipulation pulse to rotate the qubit around the Bloch sphere by pi."""
    pi_pulse = QiPulse(
        length=cell["pi"], phase=phase, frequency=cell["manip_frequency"] + detuning
    )
    Play(cell, pi_pulse)


@QiGate
def PiHalfPulse(cell: QiCell, phase: float = 0.0, detuning: float = 0.0):
    """Outputs a manipulation pulse to rotate the qubit around the Bloch sphere by pi/2."""
    pi_pulse = QiPulse(
        length=cell["pi"] / 2, phase=phase, frequency=cell["manip_frequency"] + detuning
    )
    Play(cell, pi_pulse)


@QiGate
def Thermalize(cell):
    """Wait 5x the T1 time of the qubit so it can return to the ground state."""
    Wait(cell, 5 * cell["T1"])


###
### Commonly used experiments and their QiCode representation
###


def SimpleReadout() -> QiJob:
    """Performing a single IQ Readout without any extras.

    Sequence: `[Readout]`

    :return: The created SimpleReadout experiment description as QiJob object.
        It can be started by using the :python:`job.run(controller, sample)` method.
    """
    with QiJob() as job:
        q = QiCells(1)
        Readout(q[0], save_to="result")
        Thermalize(q[0])
    return job


def Rabi(start: float, stop: float, step: float):
    """Sweeping the length of a manipulation pulse, then check the resulting qubit state.

    Sequence: `(Var. length pulse) - [Readout]`

    :param start: The start duration of the manipulation pulse in seconds
    :param stop: The end duration of the manipulation pulse (not included)
    :param step: The step size in which the manipulation pulse length is changed

    :return: The created Rabi experiment description as QiJob object.
        It can be started by using the :python:`job.run(controller, sample)` method.
    """
    with QiJob() as job:
        q = QiCells(1)
        length = QiTimeVariable()
        with ForRange(length, start, stop, step):
            Play(q[0], QiPulse(length, frequency=q[0]["manip_frequency"]))
            Readout(q[0], save_to="result")
            Thermalize(q[0])
    return job


def T1(start: float, stop: float, step: float):
    """Exciting the qubit with a pi pulse, then waiting a variable time before reading
    out the qubit state. This is to investigate the decay behavior of the excited state.

    Sequence: `(Pi) - Delay - [Readout]`

    :param start: The start delay between pi pulse and readout in seconds
    :param stop: The end delay between pi pulse and readout (not included)
    :param step: The step size in which the delay length is changed

    :return: The created T1 experiment description as QiJob object.
        It can be started by using the :python:`job.run(controller, sample)` method.
    """
    with QiJob() as job:
        q = QiCells(1)
        length = QiTimeVariable()
        with ForRange(length, start, stop, step):
            PiPulse(q[0])
            Wait(q[0], length)
            Readout(q[0], save_to="result")
            Thermalize(q[0])
    return job


def Ramsey(start: float, stop: float, step: float, detuning: float = 0.0):
    """Performing a pi/2 pulse, followed by a delay and a second pi/2 pulse.
    Afterwards, the qubit state is determined.

    Sequence: `(Pi/2) - Delay - (Pi/2) - [Readout]`

    :param start: The start delay between the two pi/2 pulses in seconds
    :param stop: The end delay between the two pi/2 pulses (not included)
    :param step: The step size in which the delay length is changed

    :return: The created Ramsey experiment description as QiJob object.
        It can be started by using the :python:`job.run(controller, sample)` method.
    """
    with QiJob() as job:
        q = QiCells(1)
        length = QiTimeVariable()
        with ForRange(length, start, stop, step):
            PiHalfPulse(q[0], detuning=detuning)
            Wait(q[0], length)
            PiHalfPulse(q[0], detuning=detuning)
            Readout(q[0], save_to="result")
            Thermalize(q[0])
    return job


def SpinEcho(start: float, stop: float, step: float):
    """Performing a pi/2 pulse, followed by a delay, a pi pulse, the same delay and a
    second pi/2 pulse. Afterwards, the qubit state is determined.

    Sequence: `(Pi/2) - Delay/2 - (Pi) - Delay/2 - (Pi/2) - [Readout]`

    Note
    ----
    The delay in this sequence resembles the full delay consisting of the two waiting
    times between the three pulses.
    Be aware, that for accurate results, start and step should be multiples of 2 clock
    cycles (8ns). Otherwise, rounding errors may occur.

    :param start: The start delay during the sequence in seconds
    :param stop: The end delay during the sequence (not included)
    :param step: The step size in which the delay length is changed

    :return: The created SpinEcho experiment description as QiJob object.
        It can be started by using the :python:`job.run(controller, sample)` method.
    """
    with QiJob() as job:
        q = QiCells(1)
        length = QiTimeVariable()
        length_half = QiTimeVariable()
        with ForRange(length, start, stop, step):
            Assign(length_half, length >> 1)  # divide by two (possible rounding error!)
            PiHalfPulse(q[0])
            Wait(q[0], length_half)
            PiPulse(q[0])
            Wait(q[0], length_half)
            PiHalfPulse(q[0])
            Readout(q[0], save_to="result")
            Thermalize(q[0])
    return job


def MultiPi(max: int, step: int = 2, min: int = 0):
    """Performing multiple pi pulses in a row and checking the resulting state.

    Sequence: ``(Pi) - (Pi) - ... - (Pi) - [Readout]``

    .. note::
        The delay in this sequence resembles the full delay consisting of the two waiting
        times between the three pulses.

    :param max: The maximum number of pi pulses to perform (included)
    :param step: The step sizie in which the number of pi pulses is increased
    :param min: The minimum number of pi pulses to perform

    :return: The created MultiPi experiment description as QiJob object.
        It can be started by using the :python:`job.run(controller, sample)` method.
    """
    with QiJob() as job:
        q = QiCells(1)
        count = QiVariable(int)
        i = QiVariable(int)
        with ForRange(count, min, max + 1, step):
            with ForRange(i, 0, count):
                PiPulse(q[0])
            Readout(q[0], save_to="result")
            Thermalize(q[0])
    return job


def ActiveReset(target_state=0):
    """Performing a Readout to determine the qubit state. Then perform a conditional pi
    pulse to reach the desired `target_state`. Afterwards check the obtained state.

    Sequence: `[Temporary Readout to detect State] - If necessary: (Pi) - [Readout]`

    :param target_state: In which state to prepare the qubit, by default 0
    :type target_state: 0|1

    :return: The created ActiveReset experiment description as QiJob object.
        It can be started by using the :python:`job.run(controller, sample)` method.
    """
    if target_state not in [0, 1]:
        raise ValueError("QiController can only distinguish between states 0 and 1.")
    with QiJob() as job:
        q = QiCells(1)
        state = QiStateVariable()
        Readout(q[0], state_to=state)
        with If(state != target_state):
            PiPulse(q[0])
        Readout(q[0], save_to="result")
    return job


def MultiQuantumJumps(shots=32000, qubits=1):
    if shots % 32 != 0:
        raise ValueError("shots needs to be a multiple of 32!")

    with QiJob() as job:
        cells = QiCells(qubits)
        for q in cells:
            PlayReadout(q, QiPulse("cw", frequency=q["rec_frequency"]))
            Wait(q, 100e-9)
            Recording(
                q, q["rec_length"], q["rec_offset"], "result", toggleContinuous=True
            )
            Wait(q, (shots - 1) * q["rec_length"])
            Recording(q, q["rec_length"], q["rec_offset"], toggleContinuous=True)
            Wait(q, 10e-6)  # Wait until last recording has finished
            PlayReadout(q, QiPulse("off"))

    # Add custom data handling for quantum jumps
    def data_converter(databoxes):
        results = []
        for db in databoxes:
            results.append(
                np.array(
                    [[(val >> i) & 0x1 for i in range(32)] for val in db]
                ).flatten()
            )
        return results

    # Do not overwrite the default parameter values which include cell mapping
    job.set_custom_data_processing(
        "quantum_jumps_multi.c", converter=data_converter, mode="uint32"
    )
    return job
