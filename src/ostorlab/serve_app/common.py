"""common utilities for the flask app."""

import struct
from typing import Optional, Union

import cvss
import graphene
from graphene.types import scalars


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
    def coerce_bytes(value: Union[str, bytes, memoryview, list]) -> bytes:
        if isinstance(value, bytes):
            return value
        elif isinstance(value, memoryview):
            return value.tobytes()
        elif isinstance(value, str):
            return Bytes._rawbytes(value)
        elif isinstance(value, list):
            return bytes(value)
        else:
            raise NotImplementedError(f"Bytes scalar coerce error from {type(value)}")

    serialize = coerce_bytes
    parse_value = coerce_bytes

    @staticmethod
    def parse_literal(ast):
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
