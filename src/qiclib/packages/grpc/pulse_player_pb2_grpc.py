# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

import qiclib.packages.grpc.datatypes_pb2 as datatypes__pb2
import qiclib.packages.grpc.pulse_player_pb2 as pulse__player__pb2

GRPC_GENERATED_VERSION = '1.66.1'
GRPC_VERSION = grpc.__version__
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    raise RuntimeError(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in pulse_player_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


class PulsePlayerServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Reset = channel.unary_unary(
                '/pulse_player.PulsePlayerService/Reset',
                request_serializer=datatypes__pb2.EndpointIndex.SerializeToString,
                response_deserializer=datatypes__pb2.Empty.FromString,
                _registered_method=True)
        self.SetPulse = channel.unary_unary(
                '/pulse_player.PulsePlayerService/SetPulse',
                request_serializer=pulse__player__pb2.IndexedPulses.SerializeToString,
                response_deserializer=datatypes__pb2.Empty.FromString,
                _registered_method=True)
        self.GetPulse = channel.unary_unary(
                '/pulse_player.PulsePlayerService/GetPulse',
                request_serializer=pulse__player__pb2.PulseIndex.SerializeToString,
                response_deserializer=pulse__player__pb2.Pulse.FromString,
                _registered_method=True)
        self.SetOffset = channel.unary_unary(
                '/pulse_player.PulsePlayerService/SetOffset',
                request_serializer=pulse__player__pb2.Offset.SerializeToString,
                response_deserializer=datatypes__pb2.Empty.FromString,
                _registered_method=True)
        self.GetOffset = channel.unary_unary(
                '/pulse_player.PulsePlayerService/GetOffset',
                request_serializer=datatypes__pb2.EndpointIndex.SerializeToString,
                response_deserializer=pulse__player__pb2.Offset.FromString,
                _registered_method=True)
        self.Trigger = channel.unary_unary(
                '/pulse_player.PulsePlayerService/Trigger',
                request_serializer=pulse__player__pb2.PulseIndex.SerializeToString,
                response_deserializer=datatypes__pb2.Empty.FromString,
                _registered_method=True)
        self.GetPulseCapacity = channel.unary_unary(
                '/pulse_player.PulsePlayerService/GetPulseCapacity',
                request_serializer=datatypes__pb2.EndpointIndex.SerializeToString,
                response_deserializer=datatypes__pb2.UInt.FromString,
                _registered_method=True)
        self.GetSampleRate = channel.unary_unary(
                '/pulse_player.PulsePlayerService/GetSampleRate',
                request_serializer=datatypes__pb2.EndpointIndex.SerializeToString,
                response_deserializer=datatypes__pb2.Double.FromString,
                _registered_method=True)


class PulsePlayerServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Reset(self, request, context):
        """*
        Resets the module. Also clears the pulse memory.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SetPulse(self, request, context):
        """*
        Sets the value of a pulse.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetPulse(self, request, context):
        """*
        Returns a subset of all pulses.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SetOffset(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetOffset(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Trigger(self, request, context):
        """*
        Trigger a specific pulse
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetPulseCapacity(self, request, context):
        """*
        Returns the amount of pulses that this component can handle.
        Note that the count a user can set is one less because there is a zero pulse
        which cannot be overwritten.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetSampleRate(self, request, context):
        """*
        Returns the sample rate in Hertz for the given endpoint index.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_PulsePlayerServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Reset': grpc.unary_unary_rpc_method_handler(
                    servicer.Reset,
                    request_deserializer=datatypes__pb2.EndpointIndex.FromString,
                    response_serializer=datatypes__pb2.Empty.SerializeToString,
            ),
            'SetPulse': grpc.unary_unary_rpc_method_handler(
                    servicer.SetPulse,
                    request_deserializer=pulse__player__pb2.IndexedPulses.FromString,
                    response_serializer=datatypes__pb2.Empty.SerializeToString,
            ),
            'GetPulse': grpc.unary_unary_rpc_method_handler(
                    servicer.GetPulse,
                    request_deserializer=pulse__player__pb2.PulseIndex.FromString,
                    response_serializer=pulse__player__pb2.Pulse.SerializeToString,
            ),
            'SetOffset': grpc.unary_unary_rpc_method_handler(
                    servicer.SetOffset,
                    request_deserializer=pulse__player__pb2.Offset.FromString,
                    response_serializer=datatypes__pb2.Empty.SerializeToString,
            ),
            'GetOffset': grpc.unary_unary_rpc_method_handler(
                    servicer.GetOffset,
                    request_deserializer=datatypes__pb2.EndpointIndex.FromString,
                    response_serializer=pulse__player__pb2.Offset.SerializeToString,
            ),
            'Trigger': grpc.unary_unary_rpc_method_handler(
                    servicer.Trigger,
                    request_deserializer=pulse__player__pb2.PulseIndex.FromString,
                    response_serializer=datatypes__pb2.Empty.SerializeToString,
            ),
            'GetPulseCapacity': grpc.unary_unary_rpc_method_handler(
                    servicer.GetPulseCapacity,
                    request_deserializer=datatypes__pb2.EndpointIndex.FromString,
                    response_serializer=datatypes__pb2.UInt.SerializeToString,
            ),
            'GetSampleRate': grpc.unary_unary_rpc_method_handler(
                    servicer.GetSampleRate,
                    request_deserializer=datatypes__pb2.EndpointIndex.FromString,
                    response_serializer=datatypes__pb2.Double.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'pulse_player.PulsePlayerService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('pulse_player.PulsePlayerService', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class PulsePlayerService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Reset(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/pulse_player.PulsePlayerService/Reset',
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
            _registered_method=True)

    @staticmethod
    def SetPulse(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/pulse_player.PulsePlayerService/SetPulse',
            pulse__player__pb2.IndexedPulses.SerializeToString,
            datatypes__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def GetPulse(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/pulse_player.PulsePlayerService/GetPulse',
            pulse__player__pb2.PulseIndex.SerializeToString,
            pulse__player__pb2.Pulse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def SetOffset(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/pulse_player.PulsePlayerService/SetOffset',
            pulse__player__pb2.Offset.SerializeToString,
            datatypes__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def GetOffset(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/pulse_player.PulsePlayerService/GetOffset',
            datatypes__pb2.EndpointIndex.SerializeToString,
            pulse__player__pb2.Offset.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def Trigger(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/pulse_player.PulsePlayerService/Trigger',
            pulse__player__pb2.PulseIndex.SerializeToString,
            datatypes__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def GetPulseCapacity(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/pulse_player.PulsePlayerService/GetPulseCapacity',
            datatypes__pb2.EndpointIndex.SerializeToString,
            datatypes__pb2.UInt.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def GetSampleRate(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/pulse_player.PulsePlayerService/GetSampleRate',
            datatypes__pb2.EndpointIndex.SerializeToString,
            datatypes__pb2.Double.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
