# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import qiclib.packages.grpc.datatypes_pb2 as datatypes__pb2
import qiclib.packages.grpc.direct_rf_pb2 as direct__rf__pb2


class DirectRfServiceStub(object):
    """*
    The DirectRf service manages the entire input / output chain using
    the DirectRf frontend board.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.SetFrequency = channel.unary_unary(
            "/direct_rf.DirectRfService/SetFrequency",
            request_serializer=direct__rf__pb2.IndexedDouble.SerializeToString,
            response_deserializer=datatypes__pb2.Empty.FromString,
        )
        self.GetFrequency = channel.unary_unary(
            "/direct_rf.DirectRfService/GetFrequency",
            request_serializer=direct__rf__pb2.ConverterIndex.SerializeToString,
            response_deserializer=datatypes__pb2.Double.FromString,
        )
        self.SetPhase = channel.unary_unary(
            "/direct_rf.DirectRfService/SetPhase",
            request_serializer=direct__rf__pb2.IndexedDouble.SerializeToString,
            response_deserializer=datatypes__pb2.Empty.FromString,
        )
        self.GetPhase = channel.unary_unary(
            "/direct_rf.DirectRfService/GetPhase",
            request_serializer=direct__rf__pb2.ConverterIndex.SerializeToString,
            response_deserializer=datatypes__pb2.Double.FromString,
        )
        self.SetAttenuation = channel.unary_unary(
            "/direct_rf.DirectRfService/SetAttenuation",
            request_serializer=direct__rf__pb2.IndexedDouble.SerializeToString,
            response_deserializer=datatypes__pb2.Empty.FromString,
        )
        self.GetAttenuation = channel.unary_unary(
            "/direct_rf.DirectRfService/GetAttenuation",
            request_serializer=direct__rf__pb2.ConverterIndex.SerializeToString,
            response_deserializer=datatypes__pb2.Double.FromString,
        )
        self.ToRfdcIndex = channel.unary_unary(
            "/direct_rf.DirectRfService/ToRfdcIndex",
            request_serializer=direct__rf__pb2.ConverterIndex.SerializeToString,
            response_deserializer=direct__rf__pb2.RfDcIndex.FromString,
        )
        self.ToChannelIndex = channel.unary_unary(
            "/direct_rf.DirectRfService/ToChannelIndex",
            request_serializer=direct__rf__pb2.ConverterIndex.SerializeToString,
            response_deserializer=datatypes__pb2.UInt.FromString,
        )


class DirectRfServiceServicer(object):
    """*
    The DirectRf service manages the entire input / output chain using
    the DirectRf frontend board.
    """

    def SetFrequency(self, request, context):
        """*
        Set the frequency of the entire input or output chain.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetFrequency(self, request, context):
        """*
        Return the frequency of the chain.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def SetPhase(self, request, context):
        """*
        Set the phase of the entire input or output chain.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetPhase(self, request, context):
        """*
        Get the phase of the entire input or output chain.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def SetAttenuation(self, request, context):
        """*
        Set the attenuation for the input or output chain.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetAttenuation(self, request, context):
        """*
        Get the attenuation for the input or output chain.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def ToRfdcIndex(self, request, context):
        """*
        Returns the RFdc index attached to this converter index
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def ToChannelIndex(self, request, context):
        """*
        Returns the Channel index attached to this converter index
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_DirectRfServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "SetFrequency": grpc.unary_unary_rpc_method_handler(
            servicer.SetFrequency,
            request_deserializer=direct__rf__pb2.IndexedDouble.FromString,
            response_serializer=datatypes__pb2.Empty.SerializeToString,
        ),
        "GetFrequency": grpc.unary_unary_rpc_method_handler(
            servicer.GetFrequency,
            request_deserializer=direct__rf__pb2.ConverterIndex.FromString,
            response_serializer=datatypes__pb2.Double.SerializeToString,
        ),
        "SetPhase": grpc.unary_unary_rpc_method_handler(
            servicer.SetPhase,
            request_deserializer=direct__rf__pb2.IndexedDouble.FromString,
            response_serializer=datatypes__pb2.Empty.SerializeToString,
        ),
        "GetPhase": grpc.unary_unary_rpc_method_handler(
            servicer.GetPhase,
            request_deserializer=direct__rf__pb2.ConverterIndex.FromString,
            response_serializer=datatypes__pb2.Double.SerializeToString,
        ),
        "SetAttenuation": grpc.unary_unary_rpc_method_handler(
            servicer.SetAttenuation,
            request_deserializer=direct__rf__pb2.IndexedDouble.FromString,
            response_serializer=datatypes__pb2.Empty.SerializeToString,
        ),
        "GetAttenuation": grpc.unary_unary_rpc_method_handler(
            servicer.GetAttenuation,
            request_deserializer=direct__rf__pb2.ConverterIndex.FromString,
            response_serializer=datatypes__pb2.Double.SerializeToString,
        ),
        "ToRfdcIndex": grpc.unary_unary_rpc_method_handler(
            servicer.ToRfdcIndex,
            request_deserializer=direct__rf__pb2.ConverterIndex.FromString,
            response_serializer=direct__rf__pb2.RfDcIndex.SerializeToString,
        ),
        "ToChannelIndex": grpc.unary_unary_rpc_method_handler(
            servicer.ToChannelIndex,
            request_deserializer=direct__rf__pb2.ConverterIndex.FromString,
            response_serializer=datatypes__pb2.UInt.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        "direct_rf.DirectRfService", rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))


# This class is part of an EXPERIMENTAL API.
class DirectRfService(object):
    """*
    The DirectRf service manages the entire input / output chain using
    the DirectRf frontend board.
    """

    @staticmethod
    def SetFrequency(
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
            "/direct_rf.DirectRfService/SetFrequency",
            direct__rf__pb2.IndexedDouble.SerializeToString,
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
    def GetFrequency(
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
            "/direct_rf.DirectRfService/GetFrequency",
            direct__rf__pb2.ConverterIndex.SerializeToString,
            datatypes__pb2.Double.FromString,
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
    def SetPhase(
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
            "/direct_rf.DirectRfService/SetPhase",
            direct__rf__pb2.IndexedDouble.SerializeToString,
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
    def GetPhase(
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
            "/direct_rf.DirectRfService/GetPhase",
            direct__rf__pb2.ConverterIndex.SerializeToString,
            datatypes__pb2.Double.FromString,
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
            "/direct_rf.DirectRfService/SetAttenuation",
            direct__rf__pb2.IndexedDouble.SerializeToString,
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
            "/direct_rf.DirectRfService/GetAttenuation",
            direct__rf__pb2.ConverterIndex.SerializeToString,
            datatypes__pb2.Double.FromString,
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
    def ToRfdcIndex(
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
            "/direct_rf.DirectRfService/ToRfdcIndex",
            direct__rf__pb2.ConverterIndex.SerializeToString,
            direct__rf__pb2.RfDcIndex.FromString,
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
    def ToChannelIndex(
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
            "/direct_rf.DirectRfService/ToChannelIndex",
            direct__rf__pb2.ConverterIndex.SerializeToString,
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
