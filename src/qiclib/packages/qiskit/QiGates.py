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

import numpy as np

import qiclib as ql
from qiclib.code import *  # pylint: disable=unused-wildcard-import,wildcard-import


@QiGate
def X_gate(cell: QiCell):
    """The Pauli X gate acts on a single qubit by rotating its state around the x axis of the Bloch Sphere by π radians.

    :param cell:
        The qubit acted on specified with its index

    :return:
        Apply X gate on a single qubit

    """
    X_pulse = QiPulse(
        length=cell["pi"],
        shape=ShapeLib.gauss,
        phase=0.0,
        frequency=cell["manip_frequency"],
    )

    Play(cell, X_pulse)


@QiGate
def Y_gate(cell: QiCell):
    """The Pauli Y gate acts on a single qubit by rotating its state around the y axis of the Bloch Sphere by π radians.

    :param cell: QiCell
        The qubit acted on specified with its index

    :return:
        Apply Y gate on a single qubit

    """
    Y_pulse = QiPulse(
        length=cell["pi"],
        shape=ShapeLib.gauss,
        phase=np.pi / 2,
        frequency=cell["manip_frequency"],
    )

    Play(cell, Y_pulse)


@QiGate
def Z_gate(cell: QiCell):
    """The Pauli Z gate acts on a single qubit by rotating its state around the z axis of the Bloch Sphere by π radians.

    :param cell:
        The qubit acted on specified with its index

    :return:
        Apply Z gate on a single qubit

    """
    RotateFrame(cell, np.pi)


@QiGate
def Rx_gate(cell: QiCell, angle: float):
    """The Rx gate acts on a single qubit by rotating its state around the x axis of the Bloch Sphere by the angle θ radians.

    :param cell:
        The qubit acted on specified with its index
    :param angle:
        The angle of rotation in radians

    :raises ValueError:
        Angle must be between 0 and π

    :return:
        Apply Rx gate with angle θ on a single qubit

    """
    Rx_pulse = QiPulse(
        length=cell["pi"],
        shape=ShapeLib.gauss,
        phase=0.0,
        frequency=cell["manip_frequency"],
        amplitude=angle / np.pi,
    )

    Play(cell, Rx_pulse)


@QiGate
def Ry_gate(cell: QiCell, angle: float):
    """The Ry gate acts on a single qubit by rotating its state around the y axis of the Bloch Sphere by the angle θ radians.

    :param cell:
        The qubit acted on specified with its index
    :param angle:
        The angle of rotation in radians

    :raises ValueError:
        Angle must be between 0 and π

    :return:
        Apply Ry gate with angle θ on a single qubit
    """
    Ry_pulse = QiPulse(
        length=cell["pi"],
        shape=ShapeLib.gauss,
        phase=np.pi / 2,
        frequency=cell["manip_frequency"],
        amplitude=angle / np.pi,
    )

    Play(cell, Ry_pulse)


@QiGate
def Rz_gate(cell: QiCell, angle: float):
    """The Rz gate acts on a single qubit by rotating its state around the z axis of the Bloch Sphere by the angle θ radians.

    :param cell:
        The qubit acted on specified with its index
    :param angle:
        The angle of rotation in radians

    :raises ValueError:
        Angle must be between 0 and π

    :return:
        Apply Rz gate with angle θ on a single qubit
    """
    RotateFrame(cell, angle)


@QiGate
def U1_gate(cell: QiCell, angle: float):
    """The U1 gate acts on a single qubit by rotating its state around the z axis of the Bloch Sphere by the angle θ radians.

    :param cell:
         The qubit acted on specified with its index
    :param angle:
         The polar angle of rotation θ in radians

    :return:
        Apply U1(θ) gate with angle θ on a single qubit
    """
    RotateFrame(cell, angle)


@QiGate
def U2_gate(cell: QiCell, angle_theta: float, angle_phi: float):
    """The U2 gate acts on a single qubit by rotating its state around the X+Z-axis of the Bloch Sphere.
    U2 gate decomposition into a series of Rx, Ry and Rz rotations: U2(θ,ϕ) = RZ(θ).RY(π/2).RZ(ϕ)

    :param cell:
        The qubit acted on specified with its index
    :param angle_theta:
        The polar angle of rotation θ in radians
    :param angle_phi:
        The azimuthal angle of rotation φ in radians

    :return:
        Apply U2(θ,ϕ) gate on a single qubit
    """
    Rz_gate(cell, angle_theta)
    Ry_gate(cell, np.pi / 2)
    Rz_gate(cell, angle_phi)


@QiGate
def U3_gate(cell: QiCell, angle_theta: float, angle_phi: float, angle_psi: float):
    """The U3 gate acts on a single qubit by rotating its state with 3 Euler angles in the Bloch Sphere.
    U3 gate decomposition into a series of Rx, Ry and Rz rotations: U3(θ,ϕ,ψ) = RZ(ϕ).RX(π/2).RZ(θ).RX(π/2).RZ(ψ)

    :param cell: QiCell
        The qubit acted on specified with its index
    :param angle_theta:
        The radial angle of rotation θ in radians
    :param angle_phi:
        The polar angle of rotation θ in radians
    :param angle_psi:
        The azimuthal angle of rotation φ in radians

    :return:
        Apply U3(θ,ϕ,ψ) gate on a single qubit
    """
    Rz_gate(cell, angle_phi)
    Rx_gate(cell, np.pi / 2)
    Rz_gate(cell, angle_theta)
    Rx_gate(cell, np.pi / 2)
    Rz_gate(cell, angle_psi)


@QiGate
def H_gate(cell: QiCell):
    """The Hadamard gate acts on a single qubit by creating a superposition if given a basis state. It rotates the state the qubit state around the axis (X+Z).1/√2

    The Hadamard gate can be expressed as a 90º rotation around the Y-axis, followed by a 180º rotation around the X-axis: H = X Y^{1/2}

    :param cell:
        The qubit acted on specified with its index

    :return:
        Apply Hadamard gate on a single qubit
    """
    Ry_gate(cell, np.pi / 2)
    X_gate(cell)


@QiGate
def S_gate(cell: QiCell):
    """The S gate acts on a single qubit by rotating its state around the z axis of the Bloch Sphere by the angle π/2.

    :param cell:
        The qubit acted on specified with its index

    :return:
        Apply S gate on a single qubit
    """
    Rz_gate(cell, np.pi / 2)


@QiGate
def T_gate(cell):
    """The T gate acts on a single qubit by rotating its state around the z axis of the Bloch Sphere by the angle π/4.

    :param cell: QiCell
        The qubit acted on specified with its index

    :return:
        Apply T gate on a single qubit
    """

    Rz_gate(cell, np.pi / 4)


@QiGate
def iSWAP_gate(cell_c: QiCell, cell_t: QiCell, cell_i: QiCell):
    r"""The iSWAP gate swaps the two qubit states \|01⟩ and \|10⟩ amplitudes by i.

    :param cell_c:
        The control qubit specified with its index
    :param cell_t:
        The target qubit specified with its index
    :param cell_i:
        The intermediate cell used to drive the flux-modulation pulse between the control and the target qubits

    :return:
        Apply iSWAP gate on two qubits
    """
    Sync(cell_c, cell_t, cell_i)

    Play(
        cell_i,
        QiPulse(
            length=cell_i["gauss_on_pulse_length"],
            shape=ShapeLib.gauss_up,
            frequency=cell_i["pulse_frequency"] + 0.0,
            amplitude=1,
        ),
    )

    Play(
        cell_i,
        QiPulse(
            length=cell_i["rectangular_pulse_length"],
            shape=ShapeLib.rect,
            frequency=cell_i["pulse_frequency"] + 0.0,
            amplitude=1,
        ),
    )

    Play(
        cell_i,
        QiPulse(
            length=cell_i["gauss_off_pulse_length"],
            shape=ShapeLib.gauss_down,
            frequency=cell_i["pulse_frequency"] + 0.0,
            amplitude=1,
        ),
    )

    Sync(cell_c, cell_t, cell_i)


@QiGate
def CNOT_gate(cell_c: QiCell, cell_t: QiCell, cell_i: QiCell):
    r"""The controlled X gate, or CNOT gate, flips the target qubit if the control qubit is in the \|1⟩ state in the computational basis.
    It is equivalent to a classical XOR gate.

    :param cell_c:
        The control qubit specified with its index
    :param cell_t:
        The target qubit specified with its index
    :param cell_i:
        The intermediate cell used to drive the flux-modulation pulse between the control and the target qubits

    :return:
        Apply CNOT on two qubits
    """
    Rz_gate(cell_c, -np.pi / 2)
    Rx_gate(cell_t, np.pi / 2)
    Rz_gate(cell_t, np.pi / 2)
    iSWAP_gate(cell_c, cell_t, cell_i)
    Rx_gate(cell_c, np.pi / 2)
    iSWAP_gate(cell_c, cell_t, cell_i)
    Rz_gate(cell_t, np.pi / 2)


@QiGate
def Measure(cell: QiCell, state_to, save_to="result"):
    r"""Quantum measurement on a single qubit in the computational basis {\|0〉, \|1〉}

    :param cell:
        The qubit acted on specified with its index

    :return:
        Measure a single qubit
    """
    ql.jobs.Readout(cell, save_to, state_to)
