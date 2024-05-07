# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import qiclib.packages.grpc.datatypes_pb2 as datatypes__pb2
import qiclib.packages.grpc.digital_trigger_pb2 as digital__trigger__pb2


class DigitalTriggerServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Reset = channel.unary_unary(
            "/digital_trigger.DigitalTriggerService/Reset",
            request_serializer=datatypes__pb2.EndpointIndex.SerializeToString,
            response_deserializer=datatypes__pb2.Empty.FromString,
        )
        self.SetTriggerSet = channel.unary_unary(
            "/digital_trigger.DigitalTriggerService/SetTriggerSet",
            request_serializer=digital__trigger__pb2.IndexedTriggerSet.SerializeToString,
            response_deserializer=datatypes__pb2.Empty.FromString,
        )
        self.GetTriggerSet = channel.unary_unary(
            "/digital_trigger.DigitalTriggerService/GetTriggerSet",
            request_serializer=digital__trigger__pb2.TriggerIndex.SerializeToString,
            response_deserializer=digital__trigger__pb2.TriggerSet.FromString,
        )
        self.ClearTriggerSets = channel.unary_unary(
            "/digital_trigger.DigitalTriggerService/ClearTriggerSets",
            request_serializer=datatypes__pb2.EndpointIndex.SerializeToString,
            response_deserializer=datatypes__pb2.Empty.FromString,
        )
        self.SetOutputConfig = channel.unary_unary(
            "/digital_trigger.DigitalTriggerService/SetOutputConfig",
            request_serializer=digital__trigger__pb2.IndexedOutputConfig.SerializeToString,
            response_deserializer=datatypes__pb2.Empty.FromString,
        )
        self.GetOutputConfig = channel.unary_unary(
            "/digital_trigger.DigitalTriggerService/GetOutputConfig",
            request_serializer=digital__trigger__pb2.OutputIndex.SerializeToString,
            response_deserializer=digital__trigger__pb2.OutputConfig.FromString,
        )
        self.Trigger = channel.unary_unary(
            "/digital_trigger.DigitalTriggerService/Trigger",
            request_serializer=digital__trigger__pb2.TriggerIndex.SerializeToString,
            response_deserializer=datatypes__pb2.Empty.FromString,
        )


class DigitalTriggerServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Reset(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def SetTriggerSet(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetTriggerSet(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def ClearTriggerSets(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def SetOutputConfig(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetOutputConfig(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def Trigger(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_DigitalTriggerServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "Reset": grpc.unary_unary_rpc_method_handler(
            servicer.Reset,
            request_deserializer=datatypes__pb2.EndpointIndex.FromString,
            response_serializer=datatypes__pb2.Empty.SerializeToString,
        ),
        "SetTriggerSet": grpc.unary_unary_rpc_method_handler(
            servicer.SetTriggerSet,
            request_deserializer=digital__trigger__pb2.IndexedTriggerSet.FromString,
            response_serializer=datatypes__pb2.Empty.SerializeToString,
        ),
        "GetTriggerSet": grpc.unary_unary_rpc_method_handler(
            servicer.GetTriggerSet,
            request_deserializer=digital__trigger__pb2.TriggerIndex.FromString,
            response_serializer=digital__trigger__pb2.TriggerSet.SerializeToString,
        ),
        "ClearTriggerSets": grpc.unary_unary_rpc_method_handler(
            servicer.ClearTriggerSets,
            request_deserializer=datatypes__pb2.EndpointIndex.FromString,
            response_serializer=datatypes__pb2.Empty.SerializeToString,
        ),
        "SetOutputConfig": grpc.unary_unary_rpc_method_handler(
            servicer.SetOutputConfig,
            request_deserializer=digital__trigger__pb2.IndexedOutputConfig.FromString,
            response_serializer=datatypes__pb2.Empty.SerializeToString,
        ),
        "GetOutputConfig": grpc.unary_unary_rpc_method_handler(
            servicer.GetOutputConfig,
            request_deserializer=digital__trigger__pb2.OutputIndex.FromString,
            response_serializer=digital__trigger__pb2.OutputConfig.SerializeToString,
        ),
        "Trigger": grpc.unary_unary_rpc_method_handler(
            servicer.Trigger,
            request_deserializer=digital__trigger__pb2.TriggerIndex.FromString,
            response_serializer=datatypes__pb2.Empty.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        "digital_trigger.DigitalTriggerService", rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))


# This class is part of an EXPERIMENTAL API.
class DigitalTriggerService(object):
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
            "/digital_trigger.DigitalTriggerService/Reset",
            datatypes__pb2.EndpointIndex.SerializeToString,
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
    def SetTriggerSet(
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
            "/digital_trigger.DigitalTriggerService/SetTriggerSet",
            digital__trigger__pb2.IndexedTriggerSet.SerializeToString,
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
    def GetTriggerSet(
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
            "/digital_trigger.DigitalTriggerService/GetTriggerSet",
            digital__trigger__pb2.TriggerIndex.SerializeToString,
            digital__trigger__pb2.TriggerSet.FromString,
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
    def ClearTriggerSets(
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
            "/digital_trigger.DigitalTriggerService/ClearTriggerSets",
            datatypes__pb2.EndpointIndex.SerializeToString,
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
    def SetOutputConfig(
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
            "/digital_trigger.DigitalTriggerService/SetOutputConfig",
            digital__trigger__pb2.IndexedOutputConfig.SerializeToString,
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
    def GetOutputConfig(
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
            "/digital_trigger.DigitalTriggerService/GetOutputConfig",
            digital__trigger__pb2.OutputIndex.SerializeToString,
            digital__trigger__pb2.OutputConfig.FromString,
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
    def Trigger(
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
            "/digital_trigger.DigitalTriggerService/Trigger",
            digital__trigger__pb2.TriggerIndex.SerializeToString,
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
