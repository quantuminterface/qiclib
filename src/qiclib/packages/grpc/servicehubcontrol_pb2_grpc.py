# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import qiclib.packages.grpc.datatypes_pb2 as datatypes__pb2
import qiclib.packages.grpc.servicehubcontrol_pb2 as servicehubcontrol__pb2


class ServicehubControlServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Reload = channel.unary_unary(
            "/servicehubcontrol.ServicehubControlService/Reload",
            request_serializer=datatypes__pb2.Empty.SerializeToString,
            response_deserializer=datatypes__pb2.Empty.FromString,
        )
        self.Reboot = channel.unary_unary(
            "/servicehubcontrol.ServicehubControlService/Reboot",
            request_serializer=datatypes__pb2.Empty.SerializeToString,
            response_deserializer=datatypes__pb2.Empty.FromString,
        )
        self.GetLogs = channel.unary_unary(
            "/servicehubcontrol.ServicehubControlService/GetLogs",
            request_serializer=datatypes__pb2.Empty.SerializeToString,
            response_deserializer=servicehubcontrol__pb2.MultiLog.FromString,
        )
        self.CleanLogs = channel.unary_unary(
            "/servicehubcontrol.ServicehubControlService/CleanLogs",
            request_serializer=servicehubcontrol__pb2.MultiLog.SerializeToString,
            response_deserializer=servicehubcontrol__pb2.MultiLog.FromString,
        )
        self.GetPlugins = channel.unary_unary(
            "/servicehubcontrol.ServicehubControlService/GetPlugins",
            request_serializer=datatypes__pb2.Empty.SerializeToString,
            response_deserializer=servicehubcontrol__pb2.Plugins.FromString,
        )
        self.GetPluginList = channel.unary_unary(
            "/servicehubcontrol.ServicehubControlService/GetPluginList",
            request_serializer=datatypes__pb2.Empty.SerializeToString,
            response_deserializer=servicehubcontrol__pb2.StringVector.FromString,
        )
        self.GetEndpointsOfPlugin = channel.unary_unary(
            "/servicehubcontrol.ServicehubControlService/GetEndpointsOfPlugin",
            request_serializer=servicehubcontrol__pb2.String.SerializeToString,
            response_deserializer=servicehubcontrol__pb2.StringVector.FromString,
        )
        self.GetEndpointIndexOfPlugin = channel.unary_unary(
            "/servicehubcontrol.ServicehubControlService/GetEndpointIndexOfPlugin",
            request_serializer=servicehubcontrol__pb2.EndpointIndexRequest.SerializeToString,
            response_deserializer=servicehubcontrol__pb2.Integer.FromString,
        )
        self.GetPluginVersion = channel.unary_unary(
            "/servicehubcontrol.ServicehubControlService/GetPluginVersion",
            request_serializer=servicehubcontrol__pb2.String.SerializeToString,
            response_deserializer=servicehubcontrol__pb2.PluginVersions.FromString,
        )
        self.GetServiceHubVersion = channel.unary_unary(
            "/servicehubcontrol.ServicehubControlService/GetServiceHubVersion",
            request_serializer=datatypes__pb2.Empty.SerializeToString,
            response_deserializer=servicehubcontrol__pb2.ServiceHubVersions.FromString,
        )
        self.DumpCoverageData = channel.unary_unary(
            "/servicehubcontrol.ServicehubControlService/DumpCoverageData",
            request_serializer=datatypes__pb2.Empty.SerializeToString,
            response_deserializer=servicehubcontrol__pb2.BuildPath.FromString,
        )
        self.IsAlive = channel.unary_unary(
            "/servicehubcontrol.ServicehubControlService/IsAlive",
            request_serializer=datatypes__pb2.Empty.SerializeToString,
            response_deserializer=datatypes__pb2.Empty.FromString,
        )


class ServicehubControlServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Reload(self, request, context):
        """*
        @brief Shutdown and restart grpc server

        @return void
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def Reboot(self, request, context):
        """*
        @brief Shutdown and restart platform

        @return void
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetLogs(self, request, context):
        """*
        @brief Returns log of every registered plugin.

        @return Array of logs containing name, path and content
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def CleanLogs(self, request, context):
        """*
        @brief Cleans module logs.

        @param msg MultiLog If left empty, cleans all logs; if defined cleans specified logs
        @return if everything was alright; return names of logs that could not be deleted
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetPlugins(self, request, context):
        """*
        @brief Returns a json dict of registered plugins.

        @return Dictionary of registered plugins and its config in json format
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetPluginList(self, request, context):
        """*
        @brief Returns a list of registered plugins.

        @return Vector of registered plugin names as strings.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetEndpointsOfPlugin(self, request, context):
        """*
        @brief Returns a list of Endpoints of plugins.

        @param msg Name of a plugin
        @return Vector of registered Endpoints names as strings.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetEndpointIndexOfPlugin(self, request, context):
        """*
        @brief Get the index of a Endpoint from a Plugin

        @param msg Names of Plugin and Endpoint
        @return Index as integer
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetPluginVersion(self, request, context):
        """*
        @brief Returns the git version of chosen plugin

        @param msg Name of a plugin
        @return Version of the common, plugin and proto repo.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetServiceHubVersion(self, request, context):
        """*
        @brief Returns the git version of the service hub

        @param msg Name of a plugin
        @return Version of the common, hub and proto repo.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def DumpCoverageData(self, request, context):
        """*
        @brief Returns the build path and dumps coverage info. Fails if not a coverage build.

        @param sdr.datatypes.Empty
        @return Build path
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def IsAlive(self, request, context):
        """*
        @brief Just an RPC that can be called to check if the gRPC server is reachable and responsive.

        @param sdr.datatypes.Empty
        @return sdr.datatypes.Empty
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_ServicehubControlServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "Reload": grpc.unary_unary_rpc_method_handler(
            servicer.Reload,
            request_deserializer=datatypes__pb2.Empty.FromString,
            response_serializer=datatypes__pb2.Empty.SerializeToString,
        ),
        "Reboot": grpc.unary_unary_rpc_method_handler(
            servicer.Reboot,
            request_deserializer=datatypes__pb2.Empty.FromString,
            response_serializer=datatypes__pb2.Empty.SerializeToString,
        ),
        "GetLogs": grpc.unary_unary_rpc_method_handler(
            servicer.GetLogs,
            request_deserializer=datatypes__pb2.Empty.FromString,
            response_serializer=servicehubcontrol__pb2.MultiLog.SerializeToString,
        ),
        "CleanLogs": grpc.unary_unary_rpc_method_handler(
            servicer.CleanLogs,
            request_deserializer=servicehubcontrol__pb2.MultiLog.FromString,
            response_serializer=servicehubcontrol__pb2.MultiLog.SerializeToString,
        ),
        "GetPlugins": grpc.unary_unary_rpc_method_handler(
            servicer.GetPlugins,
            request_deserializer=datatypes__pb2.Empty.FromString,
            response_serializer=servicehubcontrol__pb2.Plugins.SerializeToString,
        ),
        "GetPluginList": grpc.unary_unary_rpc_method_handler(
            servicer.GetPluginList,
            request_deserializer=datatypes__pb2.Empty.FromString,
            response_serializer=servicehubcontrol__pb2.StringVector.SerializeToString,
        ),
        "GetEndpointsOfPlugin": grpc.unary_unary_rpc_method_handler(
            servicer.GetEndpointsOfPlugin,
            request_deserializer=servicehubcontrol__pb2.String.FromString,
            response_serializer=servicehubcontrol__pb2.StringVector.SerializeToString,
        ),
        "GetEndpointIndexOfPlugin": grpc.unary_unary_rpc_method_handler(
            servicer.GetEndpointIndexOfPlugin,
            request_deserializer=servicehubcontrol__pb2.EndpointIndexRequest.FromString,
            response_serializer=servicehubcontrol__pb2.Integer.SerializeToString,
        ),
        "GetPluginVersion": grpc.unary_unary_rpc_method_handler(
            servicer.GetPluginVersion,
            request_deserializer=servicehubcontrol__pb2.String.FromString,
            response_serializer=servicehubcontrol__pb2.PluginVersions.SerializeToString,
        ),
        "GetServiceHubVersion": grpc.unary_unary_rpc_method_handler(
            servicer.GetServiceHubVersion,
            request_deserializer=datatypes__pb2.Empty.FromString,
            response_serializer=servicehubcontrol__pb2.ServiceHubVersions.SerializeToString,
        ),
        "DumpCoverageData": grpc.unary_unary_rpc_method_handler(
            servicer.DumpCoverageData,
            request_deserializer=datatypes__pb2.Empty.FromString,
            response_serializer=servicehubcontrol__pb2.BuildPath.SerializeToString,
        ),
        "IsAlive": grpc.unary_unary_rpc_method_handler(
            servicer.IsAlive,
            request_deserializer=datatypes__pb2.Empty.FromString,
            response_serializer=datatypes__pb2.Empty.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        "servicehubcontrol.ServicehubControlService", rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))


# This class is part of an EXPERIMENTAL API.
class ServicehubControlService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Reload(
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
            "/servicehubcontrol.ServicehubControlService/Reload",
            datatypes__pb2.Empty.SerializeToString,
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
    def Reboot(
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
            "/servicehubcontrol.ServicehubControlService/Reboot",
            datatypes__pb2.Empty.SerializeToString,
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
    def GetLogs(
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
            "/servicehubcontrol.ServicehubControlService/GetLogs",
            datatypes__pb2.Empty.SerializeToString,
            servicehubcontrol__pb2.MultiLog.FromString,
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
    def CleanLogs(
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
            "/servicehubcontrol.ServicehubControlService/CleanLogs",
            servicehubcontrol__pb2.MultiLog.SerializeToString,
            servicehubcontrol__pb2.MultiLog.FromString,
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
    def GetPlugins(
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
            "/servicehubcontrol.ServicehubControlService/GetPlugins",
            datatypes__pb2.Empty.SerializeToString,
            servicehubcontrol__pb2.Plugins.FromString,
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
    def GetPluginList(
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
            "/servicehubcontrol.ServicehubControlService/GetPluginList",
            datatypes__pb2.Empty.SerializeToString,
            servicehubcontrol__pb2.StringVector.FromString,
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
    def GetEndpointsOfPlugin(
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
            "/servicehubcontrol.ServicehubControlService/GetEndpointsOfPlugin",
            servicehubcontrol__pb2.String.SerializeToString,
            servicehubcontrol__pb2.StringVector.FromString,
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
    def GetEndpointIndexOfPlugin(
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
            "/servicehubcontrol.ServicehubControlService/GetEndpointIndexOfPlugin",
            servicehubcontrol__pb2.EndpointIndexRequest.SerializeToString,
            servicehubcontrol__pb2.Integer.FromString,
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
    def GetPluginVersion(
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
            "/servicehubcontrol.ServicehubControlService/GetPluginVersion",
            servicehubcontrol__pb2.String.SerializeToString,
            servicehubcontrol__pb2.PluginVersions.FromString,
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
    def GetServiceHubVersion(
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
            "/servicehubcontrol.ServicehubControlService/GetServiceHubVersion",
            datatypes__pb2.Empty.SerializeToString,
            servicehubcontrol__pb2.ServiceHubVersions.FromString,
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
    def DumpCoverageData(
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
            "/servicehubcontrol.ServicehubControlService/DumpCoverageData",
            datatypes__pb2.Empty.SerializeToString,
            servicehubcontrol__pb2.BuildPath.FromString,
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
    def IsAlive(
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
            "/servicehubcontrol.ServicehubControlService/IsAlive",
            datatypes__pb2.Empty.SerializeToString,
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
