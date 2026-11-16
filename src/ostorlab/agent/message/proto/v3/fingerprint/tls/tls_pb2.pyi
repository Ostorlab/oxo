from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Cipher(_message.Message):
    __slots__ = ("version", "name")
    VERSION_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    version: str
    name: str
    def __init__(self, version: _Optional[str] = ..., name: _Optional[str] = ...) -> None: ...

class Message(_message.Message):
    __slots__ = ("host", "port", "versions", "ciphers")
    HOST_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    VERSIONS_FIELD_NUMBER: _ClassVar[int]
    CIPHERS_FIELD_NUMBER: _ClassVar[int]
    host: str
    port: int
    versions: _containers.RepeatedScalarFieldContainer[str]
    ciphers: _containers.RepeatedCompositeFieldContainer[Cipher]
    def __init__(self, host: _Optional[str] = ..., port: _Optional[int] = ..., versions: _Optional[_Iterable[str]] = ..., ciphers: _Optional[_Iterable[_Union[Cipher, _Mapping]]] = ...) -> None: ...
