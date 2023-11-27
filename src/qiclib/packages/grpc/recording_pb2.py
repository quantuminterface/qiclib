# -*- coding: utf-8 -*-
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
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: recording.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x0frecording.proto\x12\trecording"\x1e\n\rEndpointIndex\x12\r\n\x05value\x18\x01 \x01(\r"/\n\x0cStatusReport\x12\x0e\n\x06report\x18\x01 \x01(\t\x12\x0f\n\x07\x66\x61ilure\x18\x02 \x01(\x08"X\n\x12InterferometerMode\x12\'\n\x05index\x18\x01 \x01(\x0b\x32\x18.recording.EndpointIndex\x12\x19\n\x11is_interferometer\x18\x02 \x01(\x08"P\n\x0e\x43ontinuousMode\x12\'\n\x05index\x18\x01 \x01(\x0b\x32\x18.recording.EndpointIndex\x12\x15\n\ris_continuous\x18\x02 \x01(\x08"\xd9\x01\n\x07Trigger\x12\'\n\x05index\x18\x01 \x01(\x0b\x32\x18.recording.EndpointIndex\x12.\n\x05value\x18\x02 \x01(\x0e\x32\x1f.recording.Trigger.TriggerValue"u\n\x0cTriggerValue\x12\x08\n\x04NONE\x10\x00\x12\n\n\x06SINGLE\x10\x01\x12\x0b\n\x07ONESHOT\x10\x02\x12\x14\n\x10START_CONTINUOUS\x10\x06\x12\x13\n\x0fSTOP_CONTINUOUS\x10\x07\x12\t\n\x05RESET\x10\x0e\x12\x0c\n\x08NCO_SYNC\x10\x0f"G\n\rTriggerOffset\x12\'\n\x05index\x18\x01 \x01(\x0b\x32\x18.recording.EndpointIndex\x12\r\n\x05value\x18\x02 \x01(\x01"K\n\x11RecordingDuration\x12\'\n\x05index\x18\x01 \x01(\x0b\x32\x18.recording.EndpointIndex\x12\r\n\x05value\x18\x02 \x01(\x01"D\n\nValueShift\x12\'\n\x05index\x18\x01 \x01(\x0b\x32\x18.recording.EndpointIndex\x12\r\n\x05value\x18\x02 \x01(\r"J\n\x10ValueShiftOffset\x12\'\n\x05index\x18\x01 \x01(\x0b\x32\x18.recording.EndpointIndex\x12\r\n\x05value\x18\x02 \x01(\x05"F\n\x0c\x41verageShift\x12\'\n\x05index\x18\x01 \x01(\x0b\x32\x18.recording.EndpointIndex\x12\r\n\x05value\x18\x02 \x01(\r"C\n\tFrequency\x12\'\n\x05index\x18\x01 \x01(\x0b\x32\x18.recording.EndpointIndex\x12\r\n\x05value\x18\x02 \x01(\x01"E\n\x0bPhaseOffset\x12\'\n\x05index\x18\x01 \x01(\x0b\x32\x18.recording.EndpointIndex\x12\r\n\x05value\x18\x02 \x01(\x01"H\n\x0eReferenceDelay\x12\'\n\x05index\x18\x01 \x01(\x0b\x32\x18.recording.EndpointIndex\x12\r\n\x05value\x18\x02 \x01(\x01"k\n\x0bStateConfig\x12\'\n\x05index\x18\x01 \x01(\x0b\x32\x18.recording.EndpointIndex\x12\x10\n\x08value_ai\x18\x02 \x01(\x05\x12\x10\n\x08value_aq\x18\x03 \x01(\x05\x12\x0f\n\x07value_b\x18\x04 \x01(\x05",\n\x08IQResult\x12\x0f\n\x07i_value\x18\x01 \x01(\x05\x12\x0f\n\x07q_value\x18\x02 \x01(\x05"C\n\nMemorySize\x12\'\n\x05index\x18\x01 \x01(\x0b\x32\x18.recording.EndpointIndex\x12\x0c\n\x04size\x18\x02 \x01(\r"t\n\x0cMemoryStatus\x12\'\n\x05index\x18\x01 \x01(\x0b\x32\x18.recording.EndpointIndex\x12\x0c\n\x04size\x18\x02 \x01(\r\x12\r\n\x05\x65mpty\x18\x03 \x01(\x08\x12\x0c\n\x04\x66ull\x18\x04 \x01(\x08\x12\x10\n\x08overflow\x18\x05 \x01(\x08"2\n\x0cResultMemory\x12\x10\n\x08result_i\x18\x01 \x03(\x05\x12\x10\n\x08result_q\x18\x02 \x03(\x05")\n\tRawMemory\x12\r\n\x05raw_i\x18\x01 \x03(\x05\x12\r\n\x05raw_q\x18\x02 \x03(\x05"m\n\x12\x43onditioningMatrix\x12\'\n\x05index\x18\x01 \x01(\x0b\x32\x18.recording.EndpointIndex\x12\n\n\x02ii\x18\x02 \x01(\x01\x12\n\n\x02iq\x18\x03 \x01(\x01\x12\n\n\x02qi\x18\x04 \x01(\x01\x12\n\n\x02qq\x18\x05 \x01(\x01"S\n\x12\x43onditioningOffset\x12\'\n\x05index\x18\x01 \x01(\x0b\x32\x18.recording.EndpointIndex\x12\t\n\x01i\x18\x02 \x01(\x05\x12\t\n\x01q\x18\x03 \x01(\x05"\x07\n\x05\x45mpty2\xe2\x16\n\tRecording\x12\x35\n\x05Reset\x12\x18.recording.EndpointIndex\x1a\x10.recording.Empty"\x00\x12\x43\n\x0cReportStatus\x12\x18.recording.EndpointIndex\x1a\x17.recording.StatusReport"\x00\x12;\n\x0bResetStatus\x12\x18.recording.EndpointIndex\x1a\x10.recording.Empty"\x00\x12\x36\n\x0eResetStatusAll\x12\x10.recording.Empty\x1a\x10.recording.Empty"\x00\x12Q\n\x14IsInterferometerMode\x12\x18.recording.EndpointIndex\x1a\x1d.recording.InterferometerMode"\x00\x12J\n\x15SetInterferometerMode\x12\x1d.recording.InterferometerMode\x1a\x10.recording.Empty"\x00\x12I\n\x10IsContinuousMode\x12\x18.recording.EndpointIndex\x1a\x19.recording.ContinuousMode"\x00\x12\x42\n\x11SetContinuousMode\x12\x19.recording.ContinuousMode\x1a\x10.recording.Empty"\x00\x12@\n\x0eGetLastTrigger\x12\x18.recording.EndpointIndex\x1a\x12.recording.Trigger"\x00\x12\x39\n\x0fTriggerManually\x12\x12.recording.Trigger\x1a\x10.recording.Empty"\x00\x12H\n\x10GetTriggerOffset\x12\x18.recording.EndpointIndex\x1a\x18.recording.TriggerOffset"\x00\x12@\n\x10SetTriggerOffset\x12\x18.recording.TriggerOffset\x1a\x10.recording.Empty"\x00\x12P\n\x14GetRecordingDuration\x12\x18.recording.EndpointIndex\x1a\x1c.recording.RecordingDuration"\x00\x12H\n\x14SetRecordingDuration\x12\x1c.recording.RecordingDuration\x1a\x10.recording.Empty"\x00\x12\x42\n\rGetValueShift\x12\x18.recording.EndpointIndex\x1a\x15.recording.ValueShift"\x00\x12:\n\rSetValueShift\x12\x15.recording.ValueShift\x1a\x10.recording.Empty"\x00\x12I\n\x14GetValueShiftInitial\x12\x18.recording.EndpointIndex\x1a\x15.recording.ValueShift"\x00\x12N\n\x13GetValueShiftOffset\x12\x18.recording.EndpointIndex\x1a\x1b.recording.ValueShiftOffset"\x00\x12\x46\n\x13SetValueShiftOffset\x12\x1b.recording.ValueShiftOffset\x1a\x10.recording.Empty"\x00\x12\x46\n\x0fGetAverageShift\x12\x18.recording.EndpointIndex\x1a\x17.recording.AverageShift"\x00\x12>\n\x0fSetAverageShift\x12\x17.recording.AverageShift\x1a\x10.recording.Empty"\x00\x12R\n\x15GetConditioningMatrix\x12\x18.recording.EndpointIndex\x1a\x1d.recording.ConditioningMatrix"\x00\x12J\n\x15SetConditioningMatrix\x12\x1d.recording.ConditioningMatrix\x1a\x10.recording.Empty"\x00\x12R\n\x15GetConditioningOffset\x12\x18.recording.EndpointIndex\x1a\x1d.recording.ConditioningOffset"\x00\x12J\n\x15SetConditioningOffset\x12\x1d.recording.ConditioningOffset\x1a\x10.recording.Empty"\x00\x12H\n\x14GetInternalFrequency\x12\x18.recording.EndpointIndex\x1a\x14.recording.Frequency"\x00\x12@\n\x14SetInternalFrequency\x12\x14.recording.Frequency\x1a\x10.recording.Empty"\x00\x12L\n\x16GetInternalPhaseOffset\x12\x18.recording.EndpointIndex\x1a\x16.recording.PhaseOffset"\x00\x12\x44\n\x16SetInternalPhaseOffset\x12\x16.recording.PhaseOffset\x1a\x10.recording.Empty"\x00\x12I\n\x15GetReferenceFrequency\x12\x18.recording.EndpointIndex\x1a\x14.recording.Frequency"\x00\x12\x41\n\x15SetReferenceFrequency\x12\x14.recording.Frequency\x1a\x10.recording.Empty"\x00\x12J\n\x11GetReferenceDelay\x12\x18.recording.EndpointIndex\x1a\x19.recording.ReferenceDelay"\x00\x12\x42\n\x11SetReferenceDelay\x12\x19.recording.ReferenceDelay\x1a\x10.recording.Empty"\x00\x12\x44\n\x0eGetStateConfig\x12\x18.recording.EndpointIndex\x1a\x16.recording.StateConfig"\x00\x12<\n\x0eSetStateConfig\x12\x16.recording.StateConfig\x1a\x10.recording.Empty"\x00\x12\x44\n\x11GetAveragedResult\x12\x18.recording.EndpointIndex\x1a\x13.recording.IQResult"\x00\x12\x42\n\x0fGetSingleResult\x12\x18.recording.EndpointIndex\x1a\x13.recording.IQResult"\x00\x12L\n\x15GetResultMemoryStatus\x12\x18.recording.EndpointIndex\x1a\x17.recording.MemoryStatus"\x00\x12H\n\x13GetResultMemorySize\x12\x18.recording.EndpointIndex\x1a\x15.recording.MemorySize"\x00\x12\x43\n\x0fGetResultMemory\x12\x15.recording.MemorySize\x1a\x17.recording.ResultMemory"\x00\x12=\n\x0cGetRawMemory\x12\x15.recording.MemorySize\x1a\x14.recording.RawMemory"\x00\x62\x06proto3'
)


_ENDPOINTINDEX = DESCRIPTOR.message_types_by_name["EndpointIndex"]
_STATUSREPORT = DESCRIPTOR.message_types_by_name["StatusReport"]
_INTERFEROMETERMODE = DESCRIPTOR.message_types_by_name["InterferometerMode"]
_CONTINUOUSMODE = DESCRIPTOR.message_types_by_name["ContinuousMode"]
_TRIGGER = DESCRIPTOR.message_types_by_name["Trigger"]
_TRIGGEROFFSET = DESCRIPTOR.message_types_by_name["TriggerOffset"]
_RECORDINGDURATION = DESCRIPTOR.message_types_by_name["RecordingDuration"]
_VALUESHIFT = DESCRIPTOR.message_types_by_name["ValueShift"]
_VALUESHIFTOFFSET = DESCRIPTOR.message_types_by_name["ValueShiftOffset"]
_AVERAGESHIFT = DESCRIPTOR.message_types_by_name["AverageShift"]
_FREQUENCY = DESCRIPTOR.message_types_by_name["Frequency"]
_PHASEOFFSET = DESCRIPTOR.message_types_by_name["PhaseOffset"]
_REFERENCEDELAY = DESCRIPTOR.message_types_by_name["ReferenceDelay"]
_STATECONFIG = DESCRIPTOR.message_types_by_name["StateConfig"]
_IQRESULT = DESCRIPTOR.message_types_by_name["IQResult"]
_MEMORYSIZE = DESCRIPTOR.message_types_by_name["MemorySize"]
_MEMORYSTATUS = DESCRIPTOR.message_types_by_name["MemoryStatus"]
_RESULTMEMORY = DESCRIPTOR.message_types_by_name["ResultMemory"]
_RAWMEMORY = DESCRIPTOR.message_types_by_name["RawMemory"]
_CONDITIONINGMATRIX = DESCRIPTOR.message_types_by_name["ConditioningMatrix"]
_CONDITIONINGOFFSET = DESCRIPTOR.message_types_by_name["ConditioningOffset"]
_EMPTY = DESCRIPTOR.message_types_by_name["Empty"]
_TRIGGER_TRIGGERVALUE = _TRIGGER.enum_types_by_name["TriggerValue"]
EndpointIndex = _reflection.GeneratedProtocolMessageType(
    "EndpointIndex",
    (_message.Message,),
    {
        "DESCRIPTOR": _ENDPOINTINDEX,
        "__module__": "recording_pb2"
        # @@protoc_insertion_point(class_scope:recording.EndpointIndex)
    },
)
_sym_db.RegisterMessage(EndpointIndex)

StatusReport = _reflection.GeneratedProtocolMessageType(
    "StatusReport",
    (_message.Message,),
    {
        "DESCRIPTOR": _STATUSREPORT,
        "__module__": "recording_pb2"
        # @@protoc_insertion_point(class_scope:recording.StatusReport)
    },
)
_sym_db.RegisterMessage(StatusReport)

InterferometerMode = _reflection.GeneratedProtocolMessageType(
    "InterferometerMode",
    (_message.Message,),
    {
        "DESCRIPTOR": _INTERFEROMETERMODE,
        "__module__": "recording_pb2"
        # @@protoc_insertion_point(class_scope:recording.InterferometerMode)
    },
)
_sym_db.RegisterMessage(InterferometerMode)

ContinuousMode = _reflection.GeneratedProtocolMessageType(
    "ContinuousMode",
    (_message.Message,),
    {
        "DESCRIPTOR": _CONTINUOUSMODE,
        "__module__": "recording_pb2"
        # @@protoc_insertion_point(class_scope:recording.ContinuousMode)
    },
)
_sym_db.RegisterMessage(ContinuousMode)

Trigger = _reflection.GeneratedProtocolMessageType(
    "Trigger",
    (_message.Message,),
    {
        "DESCRIPTOR": _TRIGGER,
        "__module__": "recording_pb2"
        # @@protoc_insertion_point(class_scope:recording.Trigger)
    },
)
_sym_db.RegisterMessage(Trigger)

TriggerOffset = _reflection.GeneratedProtocolMessageType(
    "TriggerOffset",
    (_message.Message,),
    {
        "DESCRIPTOR": _TRIGGEROFFSET,
        "__module__": "recording_pb2"
        # @@protoc_insertion_point(class_scope:recording.TriggerOffset)
    },
)
_sym_db.RegisterMessage(TriggerOffset)

RecordingDuration = _reflection.GeneratedProtocolMessageType(
    "RecordingDuration",
    (_message.Message,),
    {
        "DESCRIPTOR": _RECORDINGDURATION,
        "__module__": "recording_pb2"
        # @@protoc_insertion_point(class_scope:recording.RecordingDuration)
    },
)
_sym_db.RegisterMessage(RecordingDuration)

ValueShift = _reflection.GeneratedProtocolMessageType(
    "ValueShift",
    (_message.Message,),
    {
        "DESCRIPTOR": _VALUESHIFT,
        "__module__": "recording_pb2"
        # @@protoc_insertion_point(class_scope:recording.ValueShift)
    },
)
_sym_db.RegisterMessage(ValueShift)

ValueShiftOffset = _reflection.GeneratedProtocolMessageType(
    "ValueShiftOffset",
    (_message.Message,),
    {
        "DESCRIPTOR": _VALUESHIFTOFFSET,
        "__module__": "recording_pb2"
        # @@protoc_insertion_point(class_scope:recording.ValueShiftOffset)
    },
)
_sym_db.RegisterMessage(ValueShiftOffset)

AverageShift = _reflection.GeneratedProtocolMessageType(
    "AverageShift",
    (_message.Message,),
    {
        "DESCRIPTOR": _AVERAGESHIFT,
        "__module__": "recording_pb2"
        # @@protoc_insertion_point(class_scope:recording.AverageShift)
    },
)
_sym_db.RegisterMessage(AverageShift)

Frequency = _reflection.GeneratedProtocolMessageType(
    "Frequency",
    (_message.Message,),
    {
        "DESCRIPTOR": _FREQUENCY,
        "__module__": "recording_pb2"
        # @@protoc_insertion_point(class_scope:recording.Frequency)
    },
)
_sym_db.RegisterMessage(Frequency)

PhaseOffset = _reflection.GeneratedProtocolMessageType(
    "PhaseOffset",
    (_message.Message,),
    {
        "DESCRIPTOR": _PHASEOFFSET,
        "__module__": "recording_pb2"
        # @@protoc_insertion_point(class_scope:recording.PhaseOffset)
    },
)
_sym_db.RegisterMessage(PhaseOffset)

ReferenceDelay = _reflection.GeneratedProtocolMessageType(
    "ReferenceDelay",
    (_message.Message,),
    {
        "DESCRIPTOR": _REFERENCEDELAY,
        "__module__": "recording_pb2"
        # @@protoc_insertion_point(class_scope:recording.ReferenceDelay)
    },
)
_sym_db.RegisterMessage(ReferenceDelay)

StateConfig = _reflection.GeneratedProtocolMessageType(
    "StateConfig",
    (_message.Message,),
    {
        "DESCRIPTOR": _STATECONFIG,
        "__module__": "recording_pb2"
        # @@protoc_insertion_point(class_scope:recording.StateConfig)
    },
)
_sym_db.RegisterMessage(StateConfig)

IQResult = _reflection.GeneratedProtocolMessageType(
    "IQResult",
    (_message.Message,),
    {
        "DESCRIPTOR": _IQRESULT,
        "__module__": "recording_pb2"
        # @@protoc_insertion_point(class_scope:recording.IQResult)
    },
)
_sym_db.RegisterMessage(IQResult)

MemorySize = _reflection.GeneratedProtocolMessageType(
    "MemorySize",
    (_message.Message,),
    {
        "DESCRIPTOR": _MEMORYSIZE,
        "__module__": "recording_pb2"
        # @@protoc_insertion_point(class_scope:recording.MemorySize)
    },
)
_sym_db.RegisterMessage(MemorySize)

MemoryStatus = _reflection.GeneratedProtocolMessageType(
    "MemoryStatus",
    (_message.Message,),
    {
        "DESCRIPTOR": _MEMORYSTATUS,
        "__module__": "recording_pb2"
        # @@protoc_insertion_point(class_scope:recording.MemoryStatus)
    },
)
_sym_db.RegisterMessage(MemoryStatus)

ResultMemory = _reflection.GeneratedProtocolMessageType(
    "ResultMemory",
    (_message.Message,),
    {
        "DESCRIPTOR": _RESULTMEMORY,
        "__module__": "recording_pb2"
        # @@protoc_insertion_point(class_scope:recording.ResultMemory)
    },
)
_sym_db.RegisterMessage(ResultMemory)

RawMemory = _reflection.GeneratedProtocolMessageType(
    "RawMemory",
    (_message.Message,),
    {
        "DESCRIPTOR": _RAWMEMORY,
        "__module__": "recording_pb2"
        # @@protoc_insertion_point(class_scope:recording.RawMemory)
    },
)
_sym_db.RegisterMessage(RawMemory)

ConditioningMatrix = _reflection.GeneratedProtocolMessageType(
    "ConditioningMatrix",
    (_message.Message,),
    {
        "DESCRIPTOR": _CONDITIONINGMATRIX,
        "__module__": "recording_pb2"
        # @@protoc_insertion_point(class_scope:recording.ConditioningMatrix)
    },
)
_sym_db.RegisterMessage(ConditioningMatrix)

ConditioningOffset = _reflection.GeneratedProtocolMessageType(
    "ConditioningOffset",
    (_message.Message,),
    {
        "DESCRIPTOR": _CONDITIONINGOFFSET,
        "__module__": "recording_pb2"
        # @@protoc_insertion_point(class_scope:recording.ConditioningOffset)
    },
)
_sym_db.RegisterMessage(ConditioningOffset)

Empty = _reflection.GeneratedProtocolMessageType(
    "Empty",
    (_message.Message,),
    {
        "DESCRIPTOR": _EMPTY,
        "__module__": "recording_pb2"
        # @@protoc_insertion_point(class_scope:recording.Empty)
    },
)
_sym_db.RegisterMessage(Empty)

_RECORDING = DESCRIPTOR.services_by_name["Recording"]
if _descriptor._USE_C_DESCRIPTORS == False:

    DESCRIPTOR._options = None
    _ENDPOINTINDEX._serialized_start = 30
    _ENDPOINTINDEX._serialized_end = 60
    _STATUSREPORT._serialized_start = 62
    _STATUSREPORT._serialized_end = 109
    _INTERFEROMETERMODE._serialized_start = 111
    _INTERFEROMETERMODE._serialized_end = 199
    _CONTINUOUSMODE._serialized_start = 201
    _CONTINUOUSMODE._serialized_end = 281
    _TRIGGER._serialized_start = 284
    _TRIGGER._serialized_end = 501
    _TRIGGER_TRIGGERVALUE._serialized_start = 384
    _TRIGGER_TRIGGERVALUE._serialized_end = 501
    _TRIGGEROFFSET._serialized_start = 503
    _TRIGGEROFFSET._serialized_end = 574
    _RECORDINGDURATION._serialized_start = 576
    _RECORDINGDURATION._serialized_end = 651
    _VALUESHIFT._serialized_start = 653
    _VALUESHIFT._serialized_end = 721
    _VALUESHIFTOFFSET._serialized_start = 723
    _VALUESHIFTOFFSET._serialized_end = 797
    _AVERAGESHIFT._serialized_start = 799
    _AVERAGESHIFT._serialized_end = 869
    _FREQUENCY._serialized_start = 871
    _FREQUENCY._serialized_end = 938
    _PHASEOFFSET._serialized_start = 940
    _PHASEOFFSET._serialized_end = 1009
    _REFERENCEDELAY._serialized_start = 1011
    _REFERENCEDELAY._serialized_end = 1083
    _STATECONFIG._serialized_start = 1085
    _STATECONFIG._serialized_end = 1192
    _IQRESULT._serialized_start = 1194
    _IQRESULT._serialized_end = 1238
    _MEMORYSIZE._serialized_start = 1240
    _MEMORYSIZE._serialized_end = 1307
    _MEMORYSTATUS._serialized_start = 1309
    _MEMORYSTATUS._serialized_end = 1425
    _RESULTMEMORY._serialized_start = 1427
    _RESULTMEMORY._serialized_end = 1477
    _RAWMEMORY._serialized_start = 1479
    _RAWMEMORY._serialized_end = 1520
    _CONDITIONINGMATRIX._serialized_start = 1522
    _CONDITIONINGMATRIX._serialized_end = 1631
    _CONDITIONINGOFFSET._serialized_start = 1633
    _CONDITIONINGOFFSET._serialized_end = 1716
    _EMPTY._serialized_start = 1718
    _EMPTY._serialized_end = 1725
    _RECORDING._serialized_start = 1728
    _RECORDING._serialized_end = 4642
# @@protoc_insertion_point(module_scope)