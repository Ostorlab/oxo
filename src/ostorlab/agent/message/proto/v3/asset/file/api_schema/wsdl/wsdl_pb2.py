# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: ostorlab/agent/message/proto/v3/asset/file/api_schema/wsdl/wsdl.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\nEostorlab/agent/message/proto/v3/asset/file/api_schema/wsdl/wsdl.proto\x12:ostorlab.agent.message.proto.v3.asset.file.api_schema.wsdl\"\'\n\x0f\x41ndroidMetadata\x12\x14\n\x0cpackage_name\x18\x01 \x01(\t\" \n\x0bIOSMetadata\x12\x11\n\tbundle_id\x18\x01 \x01(\t\"%\n\x06Header\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t\"\xa5\x03\n\x07Message\x12\x0f\n\x07\x63ontent\x18\x01 \x01(\x0c\x12\x0c\n\x04path\x18\x02 \x01(\t\x12\x13\n\x0b\x63ontent_url\x18\x03 \x01(\t\x12g\n\x10\x61ndroid_metadata\x18\x04 \x01(\x0b\x32K.ostorlab.agent.message.proto.v3.asset.file.api_schema.wsdl.AndroidMetadataH\x00\x12_\n\x0cios_metadata\x18\x05 \x01(\x0b\x32G.ostorlab.agent.message.proto.v3.asset.file.api_schema.wsdl.IOSMetadataH\x00\x12\x14\n\x0c\x65ndpoint_url\x18\x06 \x01(\t\x12\x19\n\x0bschema_type\x18\x07 \x01(\t:\x04wsdl\x12Y\n\rextra_headers\x18\x08 \x03(\x0b\x32\x42.ostorlab.agent.message.proto.v3.asset.file.api_schema.wsdl.HeaderB\x10\n\x0emetadata_oneof')



_ANDROIDMETADATA = DESCRIPTOR.message_types_by_name['AndroidMetadata']
_IOSMETADATA = DESCRIPTOR.message_types_by_name['IOSMetadata']
_HEADER = DESCRIPTOR.message_types_by_name['Header']
_MESSAGE = DESCRIPTOR.message_types_by_name['Message']
AndroidMetadata = _reflection.GeneratedProtocolMessageType('AndroidMetadata', (_message.Message,), {
  'DESCRIPTOR' : _ANDROIDMETADATA,
  '__module__' : 'ostorlab.agent.message.proto.v3.asset.file.api_schema.wsdl.wsdl_pb2'
  # @@protoc_insertion_point(class_scope:ostorlab.agent.message.proto.v3.asset.file.api_schema.wsdl.AndroidMetadata)
  })
_sym_db.RegisterMessage(AndroidMetadata)

IOSMetadata = _reflection.GeneratedProtocolMessageType('IOSMetadata', (_message.Message,), {
  'DESCRIPTOR' : _IOSMETADATA,
  '__module__' : 'ostorlab.agent.message.proto.v3.asset.file.api_schema.wsdl.wsdl_pb2'
  # @@protoc_insertion_point(class_scope:ostorlab.agent.message.proto.v3.asset.file.api_schema.wsdl.IOSMetadata)
  })
_sym_db.RegisterMessage(IOSMetadata)

Header = _reflection.GeneratedProtocolMessageType('Header', (_message.Message,), {
  'DESCRIPTOR' : _HEADER,
  '__module__' : 'ostorlab.agent.message.proto.v3.asset.file.api_schema.wsdl.wsdl_pb2'
  # @@protoc_insertion_point(class_scope:ostorlab.agent.message.proto.v3.asset.file.api_schema.wsdl.Header)
  })
_sym_db.RegisterMessage(Header)

Message = _reflection.GeneratedProtocolMessageType('Message', (_message.Message,), {
  'DESCRIPTOR' : _MESSAGE,
  '__module__' : 'ostorlab.agent.message.proto.v3.asset.file.api_schema.wsdl.wsdl_pb2'
  # @@protoc_insertion_point(class_scope:ostorlab.agent.message.proto.v3.asset.file.api_schema.wsdl.Message)
  })
_sym_db.RegisterMessage(Message)

if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _ANDROIDMETADATA._serialized_start=133
  _ANDROIDMETADATA._serialized_end=172
  _IOSMETADATA._serialized_start=174
  _IOSMETADATA._serialized_end=206
  _HEADER._serialized_start=208
  _HEADER._serialized_end=245
  _MESSAGE._serialized_start=248
  _MESSAGE._serialized_end=669
# @@protoc_insertion_point(module_scope)
