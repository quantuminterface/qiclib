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
# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from . import pimc_pb2 as pimc__pb2


class PIMCServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.SetReset = channel.unary_unary(
            "/pimc.PIMCService/SetReset",
            request_serializer=pimc__pb2.Empty.SerializeToString,
            response_deserializer=pimc__pb2.Empty.FromString,
        )
        self.GetBusy = channel.unary_unary(
            "/pimc.PIMCService/GetBusy",
            request_serializer=pimc__pb2.Empty.SerializeToString,
            response_deserializer=pimc__pb2.Bool.FromString,
        )
        self.GetReady = channel.unary_unary(
            "/pimc.PIMCService/GetReady",
            request_serializer=pimc__pb2.Empty.SerializeToString,
            response_deserializer=pimc__pb2.Bool.FromString,
        )
        self.SetSWReady = channel.unary_unary(
            "/pimc.PIMCService/SetSWReady",
            request_serializer=pimc__pb2.Empty.SerializeToString,
            response_deserializer=pimc__pb2.Empty.FromString,
        )
        self.GetSWReady = channel.unary_unary(
            "/pimc.PIMCService/GetSWReady",
            request_serializer=pimc__pb2.Empty.SerializeToString,
            response_deserializer=pimc__pb2.Bool.FromString,
        )
        self.SetResetDone = channel.unary_unary(
            "/pimc.PIMCService/SetResetDone",
            request_serializer=pimc__pb2.Empty.SerializeToString,
            response_deserializer=pimc__pb2.Empty.FromString,
        )
        self.GetResetDone = channel.unary_unary(
            "/pimc.PIMCService/GetResetDone",
            request_serializer=pimc__pb2.Empty.SerializeToString,
            response_deserializer=pimc__pb2.Bool.FromString,
        )
        self.GetChipVersion = channel.unary_unary(
            "/pimc.PIMCService/GetChipVersion",
            request_serializer=pimc__pb2.Empty.SerializeToString,
            response_deserializer=pimc__pb2.UInt.FromString,
        )
        self.GetModuleChipVersion = channel.unary_unary(
            "/pimc.PIMCService/GetModuleChipVersion",
            request_serializer=pimc__pb2.Empty.SerializeToString,
            response_deserializer=pimc__pb2.UInt.FromString,
        )
        self.GetInfo = channel.unary_unary(
            "/pimc.PIMCService/GetInfo",
            request_serializer=pimc__pb2.Empty.SerializeToString,
            response_deserializer=pimc__pb2.Info.FromString,
        )
        self.GetInfoString = channel.unary_unary(
            "/pimc.PIMCService/GetInfoString",
            request_serializer=pimc__pb2.Empty.SerializeToString,
            response_deserializer=pimc__pb2.String.FromString,
        )
        self.GetAllClocksValid = channel.unary_unary(
            "/pimc.PIMCService/GetAllClocksValid",
            request_serializer=pimc__pb2.Empty.SerializeToString,
            response_deserializer=pimc__pb2.Bool.FromString,
        )
        self.GetClocksInfo = channel.unary_unary(
            "/pimc.PIMCService/GetClocksInfo",
            request_serializer=pimc__pb2.Empty.SerializeToString,
            response_deserializer=pimc__pb2.String.FromString,
        )
        self.GetStatusInputs = channel.unary_unary(
            "/pimc.PIMCService/GetStatusInputs",
            request_serializer=pimc__pb2.Empty.SerializeToString,
            response_deserializer=pimc__pb2.String.FromString,
        )
        self.GetReadyMask = channel.unary_unary(
            "/pimc.PIMCService/GetReadyMask",
            request_serializer=pimc__pb2.Empty.SerializeToString,
            response_deserializer=pimc__pb2.String.FromString,
        )
        self.GetReadyState = channel.unary_unary(
            "/pimc.PIMCService/GetReadyState",
            request_serializer=pimc__pb2.Empty.SerializeToString,
            response_deserializer=pimc__pb2.String.FromString,
        )
        self.GetStatus = channel.unary_unary(
            "/pimc.PIMCService/GetStatus",
            request_serializer=pimc__pb2.Empty.SerializeToString,
            response_deserializer=pimc__pb2.PIMCStatus.FromString,
        )
        self.GetProject = channel.unary_unary(
            "/pimc.PIMCService/GetProject",
            request_serializer=pimc__pb2.Empty.SerializeToString,
            response_deserializer=pimc__pb2.Project.FromString,
        )
        self.GetBuildTime = channel.unary_unary(
            "/pimc.PIMCService/GetBuildTime",
            request_serializer=pimc__pb2.Empty.SerializeToString,
            response_deserializer=pimc__pb2.String.FromString,
        )
        self.GetBoardInfo = channel.unary_unary(
            "/pimc.PIMCService/GetBoardInfo",
            request_serializer=pimc__pb2.Empty.SerializeToString,
            response_deserializer=pimc__pb2.BoardInfo.FromString,
        )


class PIMCServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def SetReset(self, request, context):
        """*
        @brief Issue reset in the firmware.

        This reset is given to the IP cores within the FPGA side.
        The cores need to be connected to PIMC rst out.
        Some cores will go in an async state to its userspace/kernel driver
        if the reset is issued. Thus not working as expected.

        @param Empty
        @return Empty
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetBusy(self, request, context):
        """*
        @brief Read if system is busy.

        @param Empty
        @return Bool
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetReady(self, request, context):
        """*
        @brief Read if the system is fully initialized and ready to be operated.

        @param Empty
        @return Bool
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def SetSWReady(self, request, context):
        """*
        @brief Set the software ready flag of the platform.

        @param Empty
        @return Empty
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetSWReady(self, request, context):
        """*
        @brief Read the software ready flag from the platform.

        @param Empty
        @return Bool
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def SetResetDone(self, request, context):
        """*
        @brief Set the reset done flag of the platform.

        @param Empty
        @return Empty
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetResetDone(self, request, context):
        """*
        @brief Read the reset done flag from the platform.

        @param Empty
        @return Bool
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetChipVersion(self, request, context):
        """*
        @brief Returns Chip version of PIMC core.

        The ID Should be 0xFFFF, the version is iterated
        if major things are changed.

        @param Empty
        @return UInt
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetModuleChipVersion(self, request, context):
        """*
        @brief Returns version of the core module from the platform.

        @param Empty
        @return UInt
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetInfo(self, request, context):
        """*
        @brief Returns struct containing pimcID, pimcVersion, projectID,
        platformID, buildRevision and buildTime.

        @param Empty
        @return Info
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetInfoString(self, request, context):
        """*
        @brief Returns all Info data.

        @param Empty
        @return String
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetAllClocksValid(self, request, context):
        """*
        @brief Returns true if all clocks are in valid frequency range.

        @param Empty
        @return Bool
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetClocksInfo(self, request, context):
        """*
        @brief Returns String containing information about connected clocks.

        @param Empty
        @return String
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetStatusInputs(self, request, context):
        """*
        @brief Returns String representing 16bit StatusInputs.

        @param Empty
        @return String
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetReadyMask(self, request, context):
        """*
        @brief Returns String representing 16bit ReadyMask.

        @param Empty
        @return String
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetReadyState(self, request, context):
        """*
        @brief Returns String representing 16bit ReadyState.

        @param Empty
        @return String
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetStatus(self, request, context):
        """*
        @brief Returns the status of the platform.

        The user can check if the platform is ready by reading the flag.
        The ready state is defined within the PIMC core.

        @param Empty
        @return PIMCStatus
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetProject(self, request, context):
        """*
        @brief \deprecated Returns Project containing projectId, platformId and
        buildRevision.

        With this function one can test if the correct/expected
        FPGA firmware is running on the device. Using the device
        with a different image will cause unexpected behavior or even
        damage the board.

        @param Empty
        @return Project
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetBuildTime(self, request, context):
        """*
        @brief \deprecated Returns buildTime in string format.

        The returned build time tells when the synthesis was started.
        This is only related to the FPGA firmware.

        @param Empty
        @return string
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetBoardInfo(self, request, context):
        """*
        @brief \deprecated Returns BoardInfo containing coreId, the Project and
        BuildTime.

        @param Empty
        @return BoardInfo
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_PIMCServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "SetReset": grpc.unary_unary_rpc_method_handler(
            servicer.SetReset,
            request_deserializer=pimc__pb2.Empty.FromString,
            response_serializer=pimc__pb2.Empty.SerializeToString,
        ),
        "GetBusy": grpc.unary_unary_rpc_method_handler(
            servicer.GetBusy,
            request_deserializer=pimc__pb2.Empty.FromString,
            response_serializer=pimc__pb2.Bool.SerializeToString,
        ),
        "GetReady": grpc.unary_unary_rpc_method_handler(
            servicer.GetReady,
            request_deserializer=pimc__pb2.Empty.FromString,
            response_serializer=pimc__pb2.Bool.SerializeToString,
        ),
        "SetSWReady": grpc.unary_unary_rpc_method_handler(
            servicer.SetSWReady,
            request_deserializer=pimc__pb2.Empty.FromString,
            response_serializer=pimc__pb2.Empty.SerializeToString,
        ),
        "GetSWReady": grpc.unary_unary_rpc_method_handler(
            servicer.GetSWReady,
            request_deserializer=pimc__pb2.Empty.FromString,
            response_serializer=pimc__pb2.Bool.SerializeToString,
        ),
        "SetResetDone": grpc.unary_unary_rpc_method_handler(
            servicer.SetResetDone,
            request_deserializer=pimc__pb2.Empty.FromString,
            response_serializer=pimc__pb2.Empty.SerializeToString,
        ),
        "GetResetDone": grpc.unary_unary_rpc_method_handler(
            servicer.GetResetDone,
            request_deserializer=pimc__pb2.Empty.FromString,
            response_serializer=pimc__pb2.Bool.SerializeToString,
        ),
        "GetChipVersion": grpc.unary_unary_rpc_method_handler(
            servicer.GetChipVersion,
            request_deserializer=pimc__pb2.Empty.FromString,
            response_serializer=pimc__pb2.UInt.SerializeToString,
        ),
        "GetModuleChipVersion": grpc.unary_unary_rpc_method_handler(
            servicer.GetModuleChipVersion,
            request_deserializer=pimc__pb2.Empty.FromString,
            response_serializer=pimc__pb2.UInt.SerializeToString,
        ),
        "GetInfo": grpc.unary_unary_rpc_method_handler(
            servicer.GetInfo,
            request_deserializer=pimc__pb2.Empty.FromString,
            response_serializer=pimc__pb2.Info.SerializeToString,
        ),
        "GetInfoString": grpc.unary_unary_rpc_method_handler(
            servicer.GetInfoString,
            request_deserializer=pimc__pb2.Empty.FromString,
            response_serializer=pimc__pb2.String.SerializeToString,
        ),
        "GetAllClocksValid": grpc.unary_unary_rpc_method_handler(
            servicer.GetAllClocksValid,
            request_deserializer=pimc__pb2.Empty.FromString,
            response_serializer=pimc__pb2.Bool.SerializeToString,
        ),
        "GetClocksInfo": grpc.unary_unary_rpc_method_handler(
            servicer.GetClocksInfo,
            request_deserializer=pimc__pb2.Empty.FromString,
            response_serializer=pimc__pb2.String.SerializeToString,
        ),
        "GetStatusInputs": grpc.unary_unary_rpc_method_handler(
            servicer.GetStatusInputs,
            request_deserializer=pimc__pb2.Empty.FromString,
            response_serializer=pimc__pb2.String.SerializeToString,
        ),
        "GetReadyMask": grpc.unary_unary_rpc_method_handler(
            servicer.GetReadyMask,
            request_deserializer=pimc__pb2.Empty.FromString,
            response_serializer=pimc__pb2.String.SerializeToString,
        ),
        "GetReadyState": grpc.unary_unary_rpc_method_handler(
            servicer.GetReadyState,
            request_deserializer=pimc__pb2.Empty.FromString,
            response_serializer=pimc__pb2.String.SerializeToString,
        ),
        "GetStatus": grpc.unary_unary_rpc_method_handler(
            servicer.GetStatus,
            request_deserializer=pimc__pb2.Empty.FromString,
            response_serializer=pimc__pb2.PIMCStatus.SerializeToString,
        ),
        "GetProject": grpc.unary_unary_rpc_method_handler(
            servicer.GetProject,
            request_deserializer=pimc__pb2.Empty.FromString,
            response_serializer=pimc__pb2.Project.SerializeToString,
        ),
        "GetBuildTime": grpc.unary_unary_rpc_method_handler(
            servicer.GetBuildTime,
            request_deserializer=pimc__pb2.Empty.FromString,
            response_serializer=pimc__pb2.String.SerializeToString,
        ),
        "GetBoardInfo": grpc.unary_unary_rpc_method_handler(
            servicer.GetBoardInfo,
            request_deserializer=pimc__pb2.Empty.FromString,
            response_serializer=pimc__pb2.BoardInfo.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        "pimc.PIMCService", rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))


# This class is part of an EXPERIMENTAL API.
class PIMCService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def SetReset(
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
            "/pimc.PIMCService/SetReset",
            pimc__pb2.Empty.SerializeToString,
            pimc__pb2.Empty.FromString,
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
    def GetBusy(
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
            "/pimc.PIMCService/GetBusy",
            pimc__pb2.Empty.SerializeToString,
            pimc__pb2.Bool.FromString,
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
    def GetReady(
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
            "/pimc.PIMCService/GetReady",
            pimc__pb2.Empty.SerializeToString,
            pimc__pb2.Bool.FromString,
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
    def SetSWReady(
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
            "/pimc.PIMCService/SetSWReady",
            pimc__pb2.Empty.SerializeToString,
            pimc__pb2.Empty.FromString,
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
    def GetSWReady(
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
            "/pimc.PIMCService/GetSWReady",
            pimc__pb2.Empty.SerializeToString,
            pimc__pb2.Bool.FromString,
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
    def SetResetDone(
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
            "/pimc.PIMCService/SetResetDone",
            pimc__pb2.Empty.SerializeToString,
            pimc__pb2.Empty.FromString,
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
    def GetResetDone(
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
            "/pimc.PIMCService/GetResetDone",
            pimc__pb2.Empty.SerializeToString,
            pimc__pb2.Bool.FromString,
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
    def GetChipVersion(
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
            "/pimc.PIMCService/GetChipVersion",
            pimc__pb2.Empty.SerializeToString,
            pimc__pb2.UInt.FromString,
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
    def GetModuleChipVersion(
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
            "/pimc.PIMCService/GetModuleChipVersion",
            pimc__pb2.Empty.SerializeToString,
            pimc__pb2.UInt.FromString,
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
    def GetInfo(
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
            "/pimc.PIMCService/GetInfo",
            pimc__pb2.Empty.SerializeToString,
            pimc__pb2.Info.FromString,
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
    def GetInfoString(
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
            "/pimc.PIMCService/GetInfoString",
            pimc__pb2.Empty.SerializeToString,
            pimc__pb2.String.FromString,
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
    def GetAllClocksValid(
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
            "/pimc.PIMCService/GetAllClocksValid",
            pimc__pb2.Empty.SerializeToString,
            pimc__pb2.Bool.FromString,
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
    def GetClocksInfo(
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
            "/pimc.PIMCService/GetClocksInfo",
            pimc__pb2.Empty.SerializeToString,
            pimc__pb2.String.FromString,
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
    def GetStatusInputs(
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
            "/pimc.PIMCService/GetStatusInputs",
            pimc__pb2.Empty.SerializeToString,
            pimc__pb2.String.FromString,
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
    def GetReadyMask(
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
            "/pimc.PIMCService/GetReadyMask",
            pimc__pb2.Empty.SerializeToString,
            pimc__pb2.String.FromString,
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
    def GetReadyState(
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
            "/pimc.PIMCService/GetReadyState",
            pimc__pb2.Empty.SerializeToString,
            pimc__pb2.String.FromString,
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
    def GetStatus(
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
            "/pimc.PIMCService/GetStatus",
            pimc__pb2.Empty.SerializeToString,
            pimc__pb2.PIMCStatus.FromString,
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
    def GetProject(
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
            "/pimc.PIMCService/GetProject",
            pimc__pb2.Empty.SerializeToString,
            pimc__pb2.Project.FromString,
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
    def GetBuildTime(
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
            "/pimc.PIMCService/GetBuildTime",
            pimc__pb2.Empty.SerializeToString,
            pimc__pb2.String.FromString,
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
    def GetBoardInfo(
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
            "/pimc.PIMCService/GetBoardInfo",
            pimc__pb2.Empty.SerializeToString,
            pimc__pb2.BoardInfo.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )
