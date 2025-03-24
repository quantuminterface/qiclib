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

import datetime
from typing import TYPE_CHECKING

from qiskit import qobj as qobj_mod
from qiskit.circuit import Instruction, Qubit
from qiskit.circuit.quantumcircuit import QuantumCircuit
from qiskit.exceptions import QiskitError
from qiskit.providers import BackendV1 as Backend
from qiskit.providers import Options
from qiskit.providers.models import BackendConfiguration
from qiskit.providers.models.backendproperties import Gate, Nduv
from tzlocal import get_localzone

import qiclib
from qiclib.code import *  # pylint: disable=unused-wildcard-import,wildcard-import
from qiclib.packages.constants import CONTROLLER_CYCLE_TIME
from qiclib.packages.qiskit import QiGates
from qiclib.packages.qiskit.QiController_job import QiController_job

if TYPE_CHECKING:
    from qiclib.packages.qiskit.QiController_provider import QiController_provider

qicode_gates = [
    "X_gate",
    "Y_gate",
    "Z_gate",
    "H_gate",
    "Rx_gate",
    "Ry_gate",
    "Rz_gate",
    "U1_gate",
    "U2_gate",
    "U3_gate",
    "S_gate",
    "T_gate",
    "CNOT_gate",
    "iSWAP_gate",
]


qiskit_to_qicode = {
    "x": QiGates.X_gate,
    "y": QiGates.Y_gate,
    "z": QiGates.Z_gate,
    "h": QiGates.H_gate,
    "rx": QiGates.Rx_gate,
    "ry": QiGates.Ry_gate,
    "rz": QiGates.Rz_gate,
    "u1": QiGates.U1_gate,
    "u2": QiGates.U2_gate,
    "u3": QiGates.U3_gate,
    "s": QiGates.S_gate,
    "t": QiGates.T_gate,
    "cx": QiGates.CNOT_gate,
    "iswap": QiGates.iSWAP_gate,
    "measure": QiGates.Measure,
}


def reverse_string(x):
    return x[::-1]


class QiController_backend(Backend):
    """
    The QiController_backend class translates the Qiskit code to QiCode and runs the corresponding QiJob on the QiController backend

    :param backend:
        Name of the backend

    :param sample:
        The sample object storing the backend properties for experiment

    :ivar configuration:
        The configuration parameters of the backend

    """

    def __init__(
        self,
        provider: "QiController_provider",
    ):
        self.backend = provider.backend
        self.sample = provider.sample
        self.coupling_map = provider.coupling_map

        self._configuration = {
            "backend_name": self.backend.ip_address,
            "backend_version": qiclib.__version__,
            "n_qubits": len(self.sample.cells),
            "routing_map": self.sample.cell_map,
            "basis_gates": ["i", "u1", "u2", "u3", "cx"],
            "coupling_map": self.coupling_map,
            "simulator": True,
            "local": True,
            "open_pulse": False,
            "conditional": True,
            "memory": True,
            "max_shots": 100000,
            "supported_gates": qicode_gates,
            "gates": [{"name": "TODO", "parameters": [], "qasm_def": "TODO"}],
        }

        self._properties = {
            "backend_name": self.backend.ip_address,
            "backend_version": qiclib.__version__,
            "last_update_date": "2021-08-23T14:28:23.382748",
            "gates": [
                Gate(
                    qubits=[0],
                    gate="U1",
                    parameters=[
                        Nduv("2021-07-06T09:06:46Z", "gate_error", None, 0.000),
                        Nduv(
                            "2021-07-06T09:06:46Z",
                            "gate_length",
                            "ns",
                            CONTROLLER_CYCLE_TIME * 1e9,
                        ),
                    ],
                ),
                Gate(
                    qubits=[0],
                    gate="U2",
                    parameters=[
                        Nduv("2021-07-06T09:06:46Z", "gate_error", None, 0.000),
                        Nduv(
                            "2021-07-06T09:06:46Z",
                            "gate_length",
                            "ns",
                            (self.sample[0]["pi"] + 2 * CONTROLLER_CYCLE_TIME) * 1e9,
                        ),
                    ],
                ),
                Gate(
                    qubits=[0],
                    gate="U3",
                    parameters=[
                        Nduv("2021-07-06T09:06:46Z", "gate_error", None, 0.000),
                        Nduv(
                            "2021-07-06T09:06:46Z",
                            "gate_length",
                            "ns",
                            (2 * self.sample[0]["pi"] + 3 * CONTROLLER_CYCLE_TIME)
                            * 1e9,
                        ),
                    ],
                ),
                Gate(
                    qubits=[0, 1],
                    gate="Two_qubit_gate",
                    parameters=[
                        Nduv("2021-08-06T09:06:46Z", "gate_error", None, 0.000),
                        Nduv(
                            "2021-08-06T09:06:46Z",
                            "gate_length",
                            "ns",
                            327.1111111111111,  # To be updated when the 2-qubit gate will be set
                        ),
                    ],
                ),
            ],
            "qubits": [
                [
                    Nduv(
                        datetime.datetime(
                            2020, 12, 7, 9, 5, 37, tzinfo=get_localzone()
                        ),
                        "T1",
                        "ns",
                        self.sample[0]["T1"] * 1e-3,
                    )
                ],
                [
                    Nduv(
                        datetime.datetime(
                            2020, 12, 7, 9, 6, 19, tzinfo=get_localzone()
                        ),
                        "T2",
                        "ns",
                        self.sample[0]["T2"] * 1e-3,
                    )
                ],
                [
                    Nduv(
                        datetime.datetime(
                            2020, 12, 7, 9, 21, 20, tzinfo=get_localzone()
                        ),
                        "frequency",
                        "GHz",
                        self.sample[0]["manip_frequency"] * 1e-3,
                    )
                ],
                [
                    Nduv(
                        datetime.datetime(
                            2020, 12, 7, 9, 21, 20, tzinfo=get_localzone()
                        ),
                        "anharmonicity",
                        "GHz",
                        -0.31386048358781926,
                    )
                ],
                [
                    Nduv(
                        datetime.datetime(
                            2020, 12, 7, 9, 4, 47, tzinfo=get_localzone()
                        ),
                        "readout_error",
                        None,
                        0.000,
                    )
                ],
                [
                    Nduv(
                        datetime.datetime(
                            2020, 12, 7, 9, 4, 47, tzinfo=get_localzone()
                        ),
                        "prob_meas0_prep1",
                        None,
                        0.000,
                    )
                ],
                [
                    Nduv(
                        datetime.datetime(
                            2020, 12, 7, 9, 4, 47, tzinfo=get_localzone()
                        ),
                        "prob_meas1_prep0",
                        None,
                        0.000,
                    )
                ],
                [
                    Nduv(
                        datetime.datetime(
                            2020, 12, 7, 9, 4, 47, tzinfo=get_localzone()
                        ),
                        "readout_length",
                        "ns",
                        self.sample[0]["rec_length"] * 1e9
                        + self.sample[0]["rec_offset"] * 1e9,
                    )
                ],
            ],
            "general": [
                Nduv(
                    "2021-07-06T09:06:46Z",
                    "readout_length",
                    "ns",
                    self.sample[0]["rec_length"] * 1e9,
                ),
                Nduv("2021-07-06T09:06:46Z", "readout_error", None, 0.000),
            ],
        }

        super().__init__(
            configuration=BackendConfiguration.from_dict(self._configuration),
            provider=provider,
        )

    @classmethod
    def _default_options(cls):
        """Set default backend options to run the job on the QiController

        :return: Options object of default backend parameters

        """
        return Options(shots=1024, memory=False)

    def circuit_to_qic(self, circuit: QuantumCircuit):
        """Translate Qiskit code to QiCode and create a QiJob

        :param circuit:
          Quantum circuit in Qiskit code

        :raises RuntimeError:
          if a quantum operation is not supported by the QiController backend

        :return:
            The QiJob with equivalent instructions as the Qiskit circuit
        """
        with QiJob() as job:
            cells = QiCells(circuit.num_qubits + len(self.coupling_map))
            state = [QiStateVariable() for _ in range(circuit.num_qubits)]

            for gate in circuit.data:  # type: CircuitInstruction
                instr: Instruction = gate[0]
                qubits: list[Qubit] = gate[1]
                if instr.condition is None:
                    if instr.name in qiskit_to_qicode:
                        if len(qubits) == 1:
                            if instr.name == "measure":
                                QiGates.Measure(
                                    cells[qubits[0]._index],
                                    state_to=state[qubits[0]._index],
                                )
                            else:
                                qiskit_to_qicode[instr.name](
                                    cells[qubits[0]._index], *instr.params
                                )
                        elif len(qubits) == 2:
                            if (
                                [qubits[0]._index, qubits[1]._index]
                                in self.coupling_map
                            ) and (
                                [qubits[1]._index, qubits[0]._index]
                                in self.coupling_map
                            ):
                                raise RuntimeError(
                                    f"Only one coupling map of the qubits {[qubits[0]._index, qubits[1]._index]} has to be included in the list"
                                )

                            if [
                                qubits[0]._index,
                                qubits[1]._index,
                            ] in self.coupling_map:
                                coupling_cell_index = (
                                    circuit.num_qubits
                                    + self.coupling_map.index(
                                        [qubits[0]._index, qubits[1]._index]
                                    )
                                )
                            elif [
                                qubits[1]._index,
                                qubits[0]._index,
                            ] in self.coupling_map:
                                coupling_cell_index = (
                                    circuit.num_qubits
                                    + self.coupling_map.index(
                                        [qubits[1]._index, qubits[0]._index]
                                    )
                                )

                            else:
                                raise RuntimeError(
                                    f"The coupling map of the qubits {[qubits[0]._index, qubits[1]._index]} is not included"
                                )

                            qiskit_to_qicode[instr.name](
                                cells[qubits[0]._index],
                                cells[qubits[1]._index],
                                cells[coupling_cell_index],
                            )
                    elif instr.name == "barrier":
                        Sync(
                            *[
                                cells[qubits[qubit]._index]
                                for qubit in range(len(qubits))
                            ]
                        )
                    else:
                        raise RuntimeError(
                            f"Operation {instr.name} is not supported by the QiController"
                        )
                else:
                    with If(state[qubits[0]._index] == instr.condition[1]):
                        if instr.name in qiskit_to_qicode:
                            qiskit_to_qicode[instr.name](
                                cells[instr.condition[0][0].index], *instr.params
                            )

                        else:
                            raise RuntimeError(
                                f"Operation {instr.name} is not supported by the QiController"
                            )
        return job

    def run(self, run_input, shots=None, memory=False):
        """Run QiJob on QiController backend

        :param circuit:
            Quantum circuit in Qiskit code
        :type circuit: QuantumCircuit

        :param shots:
            Number of shots to run the QiJob

        :raises ValueError:
            If the number of shots exceeds the maximum

        :return:
            QiController_job object
        """
        if shots is None:
            shots = self._default_options().shots

        elif shots > self._configuration.max_shots:
            raise ValueError(
                f"Number of shots is larger than maximum of {self._configuration.max_shots} shots"
            )
        elif shots < 0:
            raise ValueError("Number of shots must be strictly positive")

        elif isinstance(run_input, qobj_mod.QasmQobj):
            raise QiskitError("Qasm strings are not accepted")

        elif isinstance(run_input, qobj_mod.PulseQobj):
            raise QiskitError("Pulse jobs are not accepted")

        else:
            job = self.circuit_to_qic(run_input)

            if memory is True:
                result = [""] * shots

                job.run(self.backend, self.sample, shots, data_collection="states")

                for qubit in range(run_input.num_qubits):
                    state = job.cells[qubit].data("result")

                    for i, res in enumerate(result):
                        result[i] = res + str(state[i])

                for i, res in enumerate(result):
                    result[i] = reverse_string(res)

            else:
                job.run(self.backend, self.sample, shots, data_collection="counts")
                result = job.cells[0].data("result")

        return QiController_job(
            backend=self.backend, sample=self.sample, shots=shots, measurements=result
        )
