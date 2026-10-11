from typing import Any

import graphene
from graphql.execution import base
from sqlalchemy import orm

class SQLAlchemyObjectType(graphene.ObjectType[object]):
    @classmethod
    def get_query(cls, info: base.ResolveInfo) -> orm.Query[Any]: ...
