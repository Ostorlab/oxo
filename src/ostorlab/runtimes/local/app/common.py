"""common utilities for the flask app."""

import graphene


class SortEnum(graphene.Enum):
    Asc = 1
    Desc = 2
