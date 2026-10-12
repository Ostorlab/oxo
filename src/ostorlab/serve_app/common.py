"""common utilities for the flask app."""

from __future__ import annotations

import collections
import io
import json
import struct
import zipfile
from functools import cached_property
from math import ceil
from typing import TYPE_CHECKING
from typing import Any
from typing import Generic
from typing import TypeVar
from typing import cast
from typing import overload

import cvss
import graphene
from graphene.types import scalars
from graphql.language import ast
from sqlalchemy import orm

if TYPE_CHECKING:
    ObjectType = graphene.ObjectType[object]
else:
    ObjectType = graphene.ObjectType


class PageInfo(ObjectType):
    """Page info object type."""

    count = graphene.Int()
    num_pages = graphene.Int()
    has_next = graphene.Boolean()
    has_previous = graphene.Boolean()


class SortEnum(graphene.Enum):
    """Sort enum, for the sorting order of the results."""

    Asc = 1
    Desc = 2


class RiskRatingEnum(graphene.Enum):
    """Enum for the risk rating of a scan."""

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    POTENTIALLY = "Potentially"
    HARDENING = "Hardening"
    SECURE = "Secure"
    IMPORTANT = "Important"
    INFO = "Info"


class Bytes(scalars.Scalar):
    """
    The `Bytes` scalar type represents binary data in a bytes format.
    """

    @staticmethod
    def coerce_bytes(
        value: str | bytes | memoryview | list[Any] | float | dict[str, Any] | bool,
    ) -> bytes:
        """Coerce a value to bytes.

        Args:
            value: Value to coerce.

        Returns:
            bytes: Coerced value.
        """
        if isinstance(value, bytes):
            return value
        elif isinstance(value, memoryview):
            return value.tobytes()
        elif isinstance(value, str):
            return Bytes._rawbytes(value)
        elif isinstance(value, list):
            return json.dumps(value).encode(encoding="utf-8")
        elif isinstance(value, (float, int)):
            return struct.pack("d", value)
        elif isinstance(value, dict):
            return json.dumps(value).encode(encoding="utf-8")
        elif isinstance(value, bool):
            return (1 if value is True else 0).to_bytes(1, byteorder="big")
        else:
            raise NotImplementedError(f"Bytes scalar coerce error from {type(value)}")

    serialize = coerce_bytes
    parse_value = coerce_bytes

    @staticmethod
    def parse_literal(asst: ast.Value) -> int | None:
        """Parse a literal value."""
        raise NotImplementedError("ast is not supported")

    @staticmethod
    def _rawbytes(s: str) -> bytes:
        """Convert a string to raw bytes without encoding"""
        outlist = []
        for cp in s:
            num = ord(cp)
            if num <= 255:
                outlist.append(struct.pack("B", num))
            elif num < 65535:
                outlist.append(struct.pack(">H", num))
            else:
                b = (num & 0xFF0000) >> 16
                H = num & 0xFFFF
                outlist.append(struct.pack(">bH", b, H))
        return b"".join(outlist)


def compute_cvss_v3_base_score(vector: str | None) -> float | None:
    """Compute the CVSS v3 base score from the vector.

    Args:
        vector (str | None): CVSS v3 vector.

    Returns:
        CVSS v3 base score or None if the vector is invalid.
    """
    if vector is None:
        return None
    try:
        return cast(float, cvss.CVSS3(vector).scores()[0])
    except cvss.CVSS3Error:
        return None


T = TypeVar("T")


class Page(collections.abc.Sequence[T]):
    """A single page in a paginated list of objects."""

    def __init__(
        self,
        object_list: collections.abc.Sequence[T],
        number: int,
        paginator: Paginator[T],
    ) -> None:
        """
        initialize the page object.
        Args:
            object_list: The list of objects in the page.
            number: page number.
            paginator: paginator object.
        """
        self.object_list = object_list
        self.number = number
        self.paginator = paginator

    def __repr__(self) -> str:
        """Return the string representation of the page object."""
        return f"<Page {self.number} of {self.paginator.num_pages}>"

    def __len__(self) -> int:
        """Return the number of objects in the page."""
        return len(self.object_list)

    @overload
    def __getitem__(self, index: int) -> T: ...

    @overload
    def __getitem__(self, index: slice) -> collections.abc.Sequence[T]: ...

    def __getitem__(self, index: int | slice) -> T | collections.abc.Sequence[T]:
        """Return the object at the given index in the page."""
        if isinstance(index, (int, slice)) is False:
            raise TypeError(
                f"Page indices must be integers or slices, not {type(index).__name__}."
            )
        if isinstance(self.object_list, list) is False:
            self.object_list = list(self.object_list)
        return self.object_list[index]

    def has_next(self) -> bool:
        """Return True if there is a next page."""
        return self.number < self.paginator.num_pages

    def has_previous(self) -> bool:
        """Return True if there is a previous page."""
        return self.number > 1


class Paginator(Generic[T]):
    """A paginator object for paginating a list of objects."""

    def __init__(
        self, object_list: collections.abc.Sequence[T] | orm.Query[T], per_page: int
    ) -> None:
        """Initialize the paginator object.
        Args:
            object_list: The list of objects to paginate.
            per_page: The number of objects per page.
        """
        self.object_list = object_list
        self.per_page = per_page

    @cached_property
    def count(self) -> int:
        """Return the total number of objects, across all pages."""
        if isinstance(self.object_list, orm.Query):
            return self.object_list.count()
        return len(self.object_list)

    @cached_property
    def num_pages(self) -> int:
        """Return the total number of pages."""
        if self.count == 0:
            return 0
        hits = max(1, self.count)
        return ceil(hits / self.per_page)

    def get_page(self, number: int) -> Page[T]:
        """Return a valid page, even if the page argument isn't a number or isn't in range.
        Args:
            number: The page number.
        Returns: The page object.
        """
        return self.page(number)

    def page(self, number: int) -> Page[T]:
        """Return a Page object for the given 1-based page number
        Args:
            number: The page number.

        Returns: The page object.
        """
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        top = min(self.count, top)
        return Page(
            object_list=self.object_list[bottom:top], number=number, paginator=self
        )

    def _get_page(
        self,
        object_list: collections.abc.Sequence[T],
        number: int,
        paginator: Paginator[T],
    ) -> Page[T]:
        """Return an instance of a single page."""
        return Page(object_list, number, paginator)


def is_apk(file_content: bytes) -> bool:
    """Check if a file is an apk.

    Args:
        file_content: File to check if it's an apk or not.

    Returns:
        True if the file is a valid apk file, False otherwise.
    """

    try:
        with zipfile.ZipFile(io.BytesIO(file_content)) as o:
            return "AndroidManifest.xml" in o.namelist()
    except zipfile.BadZipFile:
        return False


def is_xapk(file_content: bytes) -> bool:
    """Check if a file is a xapk bundle.

    Args:
        file_content: File to check if it's xapk application or not.

    Returns:
        True if the file is a valid xapk file, False otherwise.
    """

    try:
        with zipfile.ZipFile(io.BytesIO(file_content)) as o:
            return all(file_name.endswith(".apk") for file_name in o.namelist())
    except zipfile.BadZipFile:
        return False


def is_aab(file_content: bytes) -> bool:
    """Check if file is an AAB file.

    Args:
        file_content: File to check if it's an aab or not.

    Returns:
        True if the file is a valid aab file, False otherwise.
    """

    try:
        with zipfile.ZipFile(io.BytesIO(file_content)) as o:
            return "BundleConfig.pb" in o.namelist()
    except zipfile.BadZipFile:
        return False
