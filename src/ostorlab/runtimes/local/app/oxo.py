from typing import Optional

import graphene
from graphene_file_upload import scalars
from graphql.execution import base as graphql_base

from ostorlab.runtimes.local.app import import_utils
from ostorlab.runtimes.local.models import models


class ImportScanMutation(graphene.Mutation):
    class Arguments:
        scan_id = graphene.Int(required=False)
        file = scalars.Upload(required=True)

    message = graphene.String()

    @staticmethod
    def mutate(
        root,
        info: graphql_base.ResolveInfo,
        file: scalars.Upload,
        scan_id: Optional[int] = None,
    ):
        with models.Database() as session:
            scan = session.query(models.Scan).filter_by(id=scan_id).first()
            import_utils.import_scan(session, file.read(), scan)
            return ImportScanMutation(message="Scan imported successfully")


class Mutations(graphene.ObjectType):
    import_scan = ImportScanMutation.Field(description="Import scan from file")
