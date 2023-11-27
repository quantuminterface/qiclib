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

from . import sequencer_pb2 as sequencer__pb2


class SequencerServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetBusy = channel.unary_unary(
            "/sequencer.SequencerService/GetBusy",
            request_serializer=sequencer__pb2.EndpointIndex.SerializeToString,
            response_deserializer=sequencer__pb2.Bool.FromString,
        )
        self.GetRelaxed = channel.unary_unary(
            "/sequencer.SequencerService/GetRelaxed",
            request_serializer=sequencer__pb2.EndpointIndex.SerializeToString,
            response_deserializer=sequencer__pb2.Bool.FromString,
        )
        self.GetAverages = channel.unary_unary(
            "/sequencer.SequencerService/GetAverages",
            request_serializer=sequencer__pb2.EndpointIndex.SerializeToString,
            response_deserializer=sequencer__pb2.Average.FromString,
        )
        self.SetAverages = channel.unary_unary(
            "/sequencer.SequencerService/SetAverages",
            request_serializer=sequencer__pb2.Average.SerializeToString,
            response_deserializer=sequencer__pb2.Empty.FromString,
        )
        self.GetProgramCounter = channel.unary_unary(
            "/sequencer.SequencerService/GetProgramCounter",
            request_serializer=sequencer__pb2.EndpointIndex.SerializeToString,
            response_deserializer=sequencer__pb2.ProgramCounter.FromString,
        )
        self.GetRegister = channel.unary_unary(
            "/sequencer.SequencerService/GetRegister",
            request_serializer=sequencer__pb2.RegisterIndex.SerializeToString,
            response_deserializer=sequencer__pb2.Register.FromString,
        )
        self.SetRegister = channel.unary_unary(
            "/sequencer.SequencerService/SetRegister",
            request_serializer=sequencer__pb2.Register.SerializeToString,
            response_deserializer=sequencer__pb2.Empty.FromString,
        )
        self.GetAllRegisters = channel.unary_unary(
            "/sequencer.SequencerService/GetAllRegisters",
            request_serializer=sequencer__pb2.EndpointIndex.SerializeToString,
            response_deserializer=sequencer__pb2.RegisterList.FromString,
        )
        self.SetDelay = channel.unary_unary(
            "/sequencer.SequencerService/SetDelay",
            request_serializer=sequencer__pb2.Delay.SerializeToString,
            response_deserializer=sequencer__pb2.Empty.FromString,
        )
        self.LoadProgram = channel.unary_unary(
            "/sequencer.SequencerService/LoadProgram",
            request_serializer=sequencer__pb2.Program.SerializeToString,
            response_deserializer=sequencer__pb2.Empty.FromString,
        )
        self.StartAt = channel.unary_unary(
            "/sequencer.SequencerService/StartAt",
            request_serializer=sequencer__pb2.ProgramCounter.SerializeToString,
            response_deserializer=sequencer__pb2.Empty.FromString,
        )
        self.GetStartAddress = channel.unary_unary(
            "/sequencer.SequencerService/GetStartAddress",
            request_serializer=sequencer__pb2.EndpointIndex.SerializeToString,
            response_deserializer=sequencer__pb2.ProgramCounter.FromString,
        )
        self.SetStartAddress = channel.unary_unary(
            "/sequencer.SequencerService/SetStartAddress",
            request_serializer=sequencer__pb2.ProgramCounter.SerializeToString,
            response_deserializer=sequencer__pb2.Empty.FromString,
        )
        self.Resume = channel.unary_unary(
            "/sequencer.SequencerService/Resume",
            request_serializer=sequencer__pb2.EndpointIndex.SerializeToString,
            response_deserializer=sequencer__pb2.Empty.FromString,
        )
        self.Reset = channel.unary_unary(
            "/sequencer.SequencerService/Reset",
            request_serializer=sequencer__pb2.EndpointIndex.SerializeToString,
            response_deserializer=sequencer__pb2.Empty.FromString,
        )
        self.Stop = channel.unary_unary(
            "/sequencer.SequencerService/Stop",
            request_serializer=sequencer__pb2.EndpointIndex.SerializeToString,
            response_deserializer=sequencer__pb2.Empty.FromString,
        )
        self.ReportStatus = channel.unary_unary(
            "/sequencer.SequencerService/ReportStatus",
            request_serializer=sequencer__pb2.EndpointIndex.SerializeToString,
            response_deserializer=sequencer__pb2.StatusReport.FromString,
        )


class SequencerServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def GetBusy(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetRelaxed(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetAverages(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def SetAverages(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetProgramCounter(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetRegister(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def SetRegister(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetAllRegisters(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def SetDelay(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def LoadProgram(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def StartAt(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetStartAddress(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def SetStartAddress(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def Resume(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def Reset(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def Stop(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def ReportStatus(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_SequencerServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "GetBusy": grpc.unary_unary_rpc_method_handler(
            servicer.GetBusy,
            request_deserializer=sequencer__pb2.EndpointIndex.FromString,
            response_serializer=sequencer__pb2.Bool.SerializeToString,
        ),
        "GetRelaxed": grpc.unary_unary_rpc_method_handler(
            servicer.GetRelaxed,
            request_deserializer=sequencer__pb2.EndpointIndex.FromString,
            response_serializer=sequencer__pb2.Bool.SerializeToString,
        ),
        "GetAverages": grpc.unary_unary_rpc_method_handler(
            servicer.GetAverages,
            request_deserializer=sequencer__pb2.EndpointIndex.FromString,
            response_serializer=sequencer__pb2.Average.SerializeToString,
        ),
        "SetAverages": grpc.unary_unary_rpc_method_handler(
            servicer.SetAverages,
            request_deserializer=sequencer__pb2.Average.FromString,
            response_serializer=sequencer__pb2.Empty.SerializeToString,
        ),
        "GetProgramCounter": grpc.unary_unary_rpc_method_handler(
            servicer.GetProgramCounter,
            request_deserializer=sequencer__pb2.EndpointIndex.FromString,
            response_serializer=sequencer__pb2.ProgramCounter.SerializeToString,
        ),
        "GetRegister": grpc.unary_unary_rpc_method_handler(
            servicer.GetRegister,
            request_deserializer=sequencer__pb2.RegisterIndex.FromString,
            response_serializer=sequencer__pb2.Register.SerializeToString,
        ),
        "SetRegister": grpc.unary_unary_rpc_method_handler(
            servicer.SetRegister,
            request_deserializer=sequencer__pb2.Register.FromString,
            response_serializer=sequencer__pb2.Empty.SerializeToString,
        ),
        "GetAllRegisters": grpc.unary_unary_rpc_method_handler(
            servicer.GetAllRegisters,
            request_deserializer=sequencer__pb2.EndpointIndex.FromString,
            response_serializer=sequencer__pb2.RegisterList.SerializeToString,
        ),
        "SetDelay": grpc.unary_unary_rpc_method_handler(
            servicer.SetDelay,
            request_deserializer=sequencer__pb2.Delay.FromString,
            response_serializer=sequencer__pb2.Empty.SerializeToString,
        ),
        "LoadProgram": grpc.unary_unary_rpc_method_handler(
            servicer.LoadProgram,
            request_deserializer=sequencer__pb2.Program.FromString,
            response_serializer=sequencer__pb2.Empty.SerializeToString,
        ),
        "StartAt": grpc.unary_unary_rpc_method_handler(
            servicer.StartAt,
            request_deserializer=sequencer__pb2.ProgramCounter.FromString,
            response_serializer=sequencer__pb2.Empty.SerializeToString,
        ),
        "GetStartAddress": grpc.unary_unary_rpc_method_handler(
            servicer.GetStartAddress,
            request_deserializer=sequencer__pb2.EndpointIndex.FromString,
            response_serializer=sequencer__pb2.ProgramCounter.SerializeToString,
        ),
        "SetStartAddress": grpc.unary_unary_rpc_method_handler(
            servicer.SetStartAddress,
            request_deserializer=sequencer__pb2.ProgramCounter.FromString,
            response_serializer=sequencer__pb2.Empty.SerializeToString,
        ),
        "Resume": grpc.unary_unary_rpc_method_handler(
            servicer.Resume,
            request_deserializer=sequencer__pb2.EndpointIndex.FromString,
            response_serializer=sequencer__pb2.Empty.SerializeToString,
        ),
        "Reset": grpc.unary_unary_rpc_method_handler(
            servicer.Reset,
            request_deserializer=sequencer__pb2.EndpointIndex.FromString,
            response_serializer=sequencer__pb2.Empty.SerializeToString,
        ),
        "Stop": grpc.unary_unary_rpc_method_handler(
            servicer.Stop,
            request_deserializer=sequencer__pb2.EndpointIndex.FromString,
            response_serializer=sequencer__pb2.Empty.SerializeToString,
        ),
        "ReportStatus": grpc.unary_unary_rpc_method_handler(
            servicer.ReportStatus,
            request_deserializer=sequencer__pb2.EndpointIndex.FromString,
            response_serializer=sequencer__pb2.StatusReport.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        "sequencer.SequencerService", rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))


# This class is part of an EXPERIMENTAL API.
class SequencerService(object):
    """Missing associated documentation comment in .proto file."""

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
            "/sequencer.SequencerService/GetBusy",
            sequencer__pb2.EndpointIndex.SerializeToString,
            sequencer__pb2.Bool.FromString,
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
    def GetRelaxed(
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
            "/sequencer.SequencerService/GetRelaxed",
            sequencer__pb2.EndpointIndex.SerializeToString,
            sequencer__pb2.Bool.FromString,
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
    def GetAverages(
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
            "/sequencer.SequencerService/GetAverages",
            sequencer__pb2.EndpointIndex.SerializeToString,
            sequencer__pb2.Average.FromString,
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
    def SetAverages(
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
            "/sequencer.SequencerService/SetAverages",
            sequencer__pb2.Average.SerializeToString,
            sequencer__pb2.Empty.FromString,
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
    def GetProgramCounter(
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
            "/sequencer.SequencerService/GetProgramCounter",
            sequencer__pb2.EndpointIndex.SerializeToString,
            sequencer__pb2.ProgramCounter.FromString,
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
    def GetRegister(
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
            "/sequencer.SequencerService/GetRegister",
            sequencer__pb2.RegisterIndex.SerializeToString,
            sequencer__pb2.Register.FromString,
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
    def SetRegister(
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
            "/sequencer.SequencerService/SetRegister",
            sequencer__pb2.Register.SerializeToString,
            sequencer__pb2.Empty.FromString,
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
    def GetAllRegisters(
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
            "/sequencer.SequencerService/GetAllRegisters",
            sequencer__pb2.EndpointIndex.SerializeToString,
            sequencer__pb2.RegisterList.FromString,
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
    def SetDelay(
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
            "/sequencer.SequencerService/SetDelay",
            sequencer__pb2.Delay.SerializeToString,
            sequencer__pb2.Empty.FromString,
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
    def LoadProgram(
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
            "/sequencer.SequencerService/LoadProgram",
            sequencer__pb2.Program.SerializeToString,
            sequencer__pb2.Empty.FromString,
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
    def StartAt(
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
            "/sequencer.SequencerService/StartAt",
            sequencer__pb2.ProgramCounter.SerializeToString,
            sequencer__pb2.Empty.FromString,
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
    def GetStartAddress(
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
            "/sequencer.SequencerService/GetStartAddress",
            sequencer__pb2.EndpointIndex.SerializeToString,
            sequencer__pb2.ProgramCounter.FromString,
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
    def SetStartAddress(
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
            "/sequencer.SequencerService/SetStartAddress",
            sequencer__pb2.ProgramCounter.SerializeToString,
            sequencer__pb2.Empty.FromString,
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
    def Resume(
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
            "/sequencer.SequencerService/Resume",
            sequencer__pb2.EndpointIndex.SerializeToString,
            sequencer__pb2.Empty.FromString,
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
            "/sequencer.SequencerService/Reset",
            sequencer__pb2.EndpointIndex.SerializeToString,
            sequencer__pb2.Empty.FromString,
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
    def Stop(
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
            "/sequencer.SequencerService/Stop",
            sequencer__pb2.EndpointIndex.SerializeToString,
            sequencer__pb2.Empty.FromString,
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
    def ReportStatus(
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
            "/sequencer.SequencerService/ReportStatus",
            sequencer__pb2.EndpointIndex.SerializeToString,
            sequencer__pb2.StatusReport.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )
