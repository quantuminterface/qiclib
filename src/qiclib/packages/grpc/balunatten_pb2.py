# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: balunatten.proto
# Protobuf Python Version: 5.27.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    27,
    2,
    '',
    'balunatten.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import qiclib.packages.grpc.datatypes_pb2 as datatypes__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x10\x62\x61lunatten.proto\x12\nbalunatten\x1a\x0f\x64\x61tatypes.proto\"\\\n\x07\x43hannel\x12\x0f\n\x07\x63hannel\x18\x01 \x01(\r\x12&\n\x04type\x18\x02 \x01(\x0e\x32\x18.balunatten.Channel.Type\"\x18\n\x04Type\x12\x07\n\x03\x41\x44\x43\x10\x00\x12\x07\n\x03\x44\x41\x43\x10\x01\"=\n\x06Number\x12$\n\x07\x63hannel\x18\x01 \x01(\x0b\x32\x13.balunatten.Channel\x12\r\n\x05value\x18\x02 \x01(\r\"<\n\x05\x46loat\x12$\n\x07\x63hannel\x18\x01 \x01(\x0b\x32\x13.balunatten.Channel\x12\r\n\x05value\x18\x02 \x01(\x02\x32\xed\x02\n\x11\x42\x61lUnAttenService\x12\x39\n\x0eSetAttenuation\x12\x11.balunatten.Float\x1a\x14.sdr.datatypes.Empty\x12;\n\x0eGetAttenuation\x12\x13.balunatten.Channel\x1a\x14.sdr.datatypes.Float\x12\x36\n\tSwitchOff\x12\x13.balunatten.Channel\x1a\x14.sdr.datatypes.Empty\x12\x39\n\rSwitchNyquist\x12\x12.balunatten.Number\x1a\x14.sdr.datatypes.Empty\x12\x36\n\nGetNyquist\x12\x13.balunatten.Channel\x1a\x13.sdr.datatypes.UInt\x12\x35\n\x08SwitchDC\x12\x13.balunatten.Channel\x1a\x14.sdr.datatypes.Emptyb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'balunatten_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_CHANNEL']._serialized_start=49
  _globals['_CHANNEL']._serialized_end=141
  _globals['_CHANNEL_TYPE']._serialized_start=117
  _globals['_CHANNEL_TYPE']._serialized_end=141
  _globals['_NUMBER']._serialized_start=143
  _globals['_NUMBER']._serialized_end=204
  _globals['_FLOAT']._serialized_start=206
  _globals['_FLOAT']._serialized_end=266
  _globals['_BALUNATTENSERVICE']._serialized_start=269
  _globals['_BALUNATTENSERVICE']._serialized_end=634
# @@protoc_insertion_point(module_scope)
