from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Report(_message.Message):
    __slots__ = ("source", "score", "report_count", "reporter_count", "last_reported_date", "categories")
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    REPORT_COUNT_FIELD_NUMBER: _ClassVar[int]
    REPORTER_COUNT_FIELD_NUMBER: _ClassVar[int]
    LAST_REPORTED_DATE_FIELD_NUMBER: _ClassVar[int]
    CATEGORIES_FIELD_NUMBER: _ClassVar[int]
    source: str
    score: int
    report_count: int
    reporter_count: int
    last_reported_date: str
    categories: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, source: _Optional[str] = ..., score: _Optional[int] = ..., report_count: _Optional[int] = ..., reporter_count: _Optional[int] = ..., last_reported_date: _Optional[str] = ..., categories: _Optional[_Iterable[str]] = ...) -> None: ...

class Message(_message.Message):
    __slots__ = ("host", "mask", "version", "reports")
    HOST_FIELD_NUMBER: _ClassVar[int]
    MASK_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    REPORTS_FIELD_NUMBER: _ClassVar[int]
    host: str
    mask: str
    version: int
    reports: _containers.RepeatedCompositeFieldContainer[Report]
    def __init__(self, host: _Optional[str] = ..., mask: _Optional[str] = ..., version: _Optional[int] = ..., reports: _Optional[_Iterable[_Union[Report, _Mapping]]] = ...) -> None: ...
