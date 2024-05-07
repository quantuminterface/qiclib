# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: rfdc.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import qiclib.packages.grpc.datatypes_pb2 as datatypes__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\nrfdc.proto\x12\x04rfdc\x1a\x0f\x64\x61tatypes.proto"Z\n\x0e\x43onverterIndex\x12\x0c\n\x04tile\x18\x01 \x01(\r\x12\r\n\x05\x62lock\x18\x02 \x01(\r\x12+\n\x0e\x63onverter_type\x18\x03 \x01(\x0e\x32\x13.rfdc.ConverterType"F\n\tTileIndex\x12\x0c\n\x04tile\x18\x01 \x01(\r\x12+\n\x0e\x63onverter_type\x18\x02 \x01(\x0e\x32\x13.rfdc.ConverterType"\x97\x01\n\x0b\x42lockStatus\x12\x11\n\tfrequency\x18\x01 \x01(\x01\x12\x14\n\x0c\x61nalogstatus\x18\x02 \x01(\r\x12\x15\n\rdigitalstatus\x18\x03 \x01(\r\x12\x13\n\x0b\x63lockstatus\x18\x04 \x01(\r\x12\x18\n\x10\x66ifoflagsenabled\x18\x05 \x01(\r\x12\x19\n\x11\x66ifoflagsasserted\x18\x06 \x01(\r"?\n\tFrequency\x12#\n\x05index\x18\x01 \x01(\x0b\x32\x14.rfdc.ConverterIndex\x12\r\n\x05value\x18\x02 \x01(\x01"A\n\x0bNyquistZone\x12#\n\x05index\x18\x01 \x01(\x0b\x32\x14.rfdc.ConverterIndex\x12\r\n\x05value\x18\x02 \x01(\r"W\n\nInvSincFIR\x12#\n\x05index\x18\x01 \x01(\x0b\x32\x14.rfdc.ConverterIndex\x12$\n\x05value\x18\x02 \x01(\x0e\x32\x15.rfdc.InvSincFIR_Enum"K\n\x11ThresholdToUpdate\x12#\n\x05index\x18\x01 \x01(\x0b\x32\x14.rfdc.ConverterIndex\x12\x11\n\tthreshold\x18\x02 \x01(\r"J\n\x11InterruptSettings\x12#\n\x05index\x18\x01 \x01(\x0b\x32\x14.rfdc.ConverterIndex\x12\x10\n\x08intrmask\x18\x02 \x01(\r";\n\x05Phase\x12#\n\x05index\x18\x01 \x01(\x0b\x32\x14.rfdc.ConverterIndex\x12\r\n\x05value\x18\x02 \x01(\x01"f\n\rMixerSettings\x12#\n\x05index\x18\x01 \x01(\x0b\x32\x14.rfdc.ConverterIndex\x12\x1d\n\x04mode\x18\x02 \x01(\x0e\x32\x0f.rfdc.MixerMode\x12\x11\n\tfrequency\x18\x03 \x01(\x01"%\n\x04Mode\x12\x1d\n\x04mode\x18\x01 \x01(\x0e\x32\x0f.rfdc.MixerMode".\n\x08\x44\x61taType\x12"\n\x05value\x18\x01 \x01(\x0e\x32\x13.rfdc.DataType_Enum"D\n\rInterpolation\x12#\n\x05index\x18\x01 \x01(\x0b\x32\x14.rfdc.ConverterIndex\x12\x0e\n\x06\x66\x61\x63tor\x18\x02 \x01(\r"A\n\nDecimation\x12#\n\x05index\x18\x01 \x01(\x0b\x32\x14.rfdc.ConverterIndex\x12\x0e\n\x06\x66\x61\x63tor\x18\x02 \x01(\r"\x8b\x01\n\x0cStatusReport\x12\x0f\n\x07\x66\x61ilure\x18\x01 \x01(\x08\x12\x0e\n\x06report\x18\x02 \x01(\t\x12+\n\radc_overrange\x18\x03 \x03(\x0b\x32\x14.rfdc.ConverterIndex\x12-\n\x0f\x61\x64\x63_overvoltage\x18\x04 \x03(\x0b\x32\x14.rfdc.ConverterIndex*!\n\rConverterType\x12\x07\n\x03\x41\x44\x43\x10\x00\x12\x07\n\x03\x44\x41\x43\x10\x01*F\n\x0fInvSincFIR_Enum\x12\x0c\n\x08\x44ISABLED\x10\x00\x12\x11\n\rFIRST_NYQUIST\x10\x01\x12\x12\n\x0eSECOND_NYQUIST\x10\x02*V\n\tMixerMode\x12\x07\n\x03OFF\x10\x00\x12\x16\n\x12\x43OMPLEX_TO_COMPLEX\x10\x01\x12\x13\n\x0f\x43OMPLEX_TO_REAL\x10\x02\x12\x13\n\x0fREAL_TO_COMPLEX\x10\x03*!\n\rDataType_Enum\x12\x08\n\x04REAL\x10\x00\x12\x06\n\x02IQ\x10\x01\x32\xa3\x0b\n\x0bRFdcService\x12;\n\x0eGetBlockStatus\x12\x14.rfdc.ConverterIndex\x1a\x11.rfdc.BlockStatus"\x00\x12<\n\x11GetMixerFrequency\x12\x14.rfdc.ConverterIndex\x1a\x0f.rfdc.Frequency"\x00\x12<\n\x11SetMixerFrequency\x12\x0f.rfdc.Frequency\x1a\x14.sdr.datatypes.Empty"\x00\x12/\n\x08GetPhase\x12\x14.rfdc.ConverterIndex\x1a\x0b.rfdc.Phase"\x00\x12/\n\x08SetPhase\x12\x0b.rfdc.Phase\x1a\x14.sdr.datatypes.Empty"\x00\x12\x32\n\x0cGetMixerMode\x12\x14.rfdc.ConverterIndex\x1a\n.rfdc.Mode"\x00\x12?\n\x10SetMixerSettings\x12\x13.rfdc.MixerSettings\x1a\x14.sdr.datatypes.Empty"\x00\x12\x35\n\x0bGetDataType\x12\x14.rfdc.ConverterIndex\x1a\x0e.rfdc.DataType"\x00\x12?\n\x10GetInterpolation\x12\x14.rfdc.ConverterIndex\x1a\x13.rfdc.Interpolation"\x00\x12?\n\x10SetInterpolation\x12\x13.rfdc.Interpolation\x1a\x14.sdr.datatypes.Empty"\x00\x12\x39\n\rGetDecimation\x12\x14.rfdc.ConverterIndex\x1a\x10.rfdc.Decimation"\x00\x12\x39\n\rSetDecimation\x12\x10.rfdc.Decimation\x1a\x14.sdr.datatypes.Empty"\x00\x12\x39\n\rGetInvSincFIR\x12\x14.rfdc.ConverterIndex\x1a\x10.rfdc.InvSincFIR"\x00\x12\x39\n\rSetInvSincFIR\x12\x10.rfdc.InvSincFIR\x1a\x14.sdr.datatypes.Empty"\x00\x12J\n\x17SetThresholdStickyClear\x12\x17.rfdc.ThresholdToUpdate\x1a\x14.sdr.datatypes.Empty"\x00\x12\x32\n\x07StartUp\x12\x0f.rfdc.TileIndex\x1a\x14.sdr.datatypes.Empty"\x00\x12\x33\n\x08Shutdown\x12\x0f.rfdc.TileIndex\x1a\x14.sdr.datatypes.Empty"\x00\x12\x30\n\x05Reset\x12\x0f.rfdc.TileIndex\x1a\x14.sdr.datatypes.Empty"\x00\x12>\n\x0eInterruptClear\x12\x14.rfdc.ConverterIndex\x1a\x14.sdr.datatypes.Empty"\x00\x12\x45\n\x12GetInterruptStatus\x12\x14.rfdc.ConverterIndex\x1a\x17.rfdc.InterruptSettings"\x00\x12;\n\x0eGetNyquistZone\x12\x14.rfdc.ConverterIndex\x1a\x11.rfdc.NyquistZone"\x00\x12;\n\x0eSetNyquistZone\x12\x11.rfdc.NyquistZone\x1a\x14.sdr.datatypes.Empty"\x00\x12:\n\x0cReportStatus\x12\x14.sdr.datatypes.Empty\x1a\x12.rfdc.StatusReport"\x00\x12;\n\x0bResetStatus\x12\x14.sdr.datatypes.Empty\x1a\x14.sdr.datatypes.Empty"\x00\x62\x06proto3'
)

_CONVERTERTYPE = DESCRIPTOR.enum_types_by_name["ConverterType"]
ConverterType = enum_type_wrapper.EnumTypeWrapper(_CONVERTERTYPE)
_INVSINCFIR_ENUM = DESCRIPTOR.enum_types_by_name["InvSincFIR_Enum"]
InvSincFIR_Enum = enum_type_wrapper.EnumTypeWrapper(_INVSINCFIR_ENUM)
_MIXERMODE = DESCRIPTOR.enum_types_by_name["MixerMode"]
MixerMode = enum_type_wrapper.EnumTypeWrapper(_MIXERMODE)
_DATATYPE_ENUM = DESCRIPTOR.enum_types_by_name["DataType_Enum"]
DataType_Enum = enum_type_wrapper.EnumTypeWrapper(_DATATYPE_ENUM)
ADC = 0
DAC = 1
DISABLED = 0
FIRST_NYQUIST = 1
SECOND_NYQUIST = 2
OFF = 0
COMPLEX_TO_COMPLEX = 1
COMPLEX_TO_REAL = 2
REAL_TO_COMPLEX = 3
REAL = 0
IQ = 1


_CONVERTERINDEX = DESCRIPTOR.message_types_by_name["ConverterIndex"]
_TILEINDEX = DESCRIPTOR.message_types_by_name["TileIndex"]
_BLOCKSTATUS = DESCRIPTOR.message_types_by_name["BlockStatus"]
_FREQUENCY = DESCRIPTOR.message_types_by_name["Frequency"]
_NYQUISTZONE = DESCRIPTOR.message_types_by_name["NyquistZone"]
_INVSINCFIR = DESCRIPTOR.message_types_by_name["InvSincFIR"]
_THRESHOLDTOUPDATE = DESCRIPTOR.message_types_by_name["ThresholdToUpdate"]
_INTERRUPTSETTINGS = DESCRIPTOR.message_types_by_name["InterruptSettings"]
_PHASE = DESCRIPTOR.message_types_by_name["Phase"]
_MIXERSETTINGS = DESCRIPTOR.message_types_by_name["MixerSettings"]
_MODE = DESCRIPTOR.message_types_by_name["Mode"]
_DATATYPE = DESCRIPTOR.message_types_by_name["DataType"]
_INTERPOLATION = DESCRIPTOR.message_types_by_name["Interpolation"]
_DECIMATION = DESCRIPTOR.message_types_by_name["Decimation"]
_STATUSREPORT = DESCRIPTOR.message_types_by_name["StatusReport"]
ConverterIndex = _reflection.GeneratedProtocolMessageType(
    "ConverterIndex",
    (_message.Message,),
    {
        "DESCRIPTOR": _CONVERTERINDEX,
        "__module__": "rfdc_pb2"
        # @@protoc_insertion_point(class_scope:rfdc.ConverterIndex)
    },
)
_sym_db.RegisterMessage(ConverterIndex)

TileIndex = _reflection.GeneratedProtocolMessageType(
    "TileIndex",
    (_message.Message,),
    {
        "DESCRIPTOR": _TILEINDEX,
        "__module__": "rfdc_pb2"
        # @@protoc_insertion_point(class_scope:rfdc.TileIndex)
    },
)
_sym_db.RegisterMessage(TileIndex)

BlockStatus = _reflection.GeneratedProtocolMessageType(
    "BlockStatus",
    (_message.Message,),
    {
        "DESCRIPTOR": _BLOCKSTATUS,
        "__module__": "rfdc_pb2"
        # @@protoc_insertion_point(class_scope:rfdc.BlockStatus)
    },
)
_sym_db.RegisterMessage(BlockStatus)

Frequency = _reflection.GeneratedProtocolMessageType(
    "Frequency",
    (_message.Message,),
    {
        "DESCRIPTOR": _FREQUENCY,
        "__module__": "rfdc_pb2"
        # @@protoc_insertion_point(class_scope:rfdc.Frequency)
    },
)
_sym_db.RegisterMessage(Frequency)

NyquistZone = _reflection.GeneratedProtocolMessageType(
    "NyquistZone",
    (_message.Message,),
    {
        "DESCRIPTOR": _NYQUISTZONE,
        "__module__": "rfdc_pb2"
        # @@protoc_insertion_point(class_scope:rfdc.NyquistZone)
    },
)
_sym_db.RegisterMessage(NyquistZone)

InvSincFIR = _reflection.GeneratedProtocolMessageType(
    "InvSincFIR",
    (_message.Message,),
    {
        "DESCRIPTOR": _INVSINCFIR,
        "__module__": "rfdc_pb2"
        # @@protoc_insertion_point(class_scope:rfdc.InvSincFIR)
    },
)
_sym_db.RegisterMessage(InvSincFIR)

ThresholdToUpdate = _reflection.GeneratedProtocolMessageType(
    "ThresholdToUpdate",
    (_message.Message,),
    {
        "DESCRIPTOR": _THRESHOLDTOUPDATE,
        "__module__": "rfdc_pb2"
        # @@protoc_insertion_point(class_scope:rfdc.ThresholdToUpdate)
    },
)
_sym_db.RegisterMessage(ThresholdToUpdate)

InterruptSettings = _reflection.GeneratedProtocolMessageType(
    "InterruptSettings",
    (_message.Message,),
    {
        "DESCRIPTOR": _INTERRUPTSETTINGS,
        "__module__": "rfdc_pb2"
        # @@protoc_insertion_point(class_scope:rfdc.InterruptSettings)
    },
)
_sym_db.RegisterMessage(InterruptSettings)

Phase = _reflection.GeneratedProtocolMessageType(
    "Phase",
    (_message.Message,),
    {
        "DESCRIPTOR": _PHASE,
        "__module__": "rfdc_pb2"
        # @@protoc_insertion_point(class_scope:rfdc.Phase)
    },
)
_sym_db.RegisterMessage(Phase)

MixerSettings = _reflection.GeneratedProtocolMessageType(
    "MixerSettings",
    (_message.Message,),
    {
        "DESCRIPTOR": _MIXERSETTINGS,
        "__module__": "rfdc_pb2"
        # @@protoc_insertion_point(class_scope:rfdc.MixerSettings)
    },
)
_sym_db.RegisterMessage(MixerSettings)

Mode = _reflection.GeneratedProtocolMessageType(
    "Mode",
    (_message.Message,),
    {
        "DESCRIPTOR": _MODE,
        "__module__": "rfdc_pb2"
        # @@protoc_insertion_point(class_scope:rfdc.Mode)
    },
)
_sym_db.RegisterMessage(Mode)

DataType = _reflection.GeneratedProtocolMessageType(
    "DataType",
    (_message.Message,),
    {
        "DESCRIPTOR": _DATATYPE,
        "__module__": "rfdc_pb2"
        # @@protoc_insertion_point(class_scope:rfdc.DataType)
    },
)
_sym_db.RegisterMessage(DataType)

Interpolation = _reflection.GeneratedProtocolMessageType(
    "Interpolation",
    (_message.Message,),
    {
        "DESCRIPTOR": _INTERPOLATION,
        "__module__": "rfdc_pb2"
        # @@protoc_insertion_point(class_scope:rfdc.Interpolation)
    },
)
_sym_db.RegisterMessage(Interpolation)

Decimation = _reflection.GeneratedProtocolMessageType(
    "Decimation",
    (_message.Message,),
    {
        "DESCRIPTOR": _DECIMATION,
        "__module__": "rfdc_pb2"
        # @@protoc_insertion_point(class_scope:rfdc.Decimation)
    },
)
_sym_db.RegisterMessage(Decimation)

StatusReport = _reflection.GeneratedProtocolMessageType(
    "StatusReport",
    (_message.Message,),
    {
        "DESCRIPTOR": _STATUSREPORT,
        "__module__": "rfdc_pb2"
        # @@protoc_insertion_point(class_scope:rfdc.StatusReport)
    },
)
_sym_db.RegisterMessage(StatusReport)

_RFDCSERVICE = DESCRIPTOR.services_by_name["RFdcService"]
if _descriptor._USE_C_DESCRIPTORS == False:

    DESCRIPTOR._options = None
    _CONVERTERTYPE._serialized_start = 1260
    _CONVERTERTYPE._serialized_end = 1293
    _INVSINCFIR_ENUM._serialized_start = 1295
    _INVSINCFIR_ENUM._serialized_end = 1365
    _MIXERMODE._serialized_start = 1367
    _MIXERMODE._serialized_end = 1453
    _DATATYPE_ENUM._serialized_start = 1455
    _DATATYPE_ENUM._serialized_end = 1488
    _CONVERTERINDEX._serialized_start = 37
    _CONVERTERINDEX._serialized_end = 127
    _TILEINDEX._serialized_start = 129
    _TILEINDEX._serialized_end = 199
    _BLOCKSTATUS._serialized_start = 202
    _BLOCKSTATUS._serialized_end = 353
    _FREQUENCY._serialized_start = 355
    _FREQUENCY._serialized_end = 418
    _NYQUISTZONE._serialized_start = 420
    _NYQUISTZONE._serialized_end = 485
    _INVSINCFIR._serialized_start = 487
    _INVSINCFIR._serialized_end = 574
    _THRESHOLDTOUPDATE._serialized_start = 576
    _THRESHOLDTOUPDATE._serialized_end = 651
    _INTERRUPTSETTINGS._serialized_start = 653
    _INTERRUPTSETTINGS._serialized_end = 727
    _PHASE._serialized_start = 729
    _PHASE._serialized_end = 788
    _MIXERSETTINGS._serialized_start = 790
    _MIXERSETTINGS._serialized_end = 892
    _MODE._serialized_start = 894
    _MODE._serialized_end = 931
    _DATATYPE._serialized_start = 933
    _DATATYPE._serialized_end = 979
    _INTERPOLATION._serialized_start = 981
    _INTERPOLATION._serialized_end = 1049
    _DECIMATION._serialized_start = 1051
    _DECIMATION._serialized_end = 1116
    _STATUSREPORT._serialized_start = 1119
    _STATUSREPORT._serialized_end = 1258
    _RFDCSERVICE._serialized_start = 1491
    _RFDCSERVICE._serialized_end = 2934
# @@protoc_insertion_point(module_scope)
