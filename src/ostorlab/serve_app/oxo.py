"""Oxo GraphQL queries and mutations."""

import io
from typing import Optional, List

import graphene
import graphql
import httpx
from graphene_file_upload import scalars
from graphql.execution import base as graphql_base
from ruamel.yaml import error

from ostorlab import exceptions
from ostorlab.agent.schema import validator
from ostorlab.cli import agent_fetcher, install_agent
from ostorlab.runtimes import definitions
from ostorlab.runtimes.local import runtime
from ostorlab.serve_app import import_utils, types, common
from ostorlab.runtimes.local.models import models

DEFAULT_NUMBER_ELEMENTS = 15


class Query(graphene.ObjectType):
    """Query object type."""

    scans = graphene.Field(
        types.OxoScansType,
        scan_ids=graphene.List(graphene.Int, required=False),
        page=graphene.Int(required=False),
        number_elements=graphene.Int(required=False),
        order_by=types.OxoScanOrderByEnum(required=False),
        sort=common.SortEnum(required=False),
        description="List of scans.",
    )

    def resolve_scans(
        self,
        info: graphql_base.ResolveInfo,
        scan_ids: Optional[List[int]] = None,
        page: Optional[int] = None,
        number_elements: int = DEFAULT_NUMBER_ELEMENTS,
        order_by: Optional[types.OxoScanOrderByEnum] = None,
        sort: Optional[common.SortEnum] = None,
    ) -> Optional[types.OxoScansType]:
        """Resolve scans query.

        Args:
            info (graphql_base.ResolveInfo): GraphQL resolve info.
            scan_ids (Optional[List[int]], optional): List of scan ids. Defaults to None.
            page (int | None, optional): Page number. Defaults to None.
            number_elements (int, optional): Number of elements. Defaults to DEFAULT_NUMBER_ELEMENTS.
            order_by (Optional[types.OxoScanOrderByEnum], optional): Order by filter. Defaults to None.
            sort (Optional[common.SortEnum], optional): Sort filter. Defaults to None.

        Returns:
            Optional[types.OxoScansType]: List of scans.
        """
        if number_elements <= 0:
            return types.OxoScansType(scans=[])

        with models.Database() as session:
            scans = session.query(models.Scan)

            if scan_ids is not None:
                scans = scans.filter(models.Scan.id.in_(scan_ids))

            order_by_filter = None
            if order_by == types.OxoScanOrderByEnum.ScanId:
                order_by_filter = models.Scan.id
            elif order_by == types.OxoScanOrderByEnum.Title:
                order_by_filter = models.Scan.title
            elif order_by == types.OxoScanOrderByEnum.CreatedTime:
                order_by_filter = models.Scan.created_time
            elif order_by == types.OxoScanOrderByEnum.Progress:
                order_by_filter = models.Scan.progress
            if order_by_filter is not None and sort == common.SortEnum.DESC:
                scans = scans.order_by(order_by_filter.desc())
            elif order_by_filter is not None:
                scans = scans.order_by(order_by_filter)
            else:
                scans = scans.order_by(models.Scan.id.desc())

            if page is not None and number_elements > 0:
                scans = scans.offset((page - 1) * number_elements).limit(
                    number_elements
                )
                return types.OxoScansType(scans=scans)
            else:
                return types.OxoScansType(scans=scans)


class ImportScanMutation(graphene.Mutation):
    """Import scan mutation."""

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
    ) -> "ImportScanMutation":
        """Import scan mutation.

        Args:
            info (graphql_base.ResolveInfo): GraphQL resolve info.
            file (scalars.Upload): File to import.
            scan_id (Optional[int], optional): Scan id. Defaults to None.

        Returns:
            ImportScanMutation: Import scan mutation.
        """
        with models.Database() as session:
            scan = session.query(models.Scan).filter_by(id=scan_id).first()
            import_utils.import_scan(session, file.read(), scan)
            return ImportScanMutation(message="Scan imported successfully")


class ScanRunMutation(graphene.Mutation):
    class Arguments:
        title = graphene.String()
        agent_group_definition = scalars.Upload()
        assets = scalars.Upload()
        install = graphene.Boolean()
        package_names = graphene.List(graphene.String)

    message = graphene.String()

    @staticmethod
    def mutate(
        root,
        info: graphql_base.ResolveInfo,
        title: Optional[str] = None,
        agent_group_definition: Optional[io.FileIO] = None,
        assets: Optional[io.FileIO] = None,
        install: Optional[bool] = False,
    ) -> "ScanRunMutation":
        """Run scan mutation.

        Args:
            info (graphql_base.ResolveInfo): GraphQL resolve info.
            title (Optional[str], optional): Scan title. Defaults to None.
            agent_group_definition (Optional[io.FileIO], optional): Agent group definition. Defaults to None.
            assets (Optional[io.FileIO], optional): Assets. Defaults to None.
            install (Optional[bool], optional): Install agents. Defaults to False.

        Returns:
            ScanRunMutation: Scan run mutation.
        """
        if agent_group_definition is not None:
            try:
                agent_group = definitions.AgentGroupDefinition.from_yaml(
                    agent_group_definition
                )
            except validator.ValidationError as e:
                raise graphql.GraphQLError(f"Invalid agent group definition: {e}")
            except error.YAMLError as e:
                raise graphql.GraphQLError(
                    f"Agent group definition YAML parse error:: {e}"
                )
        else:
            raise graphql.GraphQLError("Missing agent list or agent group definition.")

        asset_group = None
        if assets is not None:
            try:
                asset_group = definitions.AssetsDefinition.from_yaml(assets)
            except validator.ValidationError as e:
                raise graphql.GraphQLError(f"Invalid asset group definition: {e}")
            except error.YAMLError as e:
                raise graphql.GraphQLError(
                    f"Asset group definition YAML parse error: {e}"
                )

        runtime_instance: runtime.LocalRuntime = runtime.LocalRuntime()
        runtime_instance.follow = []

        try:
            can_run_scan = runtime_instance.can_run(agent_group_definition=agent_group)
        except exceptions.OstorlabError as e:
            raise graphql.GraphQLError(f"Runtime encountered an error to run scan: {e}")
        if can_run_scan is True:
            if install is True:
                try:
                    runtime_instance.install()
                    for ag in agent_group.agents:
                        try:
                            install_agent.install(ag.key, ag.version)
                        except agent_fetcher.AgentDetailsNotFound:
                            graphql.GraphQLError(
                                f"Agent {ag.key} not found on the store."
                            )
                except httpx.HTTPError as e:
                    raise graphql.GraphQLError(f"Could not install the agents: {e}")

            message_status = runtime_instance.scan(
                title=title,
                agent_group_definition=agent_group,
                assets=asset_group.targets if asset_group is not None else None,
            )

            if message_status is not None:
                raise graphql.GraphQLError(message_status)

            return ScanRunMutation(message="Scan started successfully")


class Mutations(graphene.ObjectType):
    import_scan = ImportScanMutation.Field(description="Import scan from file")
    run_scan = ScanRunMutation.Field(description="Run scan")
