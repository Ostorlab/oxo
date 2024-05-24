"""common utilities for the flask app."""

from typing import Optional

import graphene
import cvss


class SortEnum(graphene.Enum):
    """Sort enum, for the sorting order of the results."""

    ASC = 1
    DESC = 2


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
