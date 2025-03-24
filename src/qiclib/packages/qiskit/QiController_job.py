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
from typing import TYPE_CHECKING

from qiskit.providers.jobstatus import JobStatus
from qiskit.result import Result

from qiclib.code import QiCells

if TYPE_CHECKING:
    from qiclib.packages.qiskit.QiController_backend import QiController_backend


class QiController_job:
    """The QiController_job object retrieves the result of a QiJob run on the QiController backend

    :param backend:
        Name of the backend
    :param sample:
        The sample object storing the backend properties for experiment
    :param shots:
        Number of shots to execute the QiJob
    :param measurements:
        Measurement result given in a dictionary of quantum states and their frequencies

    :ivar qobj:
        The unique Id sequence of the submitted job
    :ivar qobj_id:
         A unique identifier of the qobj
    :ivar job_id:
         A unique identifier of the submitted job

    """

    def __init__(
        self,
        backend: "QiController_backend",
        sample: QiCells,
        shots: int,
        measurements: dict,
    ):
        self.backend = backend
        self.sample = sample
        self.shots = shots
        self.measurements = measurements
        self.qobj = "Qobj001"
        self.qobj_id = "EXP001"
        self.job_id = "EXP001"

    def result(self) -> Result:
        """Retrieve measurement result

        :return: Qiskit Result object
        """
        results = [
            {
                "success": True,
                "shots": self.shots,
                "data": {"counts": self.measurements},
                "header": {
                    "memory_slots": len(self.sample.cells),
                    "name": self.qobj,
                },
            }
        ]

        return Result.from_dict(
            {
                "results": results,
                "backend_name": self.backend.ip_address,
                "backend_version": self.backend.driver_version,
                "success": True,
                "qobj_id": self.qobj_id,
                "job_id": self.job_id,
            }
        )

    def get_counts(self):
        """Retrieve the counts of measurement result

        :return:
            Dictionary object of quantum states and their frequencies

        """
        return self.result().get_counts()

    def get_memory(self):
        """Retrieve the measurement results of each single shot

        :return:
            List object of quantum states

        """
        return self.measurements

    def cancel(self):
        """Cancel job execution"""

        self.backend.stop()

    def status(self):
        """Retrieve the status of the submitted job

        :return:
            Job status of the submitted job

        """

        if self.counts:
            status = JobStatus.DONE

        else:
            status = JobStatus.ERROR

        return status

    def submit(self):
        """Submit a job to QiController backend

        :raises NotImplementedError:
            Job not submitted to the backend

        """

        raise NotImplementedError
