"""Utils to handle scan risk rating."""

import enum
from typing import List


class RiskRating(enum.Enum):
    """Enumeration of the risk rating of a scan."""

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    POTENTIALLY = "Potentially"
    HARDENING = "Hardening"
    SECURE = "Secure"
    IMPORTANT = "Important"
    INFO = "Info"

    @classmethod
    def has_value(cls, value: str) -> bool:
        return value in cls._member_map_

    @classmethod
    def values(cls) -> List[str]:
        return [key.lower() for key in cls._member_map_.keys()]


RATINGS_ORDER = {
    RiskRating.CRITICAL.name: 0,
    RiskRating.HIGH.name: 1,
    RiskRating.MEDIUM.name: 2,
    RiskRating.LOW.name: 3,
    RiskRating.POTENTIALLY.name: 4,
    RiskRating.HARDENING.name: 5,
    RiskRating.SECURE.name: 6,
    RiskRating.IMPORTANT.name: 7,
    RiskRating.INFO.name: 8,
}
