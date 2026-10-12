"""Oxo schema."""

import graphene

from ostorlab.serve_app import common
from ostorlab.serve_app import oxo


class Mutations(oxo.Mutations, common.ObjectType):
    pass


class Query(oxo.Query, common.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutations)
