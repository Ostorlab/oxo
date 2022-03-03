"""Utils to handle scan risk rating."""
import enum


class RiskRating(enum.Enum):
    """Enumeration of the risk rating of a scan."""
    HIGH = 'High'
    MEDIUM = 'Medium'
    LOW = 'Low'
    POTENTIALLY = 'Potentially'
    HARDENING = 'Hardening'
    SECURE = 'Secure'
    IMPORTANT = 'Important'
    INFO = 'Info'

    @classmethod
    def has_value(cls, value):
        return value in cls._member_map_

    @classmethod
    def values(cls):
        return [key.lower() for key in cls._member_map_.keys()]


RATINGS_ORDER = {
    RiskRating.HIGH.name: 0,
    RiskRating.MEDIUM.name: 1,
    RiskRating.LOW.name: 2,
    RiskRating.POTENTIALLY.name: 3,
    RiskRating.HARDENING.name: 4,
    RiskRating.SECURE.name: 5,
    RiskRating.IMPORTANT.name: 6,
    RiskRating.INFO.name: 7
}
