"""Graphene types for the local runtime."""

import collections
import enum
import json
from typing import Optional, List

import graphene
import graphene_sqlalchemy
from graphql.execution import base as graphql_base
from graphene_file_upload import scalars

from ostorlab.runtimes.local.models import models
from ostorlab.serve_app import common

DEFAULT_NUMBER_ELEMENTS = 15
RISK_RATINGS_ORDER = {
    common.RiskRatingEnum.CRITICAL.name: 8,
    common.RiskRatingEnum.HIGH.name: 7,
    common.RiskRatingEnum.MEDIUM.name: 6,
    common.RiskRatingEnum.LOW.name: 5,
    common.RiskRatingEnum.POTENTIALLY.name: 4,
    common.RiskRatingEnum.HARDENING.name: 3,
    common.RiskRatingEnum.SECURE.name: 2,
    common.RiskRatingEnum.IMPORTANT.name: 1,
    common.RiskRatingEnum.INFO.name: 0,
}


class OxoScanOrderByEnum(graphene.Enum):
    """Enum for the elements to order a scan by."""

    ScanId = enum.auto()
    Title = enum.auto()
    CreatedTime = enum.auto()
    Progress = enum.auto()


class AgentGroupOrderByEnum(graphene.Enum):
    AgentGroupId = enum.auto()
    Name = enum.auto()
    CreatedTime = enum.auto()


class OxoReferenceType(graphene.ObjectType):
    """Graphene object type for a reference."""

    title = graphene.String()
    url = graphene.String()


class OxoKnowledgeBaseVulnerabilityType(graphene.ObjectType):
    """SQLAlchemy object type for a knowledge base vulnerability."""

    references = graphene.List(OxoReferenceType)
    title = graphene.String()
    short_description = graphene.String()
    description = graphene.String()
    recommendation = graphene.String()


class OxoVulnerabilityType(graphene_sqlalchemy.SQLAlchemyObjectType):
    """SQLAlchemy object type for a vulnerability."""

    detail = graphene.Field(OxoKnowledgeBaseVulnerabilityType, required=False)
    cvss_v3_base_score = graphene.Float(required=False)

    class Meta:
        """Meta class for the vulnerability object type."""

        model = models.Vulnerability
        only_fields = (
            "id",
            "technical_detail",
            "risk_rating",
            "cvss_v3_vector",
            "dna",
        )

    def resolve_cvss_v3_base_score(
        self: models.Vulnerability, info: graphql_base.ResolveInfo
    ) -> float:
        """Resolve CVSS v3 base score query.

        Args:
            self (models.Vulnerability): The vulnerability object.
            info (graphql_base.ResolveInfo): GraphQL resolve info.

        Returns:
            float: The CVSS v3 base score.
        """
        return common.compute_cvss_v3_base_score(self.cvss_v3_vector)

    def resolve_detail(
        self: models.Vulnerability, info: graphql_base.ResolveInfo
    ) -> OxoKnowledgeBaseVulnerabilityType:
        """Resolve detail query.

        Args:
            self (models.Vulnerability): The vulnerability object.
            info (graphql_base.ResolveInfo): GraphQL resolve info.

        Returns:
            OxoKnowledgeBaseVulnerabilityType: The knowledge base vulnerability.
        """
        with models.Database() as session:
            references = (
                session.query(models.Reference)
                .filter(models.Reference.vulnerability_id == self.id)
                .all()
            )

            return OxoKnowledgeBaseVulnerabilityType(
                title=self.title,
                short_description=self.short_description,
                description=self.description,
                recommendation=self.recommendation,
                references=[
                    OxoReferenceType(title=ref.title, url=ref.url) for ref in references
                ],
            )


class OxoVulnerabilitiesType(graphene.ObjectType):
    """Graphene object type for a list of vulnerabilities."""

    vulnerabilities = graphene.List(OxoVulnerabilityType, required=True)
    page_info = graphene.Field(common.PageInfo, required=False)


class OxoAggregatedKnowledgeBaseVulnerabilityType(graphene.ObjectType):
    """Graphene object type for an aggregated knowledge base vulnerability."""

    highest_risk_rating = graphene.Field(common.RiskRatingEnum)
    highest_cvss_v3_vector = graphene.String()
    highest_cvss_v3_base_score = graphene.Float()
    kb = graphene.Field(OxoKnowledgeBaseVulnerabilityType)
    vulnerabilities = graphene.Field(
        OxoVulnerabilitiesType,
        detail_titles=graphene.List(graphene.String),
        page=graphene.Int(required=False),
        number_elements=graphene.Int(required=False),
        description="List of vulnerabilities.",
    )

    def resolve_vulnerabilities(
        self: models.Scan,
        info: graphql_base.ResolveInfo,
        detail_titles: Optional[List[str]] = None,
        page: Optional[int] = None,
        number_elements: int = DEFAULT_NUMBER_ELEMENTS,
    ) -> OxoVulnerabilitiesType:
        """Resolve vulnerabilities query.

        Args:
            self: The scan object.
            info: GraphQL resolve info.
            detail_titles: List of detail titles. Defaults to None.
            page: Page number. Defaults to None.
            number_elements: Number of elements. Defaults to DEFAULT_NUMBER_ELEMENTS.

        Returns:
            OxoVulnerabilitiesType: List of vulnerabilities.
        """
        if number_elements <= 0:
            return OxoVulnerabilitiesType(vulnerabilities=[])

        vulnerabilities = self.vulnerabilities.vulnerabilities.order_by(
            models.Vulnerability.id
        )

        if detail_titles is not None and len(detail_titles) > 0:
            vulnerabilities = vulnerabilities.filter(
                models.Vulnerability.title.in_(detail_titles)
            )

        if page is not None and number_elements > 0:
            p = common.Paginator(vulnerabilities, number_elements)
            page = p.get_page(page)
            page_info = common.PageInfo(
                count=p.count,
                num_pages=p.num_pages,
                has_next=page.has_next(),
                has_previous=page.has_previous(),
            )
            return OxoVulnerabilitiesType(vulnerabilities=page, page_info=page_info)
        else:
            return OxoVulnerabilitiesType(vulnerabilities=vulnerabilities)


class AssetScansMixin:
    scans = graphene.List(
        lambda: OxoScanType, last_only=graphene.Boolean(required=False)
    )

    def resolve_scans(self, info):
        with models.Database() as session:
            scans = session.query(models.Scan).filter(models.Scan.asset_id == self.id)

        return scans


class OxoAndroidStoreAssetType(
    graphene_sqlalchemy.SQLAlchemyObjectType, AssetScansMixin
):
    class Meta:
        model = models.AndroidStore
        fields = ("id", "package_name", "application_name")


class OxoAndroidStoreAssetInputType(graphene.InputObjectType):
    package_name = graphene.String()
    application_name = graphene.String()


class OxoIOSStoreAssetType(graphene_sqlalchemy.SQLAlchemyObjectType, AssetScansMixin):
    class Meta:
        model = models.IosStore
        fields = ("id", "bundle_id", "application_name")


class OxoIOSStoreAssetInputType(graphene.InputObjectType):
    bundle_id = graphene.String()
    application_name = graphene.String()


class OxoAndroidFileAssetType(
    graphene_sqlalchemy.SQLAlchemyObjectType, AssetScansMixin
):
    class Meta:
        model = models.AndroidFile
        fields = ("id", "package_name", "path")


class OxoAndroidFileAssetInputType(graphene.InputObjectType):
    file = scalars.Upload()
    package_name = graphene.String()


class OxoIOSFileAssetType(graphene_sqlalchemy.SQLAlchemyObjectType, AssetScansMixin):
    class Meta:
        model = models.IosFile
        fields = ("id", "bundle_id", "path")


class OxoIOSFileAssetInputType(graphene.InputObjectType):
    file = scalars.Upload()
    bundle_id = graphene.String()


class OxoUrlAssetType(graphene_sqlalchemy.SQLAlchemyObjectType, AssetScansMixin):
    links = graphene.List(graphene.String, required=False)

    class Meta:
        model = models.Url
        fields = ("id",)

    def resolve_links(self, info):
        try:
            return json.loads(self.links)
        except json.JSONDecodeError:
            return []


class OxoUrlAssetInputType(graphene.InputObjectType):
    links = graphene.List(graphene.String)


class OxoNetworkAssetType(graphene_sqlalchemy.SQLAlchemyObjectType, AssetScansMixin):
    networks = graphene.List(graphene.String, required=False)

    class Meta:
        model = models.Network
        fields = ("id",)

    def resolve_networks(self, info):
        try:
            return json.loads(self.networks)
        except json.JSONDecodeError:
            return []


class OxoNetworkAssetInputType(graphene.InputObjectType):
    networks = graphene.List(graphene.String)


class OxoAssetType(graphene.Union):
    class Meta:
        model = models.Asset
        types = (
            OxoAndroidFileAssetType,
            OxoIOSFileAssetType,
            OxoAndroidStoreAssetType,
            OxoIOSStoreAssetType,
            OxoUrlAssetType,
            OxoNetworkAssetType,
        )


class OxoScanType(graphene_sqlalchemy.SQLAlchemyObjectType):
    """SQLAlchemy object type for a scan."""

    vulnerabilities = graphene.Field(
        OxoVulnerabilitiesType,
        page=graphene.Int(required=False),
        number_elements=graphene.Int(required=False),
        detail_titles=graphene.List(graphene.String, required=False),
        vuln_ids=graphene.List(graphene.Int, required=False),
        description="List of vulnerabilities.",
    )
    kb_vulnerabilities = graphene.Field(
        graphene.List(OxoAggregatedKnowledgeBaseVulnerabilityType),
        detail_title=graphene.String(required=False),
        description="List of aggregated knowledge base vulnerabilities.",
    )
    message_status = graphene.String()
    progress = graphene.String()
    asset_instance = graphene.Field(OxoAssetType)

    class Meta:
        """Meta class for the scan object type."""

        model = models.Scan
        description = "Scan object."
        only_fields = (
            "id",
            "title",
            "created_time",
            "asset",
        )

    def resolve_progress(self: models.Scan, info: graphql_base.ResolveInfo) -> str:
        """Resolve progress query.

        Args:
            self (models.Scan): The scan object.
            info (graphql_base.ResolveInfo): GraphQL resolve info.

        Returns:
            str: The progress of the scan.
        """

        return self.progress.name

    def resolve_asset_instance(
        self,
        info: graphql_base.ResolveInfo,
    ):
        """Resolve asset information of a scan."""
        return self.asset_instance

    def resolve_vulnerabilities(
        self: models.Scan,
        info: graphql_base.ResolveInfo,
        detail_titles: Optional[List[str]] = None,
        vuln_ids: Optional[List[int]] = None,
        page: Optional[int] = None,
        number_elements: int = DEFAULT_NUMBER_ELEMENTS,
    ) -> OxoVulnerabilitiesType:
        """Resolve vulnerabilities query.

        Args:
            self (models.Scan): The scan object.
            info (graphql_base.ResolveInfo): GraphQL resolve info.
            detail_titles (list[str] | None, optional): List of detail titles. Defaults to None.
            vuln_ids (list[int] | None, optional): List of vulnerability ids. Defaults to None.
            page (int | None, optional): Page number. Defaults to None.
            number_elements (int, optional): Number of elements. Defaults to DEFAULT_NUMBER_ELEMENTS.

        Returns:
            OxoVulnerabilitiesType: List of vulnerabilities.
        """
        if number_elements <= 0:
            return OxoVulnerabilitiesType(vulnerabilities=[])

        with models.Database() as session:
            vulnerabilities = session.query(models.Vulnerability).filter(
                models.Vulnerability.scan_id == self.id
            )

            if vuln_ids is not None and len(vuln_ids) > 0:
                vulnerabilities = vulnerabilities.filter(
                    models.Vulnerability.id.in_(vuln_ids)
                )

            if detail_titles is not None and len(detail_titles) > 0:
                vulnerabilities = vulnerabilities.filter(
                    models.Vulnerability.title.in_(detail_titles)
                )

            vulnerabilities = vulnerabilities.order_by(models.Vulnerability.id)

            if page is not None and number_elements > 0:
                p = common.Paginator(vulnerabilities, number_elements)
                page = p.get_page(page)
                page_info = common.PageInfo(
                    count=p.count,
                    num_pages=p.num_pages,
                    has_next=page.has_next(),
                    has_previous=page.has_previous(),
                )
                return OxoVulnerabilitiesType(vulnerabilities=page, page_info=page_info)
            else:
                return OxoVulnerabilitiesType(vulnerabilities=vulnerabilities)

    def resolve_kb_vulnerabilities(
        self: models.Scan,
        info: graphql_base.ResolveInfo,
        detail_title: Optional[str] = None,
        page: Optional[int] = None,
        number_elements: int = DEFAULT_NUMBER_ELEMENTS,
    ) -> list[OxoAggregatedKnowledgeBaseVulnerabilityType]:
        """Resolve knowledge base vulnerabilities query.

        Args:
            self (models.Scan): The scan object.
            info (graphql_base.ResolveInfo): GraphQL resolve info.
            detail_title (str | None, optional): The detail title. Defaults to None.

        Returns:
            list[OxoAggregatedKnowledgeBaseVulnerabilityType]: List of aggregated knowledge base vulnerabilities.
        """
        aggregated_kb = OxoScanType._build_kb_vulnerabilities(self, detail_title)
        return aggregated_kb

    def resolve_message_status(
        self: models.Scan, info: graphql_base.ResolveInfo
    ) -> str:
        """Resolve message status query.

        Args:
            self (models.Scan): The scan object.
            info (graphql_base.ResolveInfo): GraphQL resolve info.

        Returns:
            str: The message status of the scan.
        """
        with models.Database() as session:
            scan_statuses = session.query(models.ScanStatus).filter(
                models.ScanStatus.scan_id == self.id
            )
            message_statuses = [
                s.value for s in scan_statuses if s.key == "message_status"
            ]
            if message_statuses is not None and len(message_statuses) > 0:
                return message_statuses[-1]

    @staticmethod
    def _build_kb_vulnerabilities(
        scan: models.Scan, detail_title: Optional[str] = None
    ) -> list[OxoAggregatedKnowledgeBaseVulnerabilityType]:
        """Build knowledge base vulnerabilities.

        Args:
            scan (models.Scan): The scan object.
            detail_title (str | None, optional): The detail title. Defaults to None.

        Returns:
            list[OxoAggregatedKnowledgeBaseVulnerabilityType]: List of aggregated knowledge base vulnerabilities.
        """
        with models.Database() as session:
            vulnerabilities = session.query(models.Vulnerability).filter(
                models.Vulnerability.scan_id == scan.id
            )
            if detail_title is not None:
                vulnerabilities = vulnerabilities.filter(
                    models.Vulnerability.title == detail_title
                )

            kbs = vulnerabilities.group_by(
                models.Vulnerability.title,
                models.Vulnerability.short_description,
                models.Vulnerability.recommendation,
            ).all()

            distinct_vulnz = vulnerabilities.distinct(
                models.Vulnerability.risk_rating,
                models.Vulnerability.cvss_v3_vector,
            ).all()

            kb_dict = collections.defaultdict(list)
            cvss_dict = collections.defaultdict(list)

            aggregated_kb = []
            for vuln in distinct_vulnz:
                kb_dict[vuln.title].append(vuln.risk_rating)
                cvss_dict[vuln.title].append(vuln.cvss_v3_vector)

            for kb in kbs:
                kb_vulnerabilities = vulnerabilities.filter(
                    models.Vulnerability.title == kb.title
                )
                highest_risk_rating = max(
                    kb_dict[kb.title], key=lambda risk: RISK_RATINGS_ORDER[risk.name]
                )
                if cvss_dict is not None:
                    cvss_v3_vectors = [
                        v
                        for v in cvss_dict[kb.title]
                        if v is not None
                        and common.compute_cvss_v3_base_score(v) is not None
                    ]
                if len(cvss_v3_vectors) > 0:
                    highest_cvss_v3_vector = max(
                        cvss_v3_vectors,
                        key=lambda vector: common.compute_cvss_v3_base_score(vector),
                    )
                else:
                    highest_cvss_v3_vector = kb.cvss_v3_vector or None
                references = (
                    session.query(models.Reference)
                    .filter(
                        models.Reference.vulnerability_id
                        == kb_vulnerabilities.first().id
                    )
                    .distinct(models.Reference.title)
                ).all()
                aggregated_kb.append(
                    OxoAggregatedKnowledgeBaseVulnerabilityType(
                        highest_risk_rating=highest_risk_rating,
                        highest_cvss_v3_vector=highest_cvss_v3_vector,
                        highest_cvss_v3_base_score=common.compute_cvss_v3_base_score(
                            highest_cvss_v3_vector
                        ),
                        kb=OxoKnowledgeBaseVulnerabilityType(
                            title=kb.title,
                            short_description=kb.short_description,
                            description=kb.description,
                            recommendation=kb.recommendation,
                            references=[
                                OxoReferenceType(title=ref.title, url=ref.url)
                                for ref in references
                            ],
                        ),
                        vulnerabilities=OxoVulnerabilitiesType(
                            vulnerabilities=kb_vulnerabilities
                        ),
                    )
                )

            return aggregated_kb


class OxoScansType(graphene.ObjectType):
    """Graphene object type for a list of scans."""

    scans = graphene.List(OxoScanType, required=True)
    page_info = graphene.Field(common.PageInfo, required=False)


class AgentArgumentType(graphene_sqlalchemy.SQLAlchemyObjectType):
    """Graphene object type for a list of agent arguments."""

    value = common.Bytes(required=False)

    class Meta:
        """Meta class for the agent arguments object type."""

        model = models.AgentArgument
        only_fields = (
            "id",
            "name",
            "type",
            "description",
        )

    def resolve_value(
        self: models.AgentArgument, info: graphql_base.ResolveInfo
    ) -> bytes:
        """Resolve agent argument value query.

        Args:
            self (models.AgentArgument): The agent argument object.
            info (graphql_base.ResolveInfo): GraphQL resolve info.

        Returns:
            common.Bytes: The value of the agent argument.
        """
        return self.value


class AgentArgumentsType(graphene.ObjectType):
    """Graphene object type for a list of agent arguments."""

    args = graphene.List(AgentArgumentType, required=True)


class AgentType(graphene_sqlalchemy.SQLAlchemyObjectType):
    """SQLAlchemy object type for an agent."""

    args = graphene.Field(AgentArgumentsType, required=True)

    class Meta:
        """Meta class for the agent object type."""

        model = models.Agent
        only_fields = (
            "id",
            "key",
        )

    def resolve_args(
        self: models.Agent, info: graphql_base.ResolveInfo
    ) -> AgentArgumentsType:
        """Resolve agent arguments query.

        Args:
            self (models.Agent): The agent object.
            info (graphql_base.ResolveInfo): GraphQL resolve info.

        Returns:
            AgentArgumentsType: List of agent arguments.
        """
        with models.Database() as session:
            args = session.query(models.AgentArgument).filter(
                models.AgentArgument.agent_id == self.id
            )
            return AgentArgumentsType(args=args)


class AgentsType(graphene.ObjectType):
    """Graphene object type for a list of agents."""

    agents = graphene.List(AgentType, required=True)


class AgentGroupType(graphene_sqlalchemy.SQLAlchemyObjectType):
    """SQLAlchemy object type for an agent group."""

    key = graphene.String()
    agents = graphene.Field(AgentsType, required=True)

    class Meta:
        """Meta class for the agent group object type."""

        model = models.AgentGroup

        only_fields = (
            "id",
            "name",
            "description",
            "created_time",
        )

    def resolve_key(self: models.AgentGroup, info: graphql_base.ResolveInfo) -> str:
        """Resolve key query.
        Args:
            self (models.AgentGroup): The agent group object.
            info (graphql_base.ResolveInfo): GraphQL resolve info.
        Returns:
            str: The key of the agent group.
        """
        return f"agentgroup//{self.name}"

    def resolve_agents(
        self: models.AgentGroup, info: graphql_base.ResolveInfo
    ) -> AgentsType:
        """Resolve agents query.
        Args:
            self (models.AgentGroup): The agent group object.
            info (graphql_base.ResolveInfo): GraphQL resolve info.
        Returns:
            AgentsType: List of agents.
        """
        with models.Database() as session:
            agents = (
                session.query(models.AgentGroup)
                .filter(models.AgentGroup.id == self.id)
                .first()
                .agents
            )
            return AgentsType(agents=agents)


class AgentGroupsType(graphene.ObjectType):
    agent_groups = graphene.List(AgentGroupType, required=True)
    page_info = graphene.Field(common.PageInfo, required=False)


class OxoAssetInputType(graphene.InputObjectType):
    android_file = OxoAndroidFileAssetInputType()
    ios_file = OxoIOSFileAssetInputType()
    android_store = OxoAndroidStoreAssetInputType()
    ios_store = OxoIOSStoreAssetInputType()
    url = OxoUrlAssetInputType()
    network = OxoNetworkAssetInputType()


class AgentArgumentInputType(graphene.InputObjectType):
    """Input object type for an agent argument."""

    name = graphene.String(required=True)
    type = graphene.String(required=True)
    description = graphene.String(required=False)
    value = common.Bytes(required=False)


class AgentGroupAgentCreateInputType(graphene.InputObjectType):
    """Input object type for creating an agent group agent."""

    key = graphene.String(required=True)
    args = graphene.List(AgentArgumentInputType)


class AgentGroupCreateInputType(graphene.InputObjectType):
    """Input object type for creating an agent group."""

    name = graphene.String(required=True)
    description = graphene.String(required=True)
    agents = graphene.List(AgentGroupAgentCreateInputType, required=True)
