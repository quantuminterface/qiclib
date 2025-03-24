# Copyright © 2017-2023 Quantum Interface (quantuminterface@ipe.kit.edu)
# Lukas Scheller, IPE, Karlsruhe Institute of Technology
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

from unittest import mock

from qiclib.packages.grpc.taskrunner_pb2 import *


class TaskrunnerSettings:
    def __init__(self):
        self.databoxs = {}


_settings = TaskrunnerSettings()


def _get_databoxes(dtype):
    is_64 = dtype[-2:] == "64"
    is_signed = dtype[0] == "i"
    if is_64 and is_signed:
        reply = DataboxReplyINT64
    elif is_64 and not is_signed:
        reply = DataboxReplyUINT64
    elif not is_64 and is_signed:
        reply = DataboxReplyINT32
    elif not is_64 and not is_signed:
        reply = DataboxReplyUINT32
    else:
        raise AssertionError
    for idx, all_data in _settings.databoxs[dtype].items():
        yield from (reply(data=single, index=idx) for single in all_data)


class MockTaskRunnerServiceStub:
    def __init__(self, _):
        pass

    def GetStatus(self, _):
        return StatusReply()

    def GetTaskErrorMessages(self, _):
        return GetTaskErrorMessagesReply()

    def CompileTask(self, _):
        return Empty()

    def SetParameter(self, _):
        return Empty()

    def StartTask(self, _):
        return Empty()

    def GetTaskState(self, _):
        return TaskStateReply(busy=False, done=True)

    def GetDataboxesINT8(self, _):
        return _get_databoxes("int8")

    def GetDataboxesUINT8(self, _):
        return _get_databoxes("uint8")

    def GetDataboxesINT16(self, _):
        return _get_databoxes("int16")

    def GetDataboxesUINT16(self, _):
        return _get_databoxes("uint16")

    def GetDataboxesINT32(self, _):
        return _get_databoxes("int32")

    def GetDataboxesUINT32(self, _):
        return _get_databoxes("uint32")

    def GetDataboxesINT64(self, _):
        return _get_databoxes("int64")

    def GetDataboxesUINT64(self, _):
        return _get_databoxes("uint64")


def patch(databoxes: dict | None = None):
    """
    TODO: doc
    """
    global _settings
    _settings = TaskrunnerSettings()
    _settings.databoxs = databoxes or {}
    return mock.patch(
        "qiclib.packages.grpc.taskrunner_pb2_grpc.TaskRunnerServiceStub",
        new=MockTaskRunnerServiceStub,
    )
