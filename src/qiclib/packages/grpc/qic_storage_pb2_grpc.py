# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
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
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from . import qic_storage_pb2 as qic__storage__pb2


class StorageStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Reset = channel.unary_unary(
            "/qic_storage.Storage/Reset",
            request_serializer=qic__storage__pb2.EndpointIndex.SerializeToString,
            response_deserializer=qic__storage__pb2.Empty.FromString,
        )
        self.SetStateHandling = channel.unary_unary(
            "/qic_storage.Storage/SetStateHandling",
            request_serializer=qic__storage__pb2.StateHandling.SerializeToString,
            response_deserializer=qic__storage__pb2.Empty.FromString,
        )
        self.GetStateHandling = channel.unary_unary(
            "/qic_storage.Storage/GetStateHandling",
            request_serializer=qic__storage__pb2.EndpointIndex.SerializeToString,
            response_deserializer=qic__storage__pb2.StateHandling.FromString,
        )
        self.GetStateAccumulation = channel.unary_unary(
            "/qic_storage.Storage/GetStateAccumulation",
            request_serializer=qic__storage__pb2.EndpointIndex.SerializeToString,
            response_deserializer=qic__storage__pb2.StateAccumulation.FromString,
        )
        self.SetResultHandling = channel.unary_unary(
            "/qic_storage.Storage/SetResultHandling",
            request_serializer=qic__storage__pb2.ResultHandling.SerializeToString,
            response_deserializer=qic__storage__pb2.Empty.FromString,
        )
        self.GetResultHandling = channel.unary_unary(
            "/qic_storage.Storage/GetResultHandling",
            request_serializer=qic__storage__pb2.EndpointIndex.SerializeToString,
            response_deserializer=qic__storage__pb2.ResultHandling.FromString,
        )
        self.SetAveragedHandling = channel.unary_unary(
            "/qic_storage.Storage/SetAveragedHandling",
            request_serializer=qic__storage__pb2.AveragedHandling.SerializeToString,
            response_deserializer=qic__storage__pb2.Empty.FromString,
        )
        self.GetAveragedHandling = channel.unary_unary(
            "/qic_storage.Storage/GetAveragedHandling",
            request_serializer=qic__storage__pb2.EndpointIndex.SerializeToString,
            response_deserializer=qic__storage__pb2.AveragedHandling.FromString,
        )
        self.SetBramControl = channel.unary_unary(
            "/qic_storage.Storage/SetBramControl",
            request_serializer=qic__storage__pb2.BramControl.SerializeToString,
            response_deserializer=qic__storage__pb2.Empty.FromString,
        )
        self.GetBramStatus = channel.unary_unary(
            "/qic_storage.Storage/GetBramStatus",
            request_serializer=qic__storage__pb2.BramIndex.SerializeToString,
            response_deserializer=qic__storage__pb2.BramStatus.FromString,
        )
        self.ResetBramData = channel.unary_unary(
            "/qic_storage.Storage/ResetBramData",
            request_serializer=qic__storage__pb2.BramIndex.SerializeToString,
            response_deserializer=qic__storage__pb2.Empty.FromString,
        )
        self.GetBramResultData = channel.unary_unary(
            "/qic_storage.Storage/GetBramResultData",
            request_serializer=qic__storage__pb2.EndpointIndex.SerializeToString,
            response_deserializer=qic__storage__pb2.ResultData.FromString,
        )
        self.GetBramAveragedData = channel.unary_unary(
            "/qic_storage.Storage/GetBramAveragedData",
            request_serializer=qic__storage__pb2.EndpointIndex.SerializeToString,
            response_deserializer=qic__storage__pb2.AveragedData.FromString,
        )
        self.GetBramStateData = channel.unary_unary(
            "/qic_storage.Storage/GetBramStateData",
            request_serializer=qic__storage__pb2.EndpointIndex.SerializeToString,
            response_deserializer=qic__storage__pb2.StateData.FromString,
        )
        self.GetBramDataUInt32 = channel.unary_unary(
            "/qic_storage.Storage/GetBramDataUInt32",
            request_serializer=qic__storage__pb2.BramIndex.SerializeToString,
            response_deserializer=qic__storage__pb2.BramDataUInt32.FromString,
        )
        self.GetBramDataInt32 = channel.unary_unary(
            "/qic_storage.Storage/GetBramDataInt32",
            request_serializer=qic__storage__pb2.BramIndex.SerializeToString,
            response_deserializer=qic__storage__pb2.BramDataInt32.FromString,
        )
        self.GetBramLatestData = channel.unary_unary(
            "/qic_storage.Storage/GetBramLatestData",
            request_serializer=qic__storage__pb2.BramIndex.SerializeToString,
            response_deserializer=qic__storage__pb2.LatestData.FromString,
        )
        self.IsDataLost = channel.unary_unary(
            "/qic_storage.Storage/IsDataLost",
            request_serializer=qic__storage__pb2.EndpointIndex.SerializeToString,
            response_deserializer=qic__storage__pb2.DataLost.FromString,
        )


class StorageServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Reset(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def SetStateHandling(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetStateHandling(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetStateAccumulation(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def SetResultHandling(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetResultHandling(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def SetAveragedHandling(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetAveragedHandling(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def SetBramControl(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetBramStatus(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def ResetBramData(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetBramResultData(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetBramAveragedData(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetBramStateData(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetBramDataUInt32(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetBramDataInt32(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetBramLatestData(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def IsDataLost(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_StorageServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "Reset": grpc.unary_unary_rpc_method_handler(
            servicer.Reset,
            request_deserializer=qic__storage__pb2.EndpointIndex.FromString,
            response_serializer=qic__storage__pb2.Empty.SerializeToString,
        ),
        "SetStateHandling": grpc.unary_unary_rpc_method_handler(
            servicer.SetStateHandling,
            request_deserializer=qic__storage__pb2.StateHandling.FromString,
            response_serializer=qic__storage__pb2.Empty.SerializeToString,
        ),
        "GetStateHandling": grpc.unary_unary_rpc_method_handler(
            servicer.GetStateHandling,
            request_deserializer=qic__storage__pb2.EndpointIndex.FromString,
            response_serializer=qic__storage__pb2.StateHandling.SerializeToString,
        ),
        "GetStateAccumulation": grpc.unary_unary_rpc_method_handler(
            servicer.GetStateAccumulation,
            request_deserializer=qic__storage__pb2.EndpointIndex.FromString,
            response_serializer=qic__storage__pb2.StateAccumulation.SerializeToString,
        ),
        "SetResultHandling": grpc.unary_unary_rpc_method_handler(
            servicer.SetResultHandling,
            request_deserializer=qic__storage__pb2.ResultHandling.FromString,
            response_serializer=qic__storage__pb2.Empty.SerializeToString,
        ),
        "GetResultHandling": grpc.unary_unary_rpc_method_handler(
            servicer.GetResultHandling,
            request_deserializer=qic__storage__pb2.EndpointIndex.FromString,
            response_serializer=qic__storage__pb2.ResultHandling.SerializeToString,
        ),
        "SetAveragedHandling": grpc.unary_unary_rpc_method_handler(
            servicer.SetAveragedHandling,
            request_deserializer=qic__storage__pb2.AveragedHandling.FromString,
            response_serializer=qic__storage__pb2.Empty.SerializeToString,
        ),
        "GetAveragedHandling": grpc.unary_unary_rpc_method_handler(
            servicer.GetAveragedHandling,
            request_deserializer=qic__storage__pb2.EndpointIndex.FromString,
            response_serializer=qic__storage__pb2.AveragedHandling.SerializeToString,
        ),
        "SetBramControl": grpc.unary_unary_rpc_method_handler(
            servicer.SetBramControl,
            request_deserializer=qic__storage__pb2.BramControl.FromString,
            response_serializer=qic__storage__pb2.Empty.SerializeToString,
        ),
        "GetBramStatus": grpc.unary_unary_rpc_method_handler(
            servicer.GetBramStatus,
            request_deserializer=qic__storage__pb2.BramIndex.FromString,
            response_serializer=qic__storage__pb2.BramStatus.SerializeToString,
        ),
        "ResetBramData": grpc.unary_unary_rpc_method_handler(
            servicer.ResetBramData,
            request_deserializer=qic__storage__pb2.BramIndex.FromString,
            response_serializer=qic__storage__pb2.Empty.SerializeToString,
        ),
        "GetBramResultData": grpc.unary_unary_rpc_method_handler(
            servicer.GetBramResultData,
            request_deserializer=qic__storage__pb2.EndpointIndex.FromString,
            response_serializer=qic__storage__pb2.ResultData.SerializeToString,
        ),
        "GetBramAveragedData": grpc.unary_unary_rpc_method_handler(
            servicer.GetBramAveragedData,
            request_deserializer=qic__storage__pb2.EndpointIndex.FromString,
            response_serializer=qic__storage__pb2.AveragedData.SerializeToString,
        ),
        "GetBramStateData": grpc.unary_unary_rpc_method_handler(
            servicer.GetBramStateData,
            request_deserializer=qic__storage__pb2.EndpointIndex.FromString,
            response_serializer=qic__storage__pb2.StateData.SerializeToString,
        ),
        "GetBramDataUInt32": grpc.unary_unary_rpc_method_handler(
            servicer.GetBramDataUInt32,
            request_deserializer=qic__storage__pb2.BramIndex.FromString,
            response_serializer=qic__storage__pb2.BramDataUInt32.SerializeToString,
        ),
        "GetBramDataInt32": grpc.unary_unary_rpc_method_handler(
            servicer.GetBramDataInt32,
            request_deserializer=qic__storage__pb2.BramIndex.FromString,
            response_serializer=qic__storage__pb2.BramDataInt32.SerializeToString,
        ),
        "GetBramLatestData": grpc.unary_unary_rpc_method_handler(
            servicer.GetBramLatestData,
            request_deserializer=qic__storage__pb2.BramIndex.FromString,
            response_serializer=qic__storage__pb2.LatestData.SerializeToString,
        ),
        "IsDataLost": grpc.unary_unary_rpc_method_handler(
            servicer.IsDataLost,
            request_deserializer=qic__storage__pb2.EndpointIndex.FromString,
            response_serializer=qic__storage__pb2.DataLost.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        "qic_storage.Storage", rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))


# This class is part of an EXPERIMENTAL API.
class Storage(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Reset(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/qic_storage.Storage/Reset",
            qic__storage__pb2.EndpointIndex.SerializeToString,
            qic__storage__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def SetStateHandling(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/qic_storage.Storage/SetStateHandling",
            qic__storage__pb2.StateHandling.SerializeToString,
            qic__storage__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def GetStateHandling(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/qic_storage.Storage/GetStateHandling",
            qic__storage__pb2.EndpointIndex.SerializeToString,
            qic__storage__pb2.StateHandling.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def GetStateAccumulation(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/qic_storage.Storage/GetStateAccumulation",
            qic__storage__pb2.EndpointIndex.SerializeToString,
            qic__storage__pb2.StateAccumulation.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def SetResultHandling(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/qic_storage.Storage/SetResultHandling",
            qic__storage__pb2.ResultHandling.SerializeToString,
            qic__storage__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def GetResultHandling(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/qic_storage.Storage/GetResultHandling",
            qic__storage__pb2.EndpointIndex.SerializeToString,
            qic__storage__pb2.ResultHandling.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def SetAveragedHandling(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/qic_storage.Storage/SetAveragedHandling",
            qic__storage__pb2.AveragedHandling.SerializeToString,
            qic__storage__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def GetAveragedHandling(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/qic_storage.Storage/GetAveragedHandling",
            qic__storage__pb2.EndpointIndex.SerializeToString,
            qic__storage__pb2.AveragedHandling.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def SetBramControl(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/qic_storage.Storage/SetBramControl",
            qic__storage__pb2.BramControl.SerializeToString,
            qic__storage__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def GetBramStatus(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/qic_storage.Storage/GetBramStatus",
            qic__storage__pb2.BramIndex.SerializeToString,
            qic__storage__pb2.BramStatus.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def ResetBramData(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/qic_storage.Storage/ResetBramData",
            qic__storage__pb2.BramIndex.SerializeToString,
            qic__storage__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def GetBramResultData(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/qic_storage.Storage/GetBramResultData",
            qic__storage__pb2.EndpointIndex.SerializeToString,
            qic__storage__pb2.ResultData.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def GetBramAveragedData(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/qic_storage.Storage/GetBramAveragedData",
            qic__storage__pb2.EndpointIndex.SerializeToString,
            qic__storage__pb2.AveragedData.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def GetBramStateData(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/qic_storage.Storage/GetBramStateData",
            qic__storage__pb2.EndpointIndex.SerializeToString,
            qic__storage__pb2.StateData.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def GetBramDataUInt32(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/qic_storage.Storage/GetBramDataUInt32",
            qic__storage__pb2.BramIndex.SerializeToString,
            qic__storage__pb2.BramDataUInt32.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def GetBramDataInt32(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/qic_storage.Storage/GetBramDataInt32",
            qic__storage__pb2.BramIndex.SerializeToString,
            qic__storage__pb2.BramDataInt32.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def GetBramLatestData(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/qic_storage.Storage/GetBramLatestData",
            qic__storage__pb2.BramIndex.SerializeToString,
            qic__storage__pb2.LatestData.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def IsDataLost(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/qic_storage.Storage/IsDataLost",
            qic__storage__pb2.EndpointIndex.SerializeToString,
            qic__storage__pb2.DataLost.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )
