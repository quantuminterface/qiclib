# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import qiclib.packages.grpc.datatypes_pb2 as datatypes__pb2
import qiclib.packages.grpc.taskrunner_pb2 as taskrunner__pb2


class TaskRunnerServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetStatus = channel.unary_unary(
            "/taskrunner.TaskRunnerService/GetStatus",
            request_serializer=datatypes__pb2.Empty.SerializeToString,
            response_deserializer=taskrunner__pb2.StatusReply.FromString,
        )
        self.GetTaskState = channel.unary_unary(
            "/taskrunner.TaskRunnerService/GetTaskState",
            request_serializer=datatypes__pb2.Empty.SerializeToString,
            response_deserializer=taskrunner__pb2.TaskStateReply.FromString,
        )
        self.SetParameter = channel.unary_unary(
            "/taskrunner.TaskRunnerService/SetParameter",
            request_serializer=taskrunner__pb2.ParameterRequest.SerializeToString,
            response_deserializer=datatypes__pb2.Empty.FromString,
        )
        self.ProgramTask = channel.unary_unary(
            "/taskrunner.TaskRunnerService/ProgramTask",
            request_serializer=taskrunner__pb2.ProgramTaskRequest.SerializeToString,
            response_deserializer=datatypes__pb2.Empty.FromString,
        )
        self.CompileTask = channel.unary_unary(
            "/taskrunner.TaskRunnerService/CompileTask",
            request_serializer=taskrunner__pb2.ProgramTaskRequest.SerializeToString,
            response_deserializer=datatypes__pb2.Empty.FromString,
        )
        self.StartTask = channel.unary_unary(
            "/taskrunner.TaskRunnerService/StartTask",
            request_serializer=taskrunner__pb2.StartTaskRequest.SerializeToString,
            response_deserializer=datatypes__pb2.Empty.FromString,
        )
        self.StopTask = channel.unary_unary(
            "/taskrunner.TaskRunnerService/StopTask",
            request_serializer=taskrunner__pb2.StopTaskRequest.SerializeToString,
            response_deserializer=datatypes__pb2.Empty.FromString,
        )
        self.GetDataboxes = channel.unary_stream(
            "/taskrunner.TaskRunnerService/GetDataboxes",
            request_serializer=datatypes__pb2.Empty.SerializeToString,
            response_deserializer=taskrunner__pb2.DataboxReplyINT32.FromString,
        )
        self.GetDataboxesINT8 = channel.unary_stream(
            "/taskrunner.TaskRunnerService/GetDataboxesINT8",
            request_serializer=datatypes__pb2.Empty.SerializeToString,
            response_deserializer=taskrunner__pb2.DataboxReplyINT32.FromString,
        )
        self.GetDataboxesUINT8 = channel.unary_stream(
            "/taskrunner.TaskRunnerService/GetDataboxesUINT8",
            request_serializer=datatypes__pb2.Empty.SerializeToString,
            response_deserializer=taskrunner__pb2.DataboxReplyUINT32.FromString,
        )
        self.GetDataboxesINT16 = channel.unary_stream(
            "/taskrunner.TaskRunnerService/GetDataboxesINT16",
            request_serializer=datatypes__pb2.Empty.SerializeToString,
            response_deserializer=taskrunner__pb2.DataboxReplyINT32.FromString,
        )
        self.GetDataboxesUINT16 = channel.unary_stream(
            "/taskrunner.TaskRunnerService/GetDataboxesUINT16",
            request_serializer=datatypes__pb2.Empty.SerializeToString,
            response_deserializer=taskrunner__pb2.DataboxReplyUINT32.FromString,
        )
        self.GetDataboxesINT32 = channel.unary_stream(
            "/taskrunner.TaskRunnerService/GetDataboxesINT32",
            request_serializer=datatypes__pb2.Empty.SerializeToString,
            response_deserializer=taskrunner__pb2.DataboxReplyINT32.FromString,
        )
        self.GetDataboxesUINT32 = channel.unary_stream(
            "/taskrunner.TaskRunnerService/GetDataboxesUINT32",
            request_serializer=datatypes__pb2.Empty.SerializeToString,
            response_deserializer=taskrunner__pb2.DataboxReplyUINT32.FromString,
        )
        self.GetDataboxesINT64 = channel.unary_stream(
            "/taskrunner.TaskRunnerService/GetDataboxesINT64",
            request_serializer=datatypes__pb2.Empty.SerializeToString,
            response_deserializer=taskrunner__pb2.DataboxReplyINT64.FromString,
        )
        self.GetDataboxesUINT64 = channel.unary_stream(
            "/taskrunner.TaskRunnerService/GetDataboxesUINT64",
            request_serializer=datatypes__pb2.Empty.SerializeToString,
            response_deserializer=taskrunner__pb2.DataboxReplyUINT64.FromString,
        )
        self.GetTaskErrorMessages = channel.unary_unary(
            "/taskrunner.TaskRunnerService/GetTaskErrorMessages",
            request_serializer=datatypes__pb2.Empty.SerializeToString,
            response_deserializer=taskrunner__pb2.GetTaskErrorMessagesReply.FromString,
        )


class TaskRunnerServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def GetStatus(self, request, context):
        """Sends a greeting"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetTaskState(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def SetParameter(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def ProgramTask(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def CompileTask(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def StartTask(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def StopTask(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetDataboxes(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetDataboxesINT8(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetDataboxesUINT8(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetDataboxesINT16(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetDataboxesUINT16(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetDataboxesINT32(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetDataboxesUINT32(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetDataboxesINT64(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetDataboxesUINT64(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetTaskErrorMessages(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_TaskRunnerServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "GetStatus": grpc.unary_unary_rpc_method_handler(
            servicer.GetStatus,
            request_deserializer=datatypes__pb2.Empty.FromString,
            response_serializer=taskrunner__pb2.StatusReply.SerializeToString,
        ),
        "GetTaskState": grpc.unary_unary_rpc_method_handler(
            servicer.GetTaskState,
            request_deserializer=datatypes__pb2.Empty.FromString,
            response_serializer=taskrunner__pb2.TaskStateReply.SerializeToString,
        ),
        "SetParameter": grpc.unary_unary_rpc_method_handler(
            servicer.SetParameter,
            request_deserializer=taskrunner__pb2.ParameterRequest.FromString,
            response_serializer=datatypes__pb2.Empty.SerializeToString,
        ),
        "ProgramTask": grpc.unary_unary_rpc_method_handler(
            servicer.ProgramTask,
            request_deserializer=taskrunner__pb2.ProgramTaskRequest.FromString,
            response_serializer=datatypes__pb2.Empty.SerializeToString,
        ),
        "CompileTask": grpc.unary_unary_rpc_method_handler(
            servicer.CompileTask,
            request_deserializer=taskrunner__pb2.ProgramTaskRequest.FromString,
            response_serializer=datatypes__pb2.Empty.SerializeToString,
        ),
        "StartTask": grpc.unary_unary_rpc_method_handler(
            servicer.StartTask,
            request_deserializer=taskrunner__pb2.StartTaskRequest.FromString,
            response_serializer=datatypes__pb2.Empty.SerializeToString,
        ),
        "StopTask": grpc.unary_unary_rpc_method_handler(
            servicer.StopTask,
            request_deserializer=taskrunner__pb2.StopTaskRequest.FromString,
            response_serializer=datatypes__pb2.Empty.SerializeToString,
        ),
        "GetDataboxes": grpc.unary_stream_rpc_method_handler(
            servicer.GetDataboxes,
            request_deserializer=datatypes__pb2.Empty.FromString,
            response_serializer=taskrunner__pb2.DataboxReplyINT32.SerializeToString,
        ),
        "GetDataboxesINT8": grpc.unary_stream_rpc_method_handler(
            servicer.GetDataboxesINT8,
            request_deserializer=datatypes__pb2.Empty.FromString,
            response_serializer=taskrunner__pb2.DataboxReplyINT32.SerializeToString,
        ),
        "GetDataboxesUINT8": grpc.unary_stream_rpc_method_handler(
            servicer.GetDataboxesUINT8,
            request_deserializer=datatypes__pb2.Empty.FromString,
            response_serializer=taskrunner__pb2.DataboxReplyUINT32.SerializeToString,
        ),
        "GetDataboxesINT16": grpc.unary_stream_rpc_method_handler(
            servicer.GetDataboxesINT16,
            request_deserializer=datatypes__pb2.Empty.FromString,
            response_serializer=taskrunner__pb2.DataboxReplyINT32.SerializeToString,
        ),
        "GetDataboxesUINT16": grpc.unary_stream_rpc_method_handler(
            servicer.GetDataboxesUINT16,
            request_deserializer=datatypes__pb2.Empty.FromString,
            response_serializer=taskrunner__pb2.DataboxReplyUINT32.SerializeToString,
        ),
        "GetDataboxesINT32": grpc.unary_stream_rpc_method_handler(
            servicer.GetDataboxesINT32,
            request_deserializer=datatypes__pb2.Empty.FromString,
            response_serializer=taskrunner__pb2.DataboxReplyINT32.SerializeToString,
        ),
        "GetDataboxesUINT32": grpc.unary_stream_rpc_method_handler(
            servicer.GetDataboxesUINT32,
            request_deserializer=datatypes__pb2.Empty.FromString,
            response_serializer=taskrunner__pb2.DataboxReplyUINT32.SerializeToString,
        ),
        "GetDataboxesINT64": grpc.unary_stream_rpc_method_handler(
            servicer.GetDataboxesINT64,
            request_deserializer=datatypes__pb2.Empty.FromString,
            response_serializer=taskrunner__pb2.DataboxReplyINT64.SerializeToString,
        ),
        "GetDataboxesUINT64": grpc.unary_stream_rpc_method_handler(
            servicer.GetDataboxesUINT64,
            request_deserializer=datatypes__pb2.Empty.FromString,
            response_serializer=taskrunner__pb2.DataboxReplyUINT64.SerializeToString,
        ),
        "GetTaskErrorMessages": grpc.unary_unary_rpc_method_handler(
            servicer.GetTaskErrorMessages,
            request_deserializer=datatypes__pb2.Empty.FromString,
            response_serializer=taskrunner__pb2.GetTaskErrorMessagesReply.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        "taskrunner.TaskRunnerService", rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))


# This class is part of an EXPERIMENTAL API.
class TaskRunnerService(object):
    """Missing associated documentation comment in .proto file."""

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
            "/taskrunner.TaskRunnerService/GetStatus",
            datatypes__pb2.Empty.SerializeToString,
            taskrunner__pb2.StatusReply.FromString,
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
    def GetTaskState(
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
            "/taskrunner.TaskRunnerService/GetTaskState",
            datatypes__pb2.Empty.SerializeToString,
            taskrunner__pb2.TaskStateReply.FromString,
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
    def SetParameter(
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
            "/taskrunner.TaskRunnerService/SetParameter",
            taskrunner__pb2.ParameterRequest.SerializeToString,
            datatypes__pb2.Empty.FromString,
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
    def ProgramTask(
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
            "/taskrunner.TaskRunnerService/ProgramTask",
            taskrunner__pb2.ProgramTaskRequest.SerializeToString,
            datatypes__pb2.Empty.FromString,
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
    def CompileTask(
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
            "/taskrunner.TaskRunnerService/CompileTask",
            taskrunner__pb2.ProgramTaskRequest.SerializeToString,
            datatypes__pb2.Empty.FromString,
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
    def StartTask(
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
            "/taskrunner.TaskRunnerService/StartTask",
            taskrunner__pb2.StartTaskRequest.SerializeToString,
            datatypes__pb2.Empty.FromString,
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
    def StopTask(
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
            "/taskrunner.TaskRunnerService/StopTask",
            taskrunner__pb2.StopTaskRequest.SerializeToString,
            datatypes__pb2.Empty.FromString,
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
    def GetDataboxes(
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
        return grpc.experimental.unary_stream(
            request,
            target,
            "/taskrunner.TaskRunnerService/GetDataboxes",
            datatypes__pb2.Empty.SerializeToString,
            taskrunner__pb2.DataboxReplyINT32.FromString,
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
    def GetDataboxesINT8(
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
        return grpc.experimental.unary_stream(
            request,
            target,
            "/taskrunner.TaskRunnerService/GetDataboxesINT8",
            datatypes__pb2.Empty.SerializeToString,
            taskrunner__pb2.DataboxReplyINT32.FromString,
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
    def GetDataboxesUINT8(
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
        return grpc.experimental.unary_stream(
            request,
            target,
            "/taskrunner.TaskRunnerService/GetDataboxesUINT8",
            datatypes__pb2.Empty.SerializeToString,
            taskrunner__pb2.DataboxReplyUINT32.FromString,
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
    def GetDataboxesINT16(
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
        return grpc.experimental.unary_stream(
            request,
            target,
            "/taskrunner.TaskRunnerService/GetDataboxesINT16",
            datatypes__pb2.Empty.SerializeToString,
            taskrunner__pb2.DataboxReplyINT32.FromString,
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
    def GetDataboxesUINT16(
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
        return grpc.experimental.unary_stream(
            request,
            target,
            "/taskrunner.TaskRunnerService/GetDataboxesUINT16",
            datatypes__pb2.Empty.SerializeToString,
            taskrunner__pb2.DataboxReplyUINT32.FromString,
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
    def GetDataboxesINT32(
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
        return grpc.experimental.unary_stream(
            request,
            target,
            "/taskrunner.TaskRunnerService/GetDataboxesINT32",
            datatypes__pb2.Empty.SerializeToString,
            taskrunner__pb2.DataboxReplyINT32.FromString,
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
    def GetDataboxesUINT32(
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
        return grpc.experimental.unary_stream(
            request,
            target,
            "/taskrunner.TaskRunnerService/GetDataboxesUINT32",
            datatypes__pb2.Empty.SerializeToString,
            taskrunner__pb2.DataboxReplyUINT32.FromString,
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
    def GetDataboxesINT64(
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
        return grpc.experimental.unary_stream(
            request,
            target,
            "/taskrunner.TaskRunnerService/GetDataboxesINT64",
            datatypes__pb2.Empty.SerializeToString,
            taskrunner__pb2.DataboxReplyINT64.FromString,
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
    def GetDataboxesUINT64(
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
        return grpc.experimental.unary_stream(
            request,
            target,
            "/taskrunner.TaskRunnerService/GetDataboxesUINT64",
            datatypes__pb2.Empty.SerializeToString,
            taskrunner__pb2.DataboxReplyUINT64.FromString,
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
    def GetTaskErrorMessages(
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
            "/taskrunner.TaskRunnerService/GetTaskErrorMessages",
            datatypes__pb2.Empty.SerializeToString,
            taskrunner__pb2.GetTaskErrorMessagesReply.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )
