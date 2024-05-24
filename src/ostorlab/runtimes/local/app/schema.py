"""Oxo schema."""

import graphene

from ostorlab.runtimes.local.app import oxo


class Mutations(oxo.Mutations, graphene.ObjectType):
    pass


class Query(oxo.Query, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutations)
