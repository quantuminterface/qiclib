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
"""Driver to control the Taskrunner on the Hardware Platform."""

from __future__ import annotations

import os
from enum import Enum
from typing import Any

import qiclib.packages.grpc.datatypes_pb2 as dt
import qiclib.packages.grpc.taskrunner_pb2 as proto
import qiclib.packages.grpc.taskrunner_pb2_grpc as grpc_stub
from qiclib.experiment.rtos_tasks import get_task_source
from qiclib.hardware.platform_component import (
    PlatformComponent,
    platform_attribute,
    platform_attribute_collector,
)
from qiclib.packages.servicehub import ServiceHubCall


@platform_attribute_collector
class TaskRunner(PlatformComponent):
    """Driver to control the Taskrunner on the Hardware Platform."""

    def __init__(
        self,
        name: str,
        connection,
        controller,
        qkit_instrument=True,
    ):
        super().__init__(name, connection, controller, qkit_instrument)
        self._stub = grpc_stub.TaskRunnerServiceStub(self._conn.channel)

    @property
    @platform_attribute
    @ServiceHubCall(
        errormsg="Could not fetch the current firmware hash of the Taskrunner"
    )
    def firmware_hash(self):
        """The hash of the current firmware running on the realtime core."""
        return self._stub.GetStatus(dt.Empty()).firmware_hash

    @property
    @platform_attribute
    @ServiceHubCall(
        errormsg="Could not determine the build date of the Taskrunner firmware"
    )
    def firmware_build_date(self):
        """Returns the build date of the Taskrunner firmware."""
        return self._stub.GetStatus(dt.Empty()).build_date

    @property
    @platform_attribute
    @ServiceHubCall(
        errormsg="Could not determine the build commit of the Taskrunner firmware"
    )
    def firmware_build_commit(self):
        """Returns the build commit hash of the Taskrunner firmware."""
        return self._stub.GetStatus(dt.Empty()).build_commit

    @property
    @platform_attribute
    @ServiceHubCall(errormsg="Could not determine the status of the taskrunner")
    def loaded_task(self):
        """The name of the currently loaded task."""
        return self._stub.GetStatus(dt.Empty()).task_name

    @property
    @ServiceHubCall(errormsg="Could not determine the progress of the task")
    def task_progress(self):
        """Returns the progress of the task"""
        return self._stub.GetStatus(dt.Empty()).task_progress

    @property
    @ServiceHubCall(errormsg="Could not determine number of available databoxes")
    def databoxes_available(self):
        """Returns the number of available databoxes."""
        return self._stub.GetStatus(dt.Empty()).databoxes_available

    @property
    @ServiceHubCall(errormsg="Could not determine state of the taskrunner")
    def busy(self):
        """Returns if the taskrunner is currently busy."""
        return self._stub.GetTaskState(dt.Empty()).busy

    @property
    @ServiceHubCall(errormsg="Could not determine if task has finished")
    def task_done(self):
        """Returns if the task has finished."""
        return self._stub.GetTaskState(dt.Empty()).done

    @property
    @ServiceHubCall(errormsg="Could not determine if task has error messages")
    def task_errormsg_available(self):
        """Returns if task has error messages."""
        return self._stub.GetTaskState(dt.Empty()).error_msg_available

    @property
    @ServiceHubCall(errormsg="Could not determine if error message queue is full")
    def task_errormsg_queue_full(self):
        """Returns if if error message queue is full."""
        return self._stub.GetTaskState(dt.Empty()).error_msg_queue_full

    @ServiceHubCall(errormsg="Failed to start task")
    def start_task(self, loop=False, overwrite=False):
        """Starts the execution of a previously loaded task.

        :param loop: bool, optional
            if the task should be executed in a loop, by default False
        :param overwrite: bool, optional
            if a current running task should be stopped, by default False
        """
        self._stub.StartTask(
            proto.StartTaskRequest(looping=loop, stop_running=overwrite)
        )

    @ServiceHubCall(errormsg="Failed to stop task")
    def stop_task(self):
        """Stops the execution of running task."""
        self._stub.StopTask(proto.StopTaskRequest())

    @ServiceHubCall(errormsg="Failed to reset task")
    def reset_task(self):
        """Resets (unloads) a loaded task."""
        self._stub.StopTask(proto.StopTaskRequest(reset=True))

    @ServiceHubCall(errormsg="Failed to load task binary")
    def load_task_binary(self, filename, taskname):
        """Loads a task binary into the taskrunner.
        The *taskname* needs to match the name of the task to load
        in order to verify that it is indeed the desired task file.

        :param filename: str
            name of the file with the task
        :param taskname: str
            name of the task

        :raises ValueError:
            if the path of the file is not found
        """
        if not os.path.exists(filename):
            raise ValueError("File not found!")

        with open(filename, "rb") as f:
            binary = f.read()
        self._stub.ProgramTask(proto.ProgramTaskRequest(name=taskname, task=binary))

    @ServiceHubCall(errormsg="Failed to compile and load task binary")
    def load_task_source(self, filename, taskname):
        """Loads a task source file `filename` into the taskrunner.
        `taskname` can be freely chosen to later identify the task on the platform.

        :param filename:
            name of the file with the task
        :param taskname:
            name of the task
        """
        if os.path.isfile(filename):
            # File name can be full path to a file
            filepath = filename
        else:
            # or just the file name -> pick from task repository
            filepath = get_task_source(filename)

        with open(filepath, "rb") as f:
            binary = f.read()

        self._stub.CompileTask(proto.ProgramTaskRequest(name=taskname, task=binary))

    @ServiceHubCall(errormsg="Failed to set parameters")
    def set_param_list(self, param_list):
        """Sets the parameters for the task. param_list has to be an array of 32bit values."""
        self._stub.SetParameter(proto.ParameterRequest(parameters=param_list))

    class DataMode(Enum):
        INT8 = 1
        UINT8 = 2
        INT16 = 3
        UINT16 = 4
        INT32 = 5
        UINT32 = 6
        INT64 = 7
        UINT64 = 8

    @ServiceHubCall(errormsg="Failed to fetch databoxes from taskrunner")
    def get_databoxes_with_mode(
        self, mode=DataMode.INT32, require_done=True
    ) -> list[list[Any]]:
        """Retrieves data from a previously started task on the R5.
        Depending on the parameter mode, the data is interpreted differently.

        :param mode:
            DataMode of the databoxes, by default DataMode.INT32
        :param require_done:
            if the task has to be finished before fetching data, by default True

        :return:
            A list of databoxes, being list of values themselves, either int32 or uint32.

        :raises Exception:
            If require_done is True and the Task is not finished
        :raises ValueError:
            If the data mode is not known
        :raises Exception:
            If require_done and not data is available
        """
        self.check_task_errors()

        if require_done and not self.task_done:
            raise RuntimeError("Task should be finished prior to fetching data.")

        method_call = {
            TaskRunner.DataMode.INT8: self._stub.GetDataboxesINT8,
            TaskRunner.DataMode.UINT8: self._stub.GetDataboxesUINT8,
            TaskRunner.DataMode.INT16: self._stub.GetDataboxesINT16,
            TaskRunner.DataMode.UINT16: self._stub.GetDataboxesUINT16,
            TaskRunner.DataMode.INT32: self._stub.GetDataboxesINT32,
            TaskRunner.DataMode.UINT32: self._stub.GetDataboxesUINT32,
            TaskRunner.DataMode.INT64: self._stub.GetDataboxesINT64,
            TaskRunner.DataMode.UINT64: self._stub.GetDataboxesUINT64,
        }.get(mode, None)
        if method_call is None:
            raise ValueError("Data mode is unknown! Only use DataMode Enum values.")

        databoxes: list[list[Any]] = []
        last_index = -1
        for databox_reply in method_call(dt.Empty()):
            # print databox_reply.index, databox_reply.data[:]
            if last_index != databox_reply.index:
                # Create new (empty) databox in list
                databoxes.append([])
                last_index = databox_reply.index
            # Fill the latest databox with content
            databoxes[-1].extend(databox_reply.data[:])

        if require_done and not databoxes:
            raise RuntimeError(
                "No data available to fetch. Are you sure the task completed successfully?"
            )

        return databoxes

    def get_databoxes(self, require_done=True):
        """Retrieves data from a previously started task on the R5.

        Data is interpreted as 32bit signed integer values which are returned as array.
        """
        return self.get_databoxes_with_mode(TaskRunner.DataMode.INT32, require_done)

    def get_databoxes_INT8(self, require_done=True):
        """Retrieves data from a previously started task on the R5.

        Data is interpreted as 8bit signed integer values which are returned as array.
        """
        return self.get_databoxes_with_mode(TaskRunner.DataMode.INT8, require_done)

    def get_databoxes_UINT8(self, require_done=True):
        """Retrieves data from a previously started task on the R5.

        Data is interpreted as 8bit unsigned integer values which are returned as array.
        """
        return self.get_databoxes_with_mode(TaskRunner.DataMode.UINT8, require_done)

    def get_databoxes_INT16(self, require_done=True):
        """Retrieves data from a previously started task on the R5.

        Data is interpreted as 16bit signed integer values which are returned as array.
        """
        return self.get_databoxes_with_mode(TaskRunner.DataMode.INT16, require_done)

    def get_databoxes_UINT16(self, require_done=True):
        """Retrieves data from a previously started task on the R5.

        Data is interpreted as 16bit unsigned integer values which are returned as array.
        """
        return self.get_databoxes_with_mode(TaskRunner.DataMode.UINT16, require_done)

    def get_databoxes_INT32(self, require_done=True):
        """Retrieves data from a previously started task on the R5.

        Data is interpreted as 32bit signed integer values which are returned as array.
        """
        return self.get_databoxes_with_mode(TaskRunner.DataMode.INT32, require_done)

    def get_databoxes_UINT32(self, require_done=True):
        """Retrieves data from a previously started task on the R5.

        Data is interpreted as 32bit unsigned integer values which are returned as array.
        """
        return self.get_databoxes_with_mode(TaskRunner.DataMode.UINT32, require_done)

    def get_databoxes_INT64(self, require_done=True):
        """Retrieves data from a previously started task on the R5.

        Data is interpreted as 64bit signed integer values which are returned as array.
        """
        return self.get_databoxes_with_mode(TaskRunner.DataMode.INT64, require_done)

    def get_databoxes_UINT64(self, require_done=True):
        """Retrieves data from a previously started task on the R5.

        Data is interpreted as 64bit unsigned integer values which are returned as array.
        """
        return self.get_databoxes_with_mode(TaskRunner.DataMode.UINT64, require_done)

    @ServiceHubCall
    def get_error_messages(self):
        """Retrieves all error messages from the task"""
        reply = self._stub.GetTaskErrorMessages(dt.Empty())
        return reply.message[:]

    def check_task_errors(self):
        errors = self.get_error_messages()
        if errors:
            raise RuntimeError(
                "The following error messages were retrieved "
                + "from the Taskrunner:\n{}".format("\n".join(errors))
            )

    # DEPRECATED STUFF
    @property
    def data_size(self):
        """TODO Replace by progress in all experiments."""
        raise DeprecationWarning(
            "data_size is not supported anymore! Use task_progress instead!"
        )
