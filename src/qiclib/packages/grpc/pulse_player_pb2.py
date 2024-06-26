# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: pulse_player.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import qiclib.packages.grpc.datatypes_pb2 as datatypes__pb2

from qiclib.packages.grpc.datatypes_pb2 import *

DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x12pulse_player.proto\x12\x0cpulse_player\x1a\x0f\x64\x61tatypes.proto"&\n\x05Pulse\x12\r\n\x05index\x18\x01 \x01(\r\x12\x0e\n\x06values\x18\x02 \x03(\x01"`\n\rIndexedPulses\x12+\n\x05index\x18\x01 \x01(\x0b\x32\x1c.sdr.datatypes.EndpointIndex\x12"\n\x05pulse\x18\x02 \x01(\x0b\x32\x13.pulse_player.Pulse"H\n\nPulseIndex\x12+\n\x05index\x18\x01 \x01(\x0b\x32\x1c.sdr.datatypes.EndpointIndex\x12\r\n\x05pulse\x18\x02 \x01(\r2\x93\x03\n\x12PulsePlayerService\x12;\n\x05Reset\x12\x1c.sdr.datatypes.EndpointIndex\x1a\x14.sdr.datatypes.Empty\x12=\n\x08SetPulse\x12\x1b.pulse_player.IndexedPulses\x1a\x14.sdr.datatypes.Empty\x12\x39\n\x08GetPulse\x12\x18.pulse_player.PulseIndex\x1a\x13.pulse_player.Pulse\x12\x39\n\x07Trigger\x12\x18.pulse_player.PulseIndex\x1a\x14.sdr.datatypes.Empty\x12\x45\n\x10GetPulseCapacity\x12\x1c.sdr.datatypes.EndpointIndex\x1a\x13.sdr.datatypes.UInt\x12\x44\n\rGetSampleRate\x12\x1c.sdr.datatypes.EndpointIndex\x1a\x15.sdr.datatypes.DoubleP\x00\x62\x06proto3'
)


_PULSE = DESCRIPTOR.message_types_by_name["Pulse"]
_INDEXEDPULSES = DESCRIPTOR.message_types_by_name["IndexedPulses"]
_PULSEINDEX = DESCRIPTOR.message_types_by_name["PulseIndex"]
Pulse = _reflection.GeneratedProtocolMessageType(
    "Pulse",
    (_message.Message,),
    {
        "DESCRIPTOR": _PULSE,
        "__module__": "pulse_player_pb2"
        # @@protoc_insertion_point(class_scope:pulse_player.Pulse)
    },
)
_sym_db.RegisterMessage(Pulse)

IndexedPulses = _reflection.GeneratedProtocolMessageType(
    "IndexedPulses",
    (_message.Message,),
    {
        "DESCRIPTOR": _INDEXEDPULSES,
        "__module__": "pulse_player_pb2"
        # @@protoc_insertion_point(class_scope:pulse_player.IndexedPulses)
    },
)
_sym_db.RegisterMessage(IndexedPulses)

PulseIndex = _reflection.GeneratedProtocolMessageType(
    "PulseIndex",
    (_message.Message,),
    {
        "DESCRIPTOR": _PULSEINDEX,
        "__module__": "pulse_player_pb2"
        # @@protoc_insertion_point(class_scope:pulse_player.PulseIndex)
    },
)
_sym_db.RegisterMessage(PulseIndex)

_PULSEPLAYERSERVICE = DESCRIPTOR.services_by_name["PulsePlayerService"]
if _descriptor._USE_C_DESCRIPTORS == False:
    DESCRIPTOR._options = None
    _PULSE._serialized_start = 53
    _PULSE._serialized_end = 91
    _INDEXEDPULSES._serialized_start = 93
    _INDEXEDPULSES._serialized_end = 189
    _PULSEINDEX._serialized_start = 191
    _PULSEINDEX._serialized_end = 263
    _PULSEPLAYERSERVICE._serialized_start = 266
    _PULSEPLAYERSERVICE._serialized_end = 669
# @@protoc_insertion_point(module_scope)
