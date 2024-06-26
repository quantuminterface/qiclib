# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import qiclib.packages.grpc.balunatten_pb2 as balunatten__pb2
import qiclib.packages.grpc.datatypes_pb2 as datatypes__pb2


class BalUnAttenServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.SetAttenuation = channel.unary_unary(
            "/balunatten.BalUnAttenService/SetAttenuation",
            request_serializer=balunatten__pb2.Float.SerializeToString,
            response_deserializer=datatypes__pb2.Empty.FromString,
        )
        self.GetAttenuation = channel.unary_unary(
            "/balunatten.BalUnAttenService/GetAttenuation",
            request_serializer=balunatten__pb2.Channel.SerializeToString,
            response_deserializer=datatypes__pb2.Float.FromString,
        )
        self.SwitchOff = channel.unary_unary(
            "/balunatten.BalUnAttenService/SwitchOff",
            request_serializer=balunatten__pb2.Channel.SerializeToString,
            response_deserializer=datatypes__pb2.Empty.FromString,
        )
        self.SwitchNyquist = channel.unary_unary(
            "/balunatten.BalUnAttenService/SwitchNyquist",
            request_serializer=balunatten__pb2.Number.SerializeToString,
            response_deserializer=datatypes__pb2.Empty.FromString,
        )
        self.GetNyquist = channel.unary_unary(
            "/balunatten.BalUnAttenService/GetNyquist",
            request_serializer=balunatten__pb2.Channel.SerializeToString,
            response_deserializer=datatypes__pb2.UInt.FromString,
        )
        self.SwitchDC = channel.unary_unary(
            "/balunatten.BalUnAttenService/SwitchDC",
            request_serializer=balunatten__pb2.Channel.SerializeToString,
            response_deserializer=datatypes__pb2.Empty.FromString,
        )


class BalUnAttenServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def SetAttenuation(self, request, context):
        """*
        Sets the attenuation for DAC
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetAttenuation(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def SwitchOff(self, request, context):
        """*
        Switch the given channel off
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def SwitchNyquist(self, request, context):
        """*
        Switch the nyquist zone for the given channel
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetNyquist(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def SwitchDC(self, request, context):
        """*
        Switch a certain channel to DC
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_BalUnAttenServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "SetAttenuation": grpc.unary_unary_rpc_method_handler(
            servicer.SetAttenuation,
            request_deserializer=balunatten__pb2.Float.FromString,
            response_serializer=datatypes__pb2.Empty.SerializeToString,
        ),
        "GetAttenuation": grpc.unary_unary_rpc_method_handler(
            servicer.GetAttenuation,
            request_deserializer=balunatten__pb2.Channel.FromString,
            response_serializer=datatypes__pb2.Float.SerializeToString,
        ),
        "SwitchOff": grpc.unary_unary_rpc_method_handler(
            servicer.SwitchOff,
            request_deserializer=balunatten__pb2.Channel.FromString,
            response_serializer=datatypes__pb2.Empty.SerializeToString,
        ),
        "SwitchNyquist": grpc.unary_unary_rpc_method_handler(
            servicer.SwitchNyquist,
            request_deserializer=balunatten__pb2.Number.FromString,
            response_serializer=datatypes__pb2.Empty.SerializeToString,
        ),
        "GetNyquist": grpc.unary_unary_rpc_method_handler(
            servicer.GetNyquist,
            request_deserializer=balunatten__pb2.Channel.FromString,
            response_serializer=datatypes__pb2.UInt.SerializeToString,
        ),
        "SwitchDC": grpc.unary_unary_rpc_method_handler(
            servicer.SwitchDC,
            request_deserializer=balunatten__pb2.Channel.FromString,
            response_serializer=datatypes__pb2.Empty.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        "balunatten.BalUnAttenService", rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))


# This class is part of an EXPERIMENTAL API.
class BalUnAttenService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def SetAttenuation(
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
            "/balunatten.BalUnAttenService/SetAttenuation",
            balunatten__pb2.Float.SerializeToString,
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
    def GetAttenuation(
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
            "/balunatten.BalUnAttenService/GetAttenuation",
            balunatten__pb2.Channel.SerializeToString,
            datatypes__pb2.Float.FromString,
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
    def SwitchOff(
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
            "/balunatten.BalUnAttenService/SwitchOff",
            balunatten__pb2.Channel.SerializeToString,
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
    def SwitchNyquist(
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
            "/balunatten.BalUnAttenService/SwitchNyquist",
            balunatten__pb2.Number.SerializeToString,
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
    def GetNyquist(
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
            "/balunatten.BalUnAttenService/GetNyquist",
            balunatten__pb2.Channel.SerializeToString,
            datatypes__pb2.UInt.FromString,
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
    def SwitchDC(
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
            "/balunatten.BalUnAttenService/SwitchDC",
            balunatten__pb2.Channel.SerializeToString,
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
