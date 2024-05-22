import graphene

from ostorlab.runtimes.local.app.oxo import Mutations as ScanMutations
from ostorlab.runtimes.local.app.oxo import Query as ScanQuery


class Mutations(ScanMutations, graphene.ObjectType):
    pass


class Query(ScanQuery, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutations)
