from unittest import mock

from qiclib.packages.grpc.datatypes_pb2 import Empty
from qiclib.packages.grpc.qic_storage_pb2 import *


class MockStorageService:
    def __init__(self, _):
        self._data = []

    def ReadData(self, request: ReadDataRequest):
        return ReadDataResponse(data=[1, 2, 3])

    def WriteData(self, request: WriteDataRequest):
        return Empty()


module = "qiclib.packages.grpc.qic_storage_pb2_grpc.StorageStub"


def patch():
    return mock.patch(module, new=MockStorageService)
