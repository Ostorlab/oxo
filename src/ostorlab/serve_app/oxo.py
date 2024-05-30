"""Oxo GraphQL queries and mutations."""

from typing import Optional, List

import graphene
import graphql
from graphene_file_upload import scalars
from graphql.execution import base as graphql_base

from ostorlab.runtimes.local.models import models
from ostorlab.serve_app import common
from ostorlab.serve_app import import_utils
from ostorlab.serve_app import types

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
    scan = graphene.Field(
        types.OxoScanType, scan_id=graphene.Int(), description="Retrieve scan by id."
    )

    agent_groups = graphene.Field(
        types.AgentGroupsType,
        search=graphene.String(required=False),
        page=graphene.Int(required=False),
        number_elements=graphene.Int(required=False),
        order_by=graphene.Argument(types.AgentGroupOrderByEnum, required=False),
        sort=graphene.Argument(common.SortEnum, required=False),
        agent_group_ids=graphene.List(graphene.Int),
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
            if order_by_filter is not None and sort == common.SortEnum.Desc:
                scans = scans.order_by(order_by_filter.desc())
            elif order_by_filter is not None:
                scans = scans.order_by(order_by_filter)
            else:
                scans = scans.order_by(models.Scan.id.desc())

            if page is not None and number_elements > 0:
                p = common.Paginator(scans, number_elements)
                page = p.get_page(page)
                page_info = common.PageInfo(
                    count=p.count,
                    num_pages=p.num_pages,
                    has_next=page.has_next(),
                    has_previous=page.has_previous(),
                )
                return types.OxoScansType(scans=page, page_info=page_info)
            else:
                return types.OxoScansType(scans=scans)

    def resolve_scan(
        self, info: graphql_base.ResolveInfo, scan_id: int
    ) -> types.OxoScanType:
        """Retrieve scan by its id.

        Args:
            info: `graphql_base.ResolveInfo` instance.
            scan_id: The scan ID.

        Raises:
            graphql.GraphQLError in case the scan does not exist.

        Returns:
            The scan information.
        """
        with models.Database() as session:
            scan = session.query(models.Scan).get(scan_id)
            if scan is None:
                raise graphql.GraphQLError("Scan not found.")

            return scan

    def resolve_agent_groups(
        self,
        info,
        search: str = None,
        page=None,
        number_elements: int = DEFAULT_NUMBER_ELEMENTS,
        order_by: Optional[types.AgentGroupOrderByEnum] = None,
        sort: Optional[common.SortEnum] = None,
        agent_group_ids: Optional[List[int]] = None,
    ) -> types.AgentGroupsType:
        """Resolve agent groups query.

        Args:
            info: GraphQL resolve info.
            search: Search string.
            page: Page number.
            number_elements: Number of elements.
            order_by: Order by filter.
            sort: Sort filter.
            agent_group_ids: List of agent group ids.

        Returns:
            types.AgentGroupsType: List of agent groups.
        """

        if number_elements <= 0:
            return types.AgentGroupsType(agent_groups=[])

        with models.Database() as session:
            agent_groups_query = session.query(models.AgentGroup)

            if agent_group_ids is not None:
                agent_groups_query = agent_groups_query.filter(
                    models.AgentGroup.id.in_(agent_group_ids)
                )

            if search is not None:
                agent_groups_query = agent_groups_query.filter(
                    models.AgentGroup.name.ilike(f"%{search}%")
                )

            order_by_filter = None
            if order_by == types.AgentGroupOrderByEnum.AgentGroupId:
                order_by_filter = models.AgentGroup.id
            elif order_by == types.AgentGroupOrderByEnum.Name:
                order_by_filter = models.AgentGroup.name
            elif order_by == types.AgentGroupOrderByEnum.CreatedTime:
                order_by_filter = models.AgentGroup.created_time

            if sort == common.SortEnum.Desc and order_by_filter is not None:
                agent_groups_query = agent_groups_query.order_by(order_by_filter.desc())
            elif order_by_filter is not None:
                agent_groups_query = agent_groups_query.order_by(order_by_filter)
            else:
                agent_groups_query = agent_groups_query.order_by(
                    models.AgentGroup.id.desc()
                )

            if page is not None and number_elements > 0:
                p = common.Paginator(agent_groups_query, number_elements)
                page = p.get_page(page)
                page_info = common.PageInfo(
                    count=p.count,
                    num_pages=p.num_pages,
                    has_next=page.has_next(),
                    has_previous=page.has_previous(),
                )
                return types.AgentGroupsType(agent_groups=page, page_info=page_info)
            else:
                return types.AgentGroupsType(agent_groups=agent_groups_query)


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


class DeleteScanMutation(graphene.Mutation):
    """Delete Scan & its information mutation."""

    class Arguments:
        scan_id = graphene.Int(required=True)

    result = graphene.Boolean()

    @staticmethod
    def mutate(
        root,
        info: graphql_base.ResolveInfo,
        scan_id: int,
    ) -> "DeleteScanMutation":
        """Delete a scan & its information.

        Args:
            info: `graphql_base.ResolveInfo` instance.
            scan_id: The scan ID.

        Raises:
            graphql.GraphQLError in case the scan does not exist.

        Returns:
            Boolean `True` if the delete operation is successful.

        """
        with models.Database() as session:
            scan_query = session.query(models.Scan).filter_by(id=scan_id)
            if scan_query.count() == 0:
                raise graphql.GraphQLError("Scan not found.")
            scan_query.delete()
            session.query(models.Vulnerability).filter_by(scan_id=scan_id).delete()
            session.query(models.ScanStatus).filter_by(scan_id=scan_id).delete()
            session.commit()
            return DeleteScanMutation(result=True)


class Mutations(graphene.ObjectType):
    delete_scan = DeleteScanMutation.Field(
        description="Delete a scan & all its information."
    )
    import_scan = ImportScanMutation.Field(description="Import scan from file.")
