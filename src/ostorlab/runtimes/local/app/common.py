"""common utilities for the flask app."""

import graphene


class SortEnum(graphene.Enum):
    """Sort enum, for the sorting order of the results."""

    ASC = 1
    DESC = 2
