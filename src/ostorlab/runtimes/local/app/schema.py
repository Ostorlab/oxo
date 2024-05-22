import graphene

from ostorlab.runtimes.local.app.oxo import Mutations as ScanMutations


class Mutations(ScanMutations, graphene.ObjectType):
    pass


schema = graphene.Schema(mutation=Mutations)
