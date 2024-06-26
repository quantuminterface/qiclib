# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: pimc.proto
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
    b'\n\npimc.proto\x12\x04pimc\x1a\x0f\x64\x61tatypes.proto"N\n\tBoardInfo\x12\x0e\n\x06\x63oreId\x18\x01 \x01(\r\x12\x1e\n\x07project\x18\x02 \x01(\x0b\x32\r.pimc.Project\x12\x11\n\tbuildTime\x18\x03 \x01(\t"G\n\x07Project\x12\x11\n\tprojectId\x18\x01 \x01(\r\x12\x12\n\nplatformId\x18\x02 \x01(\r\x12\x15\n\rbuildRevision\x18\x03 \x01(\r";\n\nPIMCStatus\x12\x10\n\x08rst_done\x18\x01 \x01(\x08\x12\r\n\x05ready\x18\x02 \x01(\x08\x12\x0c\n\x04\x62usy\x18\x03 \x01(\x08"\xbc\x01\n\x04Info\x12\x0e\n\x06pimcId\x18\x01 \x01(\r\x12\x13\n\x0bpimcVersion\x18\x02 \x01(\r\x12\x11\n\tprojectId\x18\x03 \x01(\r\x12\x12\n\nplatformId\x18\x04 \x01(\r\x12\x15\n\rbuildRevision\x18\x05 \x01(\r\x12\x11\n\tbuildTime\x18\x06 \x01(\t\x12\x13\n\x0bprojectName\x18\x07 \x01(\t\x12\x14\n\x0cplatformName\x18\x08 \x01(\t\x12\x13\n\x0b\x62uildCommit\x18\t \x01(\t2\xc4\t\n\x0bPIMCService\x12\x38\n\x08SetReset\x12\x14.sdr.datatypes.Empty\x1a\x14.sdr.datatypes.Empty"\x00\x12\x36\n\x07GetBusy\x12\x14.sdr.datatypes.Empty\x1a\x13.sdr.datatypes.Bool"\x00\x12\x37\n\x08GetReady\x12\x14.sdr.datatypes.Empty\x1a\x13.sdr.datatypes.Bool"\x00\x12:\n\nSetSWReady\x12\x14.sdr.datatypes.Empty\x1a\x14.sdr.datatypes.Empty"\x00\x12\x39\n\nGetSWReady\x12\x14.sdr.datatypes.Empty\x1a\x13.sdr.datatypes.Bool"\x00\x12<\n\x0cSetResetDone\x12\x14.sdr.datatypes.Empty\x1a\x14.sdr.datatypes.Empty"\x00\x12;\n\x0cGetResetDone\x12\x14.sdr.datatypes.Empty\x1a\x13.sdr.datatypes.Bool"\x00\x12=\n\x0eGetChipVersion\x12\x14.sdr.datatypes.Empty\x1a\x13.sdr.datatypes.UInt"\x00\x12\x43\n\x14GetModuleChipVersion\x12\x14.sdr.datatypes.Empty\x1a\x13.sdr.datatypes.UInt"\x00\x12-\n\x07GetInfo\x12\x14.sdr.datatypes.Empty\x1a\n.pimc.Info"\x00\x12>\n\rGetInfoString\x12\x14.sdr.datatypes.Empty\x1a\x15.sdr.datatypes.String"\x00\x12@\n\x11GetAllClocksValid\x12\x14.sdr.datatypes.Empty\x1a\x13.sdr.datatypes.Bool"\x00\x12>\n\rGetClocksInfo\x12\x14.sdr.datatypes.Empty\x1a\x15.sdr.datatypes.String"\x00\x12@\n\x0fGetStatusInputs\x12\x14.sdr.datatypes.Empty\x1a\x15.sdr.datatypes.String"\x00\x12=\n\x0cGetReadyMask\x12\x14.sdr.datatypes.Empty\x1a\x15.sdr.datatypes.String"\x00\x12>\n\rGetReadyState\x12\x14.sdr.datatypes.Empty\x1a\x15.sdr.datatypes.String"\x00\x12\x35\n\tGetStatus\x12\x14.sdr.datatypes.Empty\x1a\x10.pimc.PIMCStatus"\x00\x12\x33\n\nGetProject\x12\x14.sdr.datatypes.Empty\x1a\r.pimc.Project"\x00\x12=\n\x0cGetBuildTime\x12\x14.sdr.datatypes.Empty\x1a\x15.sdr.datatypes.String"\x00\x12\x37\n\x0cGetBoardInfo\x12\x14.sdr.datatypes.Empty\x1a\x0f.pimc.BoardInfo"\x00\x62\x06proto3'
)


_BOARDINFO = DESCRIPTOR.message_types_by_name["BoardInfo"]
_PROJECT = DESCRIPTOR.message_types_by_name["Project"]
_PIMCSTATUS = DESCRIPTOR.message_types_by_name["PIMCStatus"]
_INFO = DESCRIPTOR.message_types_by_name["Info"]
BoardInfo = _reflection.GeneratedProtocolMessageType(
    "BoardInfo",
    (_message.Message,),
    {
        "DESCRIPTOR": _BOARDINFO,
        "__module__": "pimc_pb2"
        # @@protoc_insertion_point(class_scope:pimc.BoardInfo)
    },
)
_sym_db.RegisterMessage(BoardInfo)

Project = _reflection.GeneratedProtocolMessageType(
    "Project",
    (_message.Message,),
    {
        "DESCRIPTOR": _PROJECT,
        "__module__": "pimc_pb2"
        # @@protoc_insertion_point(class_scope:pimc.Project)
    },
)
_sym_db.RegisterMessage(Project)

PIMCStatus = _reflection.GeneratedProtocolMessageType(
    "PIMCStatus",
    (_message.Message,),
    {
        "DESCRIPTOR": _PIMCSTATUS,
        "__module__": "pimc_pb2"
        # @@protoc_insertion_point(class_scope:pimc.PIMCStatus)
    },
)
_sym_db.RegisterMessage(PIMCStatus)

Info = _reflection.GeneratedProtocolMessageType(
    "Info",
    (_message.Message,),
    {
        "DESCRIPTOR": _INFO,
        "__module__": "pimc_pb2"
        # @@protoc_insertion_point(class_scope:pimc.Info)
    },
)
_sym_db.RegisterMessage(Info)

_PIMCSERVICE = DESCRIPTOR.services_by_name["PIMCService"]
if _descriptor._USE_C_DESCRIPTORS == False:

    DESCRIPTOR._options = None
    _BOARDINFO._serialized_start = 37
    _BOARDINFO._serialized_end = 115
    _PROJECT._serialized_start = 117
    _PROJECT._serialized_end = 188
    _PIMCSTATUS._serialized_start = 190
    _PIMCSTATUS._serialized_end = 249
    _INFO._serialized_start = 252
    _INFO._serialized_end = 440
    _PIMCSERVICE._serialized_start = 443
    _PIMCSERVICE._serialized_end = 1663
# @@protoc_insertion_point(module_scope)
