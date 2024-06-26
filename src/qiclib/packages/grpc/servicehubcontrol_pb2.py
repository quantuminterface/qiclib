# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: servicehubcontrol.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import qiclib.packages.grpc.datatypes_pb2 as datatypes__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x17servicehubcontrol.proto\x12\x11servicehubcontrol\x1a\x0f\x64\x61tatypes.proto"2\n\x03Log\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0c\n\x04path\x18\x02 \x01(\t\x12\x0f\n\x07\x63ontent\x18\x03 \x01(\t"\x18\n\tBuildPath\x12\x0b\n\x03str\x18\x01 \x01(\t"/\n\x08MultiLog\x12#\n\x03log\x18\x01 \x03(\x0b\x32\x16.servicehubcontrol.Log"8\n\nPluginInfo\x12\x13\n\x0bplugin_name\x18\x01 \x01(\t\x12\x15\n\rplugin_config\x18\x02 \x01(\t"4\n\x07Plugins\x12)\n\x02pi\x18\x01 \x03(\x0b\x32\x1d.servicehubcontrol.PluginInfo"B\n\x14\x45ndpointIndexRequest\x12\x13\n\x0bplugin_name\x18\x01 \x01(\t\x12\x15\n\rendpoint_name\x18\x02 \x01(\t"\x15\n\x06String\x12\x0b\n\x03str\x18\x01 \x01(\t"\x1b\n\x0cStringVector\x12\x0b\n\x03str\x18\x01 \x03(\t"\x16\n\x07Integer\x12\x0b\n\x03val\x18\x01 \x01(\x05"W\n\x0ePluginVersions\x12\x16\n\x0e\x64river_version\x18\x01 \x01(\t\x12\x15\n\rproto_version\x18\x02 \x01(\t\x12\x16\n\x0e\x63ommon_version\x18\x03 \x01(\t"_\n\x12ServiceHubVersions\x12\x1a\n\x12servicehub_version\x18\x01 \x01(\t\x12\x15\n\rproto_version\x18\x02 \x01(\t\x12\x16\n\x0e\x63ommon_version\x18\x03 \x01(\t2\x86\x07\n\x18ServicehubControlService\x12\x36\n\x06Reload\x12\x14.sdr.datatypes.Empty\x1a\x14.sdr.datatypes.Empty"\x00\x12\x36\n\x06Reboot\x12\x14.sdr.datatypes.Empty\x1a\x14.sdr.datatypes.Empty"\x00\x12>\n\x07GetLogs\x12\x14.sdr.datatypes.Empty\x1a\x1b.servicehubcontrol.MultiLog"\x00\x12G\n\tCleanLogs\x12\x1b.servicehubcontrol.MultiLog\x1a\x1b.servicehubcontrol.MultiLog"\x00\x12@\n\nGetPlugins\x12\x14.sdr.datatypes.Empty\x1a\x1a.servicehubcontrol.Plugins"\x00\x12H\n\rGetPluginList\x12\x14.sdr.datatypes.Empty\x1a\x1f.servicehubcontrol.StringVector"\x00\x12T\n\x14GetEndpointsOfPlugin\x12\x19.servicehubcontrol.String\x1a\x1f.servicehubcontrol.StringVector"\x00\x12\x61\n\x18GetEndpointIndexOfPlugin\x12\'.servicehubcontrol.EndpointIndexRequest\x1a\x1a.servicehubcontrol.Integer"\x00\x12R\n\x10GetPluginVersion\x12\x19.servicehubcontrol.String\x1a!.servicehubcontrol.PluginVersions"\x00\x12U\n\x14GetServiceHubVersion\x12\x14.sdr.datatypes.Empty\x1a%.servicehubcontrol.ServiceHubVersions"\x00\x12H\n\x10\x44umpCoverageData\x12\x14.sdr.datatypes.Empty\x1a\x1c.servicehubcontrol.BuildPath"\x00\x12\x37\n\x07IsAlive\x12\x14.sdr.datatypes.Empty\x1a\x14.sdr.datatypes.Empty"\x00\x62\x06proto3'
)


_LOG = DESCRIPTOR.message_types_by_name["Log"]
_BUILDPATH = DESCRIPTOR.message_types_by_name["BuildPath"]
_MULTILOG = DESCRIPTOR.message_types_by_name["MultiLog"]
_PLUGININFO = DESCRIPTOR.message_types_by_name["PluginInfo"]
_PLUGINS = DESCRIPTOR.message_types_by_name["Plugins"]
_ENDPOINTINDEXREQUEST = DESCRIPTOR.message_types_by_name["EndpointIndexRequest"]
_STRING = DESCRIPTOR.message_types_by_name["String"]
_STRINGVECTOR = DESCRIPTOR.message_types_by_name["StringVector"]
_INTEGER = DESCRIPTOR.message_types_by_name["Integer"]
_PLUGINVERSIONS = DESCRIPTOR.message_types_by_name["PluginVersions"]
_SERVICEHUBVERSIONS = DESCRIPTOR.message_types_by_name["ServiceHubVersions"]
Log = _reflection.GeneratedProtocolMessageType(
    "Log",
    (_message.Message,),
    {
        "DESCRIPTOR": _LOG,
        "__module__": "servicehubcontrol_pb2"
        # @@protoc_insertion_point(class_scope:servicehubcontrol.Log)
    },
)
_sym_db.RegisterMessage(Log)

BuildPath = _reflection.GeneratedProtocolMessageType(
    "BuildPath",
    (_message.Message,),
    {
        "DESCRIPTOR": _BUILDPATH,
        "__module__": "servicehubcontrol_pb2"
        # @@protoc_insertion_point(class_scope:servicehubcontrol.BuildPath)
    },
)
_sym_db.RegisterMessage(BuildPath)

MultiLog = _reflection.GeneratedProtocolMessageType(
    "MultiLog",
    (_message.Message,),
    {
        "DESCRIPTOR": _MULTILOG,
        "__module__": "servicehubcontrol_pb2"
        # @@protoc_insertion_point(class_scope:servicehubcontrol.MultiLog)
    },
)
_sym_db.RegisterMessage(MultiLog)

PluginInfo = _reflection.GeneratedProtocolMessageType(
    "PluginInfo",
    (_message.Message,),
    {
        "DESCRIPTOR": _PLUGININFO,
        "__module__": "servicehubcontrol_pb2"
        # @@protoc_insertion_point(class_scope:servicehubcontrol.PluginInfo)
    },
)
_sym_db.RegisterMessage(PluginInfo)

Plugins = _reflection.GeneratedProtocolMessageType(
    "Plugins",
    (_message.Message,),
    {
        "DESCRIPTOR": _PLUGINS,
        "__module__": "servicehubcontrol_pb2"
        # @@protoc_insertion_point(class_scope:servicehubcontrol.Plugins)
    },
)
_sym_db.RegisterMessage(Plugins)

EndpointIndexRequest = _reflection.GeneratedProtocolMessageType(
    "EndpointIndexRequest",
    (_message.Message,),
    {
        "DESCRIPTOR": _ENDPOINTINDEXREQUEST,
        "__module__": "servicehubcontrol_pb2"
        # @@protoc_insertion_point(class_scope:servicehubcontrol.EndpointIndexRequest)
    },
)
_sym_db.RegisterMessage(EndpointIndexRequest)

String = _reflection.GeneratedProtocolMessageType(
    "String",
    (_message.Message,),
    {
        "DESCRIPTOR": _STRING,
        "__module__": "servicehubcontrol_pb2"
        # @@protoc_insertion_point(class_scope:servicehubcontrol.String)
    },
)
_sym_db.RegisterMessage(String)

StringVector = _reflection.GeneratedProtocolMessageType(
    "StringVector",
    (_message.Message,),
    {
        "DESCRIPTOR": _STRINGVECTOR,
        "__module__": "servicehubcontrol_pb2"
        # @@protoc_insertion_point(class_scope:servicehubcontrol.StringVector)
    },
)
_sym_db.RegisterMessage(StringVector)

Integer = _reflection.GeneratedProtocolMessageType(
    "Integer",
    (_message.Message,),
    {
        "DESCRIPTOR": _INTEGER,
        "__module__": "servicehubcontrol_pb2"
        # @@protoc_insertion_point(class_scope:servicehubcontrol.Integer)
    },
)
_sym_db.RegisterMessage(Integer)

PluginVersions = _reflection.GeneratedProtocolMessageType(
    "PluginVersions",
    (_message.Message,),
    {
        "DESCRIPTOR": _PLUGINVERSIONS,
        "__module__": "servicehubcontrol_pb2"
        # @@protoc_insertion_point(class_scope:servicehubcontrol.PluginVersions)
    },
)
_sym_db.RegisterMessage(PluginVersions)

ServiceHubVersions = _reflection.GeneratedProtocolMessageType(
    "ServiceHubVersions",
    (_message.Message,),
    {
        "DESCRIPTOR": _SERVICEHUBVERSIONS,
        "__module__": "servicehubcontrol_pb2"
        # @@protoc_insertion_point(class_scope:servicehubcontrol.ServiceHubVersions)
    },
)
_sym_db.RegisterMessage(ServiceHubVersions)

_SERVICEHUBCONTROLSERVICE = DESCRIPTOR.services_by_name["ServicehubControlService"]
if _descriptor._USE_C_DESCRIPTORS == False:

    DESCRIPTOR._options = None
    _LOG._serialized_start = 63
    _LOG._serialized_end = 113
    _BUILDPATH._serialized_start = 115
    _BUILDPATH._serialized_end = 139
    _MULTILOG._serialized_start = 141
    _MULTILOG._serialized_end = 188
    _PLUGININFO._serialized_start = 190
    _PLUGININFO._serialized_end = 246
    _PLUGINS._serialized_start = 248
    _PLUGINS._serialized_end = 300
    _ENDPOINTINDEXREQUEST._serialized_start = 302
    _ENDPOINTINDEXREQUEST._serialized_end = 368
    _STRING._serialized_start = 370
    _STRING._serialized_end = 391
    _STRINGVECTOR._serialized_start = 393
    _STRINGVECTOR._serialized_end = 420
    _INTEGER._serialized_start = 422
    _INTEGER._serialized_end = 444
    _PLUGINVERSIONS._serialized_start = 446
    _PLUGINVERSIONS._serialized_end = 533
    _SERVICEHUBVERSIONS._serialized_start = 535
    _SERVICEHUBVERSIONS._serialized_end = 630
    _SERVICEHUBCONTROLSERVICE._serialized_start = 633
    _SERVICEHUBCONTROLSERVICE._serialized_end = 1535
# @@protoc_insertion_point(module_scope)
