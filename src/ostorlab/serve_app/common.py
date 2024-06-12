"""common utilities for the flask app."""

import collections
import inspect
import io
import json
import zipfile
from functools import cached_property
from math import ceil
import struct
from typing import Optional, Union

import cvss
import graphene
from graphql.language import ast
from graphene.types import scalars


class PageInfo(graphene.ObjectType):
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
        value: Union[str, bytes, memoryview, list, float, int, dict, bool],
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
        elif isinstance(value, float) or isinstance(value, int):
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
    def parse_literal(asst: ast.Value) -> Optional[int]:
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


def compute_cvss_v3_base_score(vector: Optional[str]) -> Optional[float]:
    """Compute the CVSS v3 base score from the vector.

    Args:
        vector (str | None): CVSS v3 vector.

    Returns:
        CVSS v3 base score or None if the vector is invalid.
    """
    if vector is None:
        return None
    try:
        return cvss.CVSS3(vector).scores()[0]
    except cvss.CVSS3Error:
        return None


class Page(collections.abc.Sequence):
    """A single page in a paginated list of objects."""

    def __init__(self, object_list, number, paginator):
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

    def __repr__(self):
        """Return the string representation of the page object."""
        return "<Page %s of %s>" % (self.number, self.paginator.num_pages)

    def __len__(self):
        """Return the number of objects in the page."""
        return len(self.object_list)

    def __getitem__(self, index):
        """Return the object at the given index in the page."""
        if isinstance(index, (int, slice)) is False:
            raise TypeError(
                "Page indices must be integers or slices, not %s."
                % type(index).__name__
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


class Paginator:
    """A paginator object for paginating a list of objects."""

    def __init__(self, object_list: list[any], per_page):
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
        c = getattr(self.object_list, "count", None)
        if callable(c) is True and inspect.isbuiltin(c) is False:
            return c()
        return len(self.object_list)

    @cached_property
    def num_pages(self) -> int:
        """Return the total number of pages."""
        if self.count == 0:
            return 0
        hits = max(1, self.count)
        return ceil(hits / self.per_page)

    def get_page(self, number: int) -> Page:
        """Return a valid page, even if the page argument isn't a number or isn't in range.
        Args:
            number: The page number.
        Returns: The page object.
        """
        return self.page(number)

    def page(self, number: int) -> Page:
        """Return a Page object for the given 1-based page number
        Args:
            number: The page number.

        Returns: The page object.
        """
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        if top >= self.count:
            top = self.count
        return Page(
            object_list=self.object_list[bottom:top], number=number, paginator=self
        )

    def _get_page(self, *args, **kwargs) -> Page:
        """Return an instance of a single page."""
        return Page(*args, **kwargs)


def is_apk(file_content: bytes) -> bool:
    """Check if a file is an apk.

    Args:
        file_content: File to check if it's an apk or not.

    Returns:
        True if the file is a valid apk file, False otherwise.
    """

    try:
        with zipfile.ZipFile(io.BytesIO(file_content)) as o:
            if "AndroidManifest.xml" in o.namelist():
                return True
            return False
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
            if "BundleConfig.pb" in o.namelist():
                return True
            return False
    except zipfile.BadZipFile:
        return False
