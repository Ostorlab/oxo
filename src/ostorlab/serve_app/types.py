"""Graphene types for the local runtime."""

from __future__ import annotations

import collections
import enum
import io
from typing import Any
from typing import Optional
from typing import Protocol
from typing import cast

import graphene
import graphene_sqlalchemy
import ruamel
from graphene_file_upload import scalars
from graphql.execution import base as graphql_base
from sqlalchemy import orm
from werkzeug import datastructures

from ostorlab.runtimes.local.models import models
from ostorlab.serve_app import common
from ostorlab.utils import risk_rating as utils_rik_rating

DEFAULT_NUMBER_ELEMENTS = 15
RISK_RATINGS_ORDER = {
    "CRITICAL": 8,
    "HIGH": 7,
    "MEDIUM": 6,
    "LOW": 5,
    "POTENTIALLY": 4,
    "HARDENING": 3,
    "SECURE": 2,
    "IMPORTANT": 1,
    "INFO": 0,
}
YAML_WIDTH = 100000000


class OxoScanOrderByEnum(graphene.Enum):
    """Enum for the elements to order a scan by."""

    ScanId = enum.auto()
    Title = enum.auto()
    CreatedTime = enum.auto()
    Progress = enum.auto()


OxoAssetTypeEnum = graphene.Enum.from_enum(models.AssetTypeEnum)


class AgentGroupOrderByEnum(graphene.Enum):
    AgentGroupId = enum.auto()
    Name = enum.auto()
    CreatedTime = enum.auto()


class OxoReferenceType(common.ObjectType):
    """Graphene object type for a reference."""

    title = graphene.String()
    url = graphene.String()


class OxoKnowledgeBaseVulnerabilityType(common.ObjectType):
    """SQLAlchemy object type for a knowledge base vulnerability."""

    references = graphene.List(OxoReferenceType)
    title = graphene.String()
    short_description = graphene.String()
    description = graphene.String()
    recommendation = graphene.String()


OxoRiskRatingEnum = graphene.Enum(
    "OxoRiskRating",
    [(risk.name.upper(), i) for i, risk in enumerate(utils_rik_rating.RiskRating)],
)


class OxoVulnerabilityType(graphene_sqlalchemy.SQLAlchemyObjectType):
    """SQLAlchemy object type for a vulnerability."""

    detail = graphene.Field(OxoKnowledgeBaseVulnerabilityType, required=False)
    cvss_v3_base_score = graphene.Float(required=False)
    risk_rating = graphene.Field(OxoRiskRatingEnum, required=False)

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

    @staticmethod
    def resolve_cvss_v3_base_score(
        root: models.Vulnerability, info: graphql_base.ResolveInfo
    ) -> Optional[float]:
        """Resolve CVSS v3 base score query.

        Args:
            self (models.Vulnerability): The vulnerability object.
            info (graphql_base.ResolveInfo): GraphQL resolve info.

        Returns:
            float: The CVSS v3 base score.
        """
        return common.compute_cvss_v3_base_score(root.cvss_v3_vector)

    @staticmethod
    def resolve_detail(
        root: models.Vulnerability, info: graphql_base.ResolveInfo
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
                .filter(models.Reference.vulnerability_id == root.id)
                .all()
            )

            return OxoKnowledgeBaseVulnerabilityType(
                title=root.title,
                short_description=root.short_description,
                description=root.description,
                recommendation=root.recommendation,
                references=[
                    OxoReferenceType(title=ref.title, url=ref.url) for ref in references
                ],
            )

    @staticmethod
    def resolve_risk_rating(
        root: models.Vulnerability, info: graphql_base.ResolveInfo
    ) -> Optional[enum.Enum]:
        """Resolve risk rating of vulnerability"""
        try:
            return cast(EnumLookup, OxoRiskRatingEnum)[
                cast(utils_rik_rating.RiskRating, root.risk_rating).name
            ]
        except KeyError:
            return None


class OxoVulnerabilitiesType(common.ObjectType):
    """Graphene object type for a list of vulnerabilities."""

    vulnerabilities = graphene.List(OxoVulnerabilityType, required=True)
    page_info = graphene.Field(common.PageInfo, required=False)


class OxoAggregatedKnowledgeBaseVulnerabilityType(common.ObjectType):
    """Graphene object type for an aggregated knowledge base vulnerability."""

    highest_risk_rating = graphene.Field(OxoRiskRatingEnum)
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

    @staticmethod
    def resolve_highest_risk_rating(
        root: AggregatedKnowledgeBase, info: graphql_base.ResolveInfo
    ) -> Optional[enum.Enum]:
        try:
            return cast(EnumLookup, OxoRiskRatingEnum)[root.highest_risk_rating.name]
        except KeyError:
            return None

    @staticmethod
    def resolve_vulnerabilities(
        root: AggregatedKnowledgeBase,
        info: graphql_base.ResolveInfo,
        detail_titles: list[str] | None = None,
        page: int | None = None,
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

        vulnerabilities = root.vulnerabilities.vulnerabilities.order_by(
            models.Vulnerability.id
        )

        if detail_titles is not None and len(detail_titles) > 0:
            vulnerabilities = vulnerabilities.filter(
                models.Vulnerability.title.in_(detail_titles)
            )

        if page is not None and number_elements > 0:
            p = common.Paginator(vulnerabilities, number_elements)
            result_page = p.get_page(page)
            page_info = common.PageInfo(
                count=p.count,
                num_pages=p.num_pages,
                has_next=result_page.has_next(),
                has_previous=result_page.has_previous(),
            )
            return OxoVulnerabilitiesType(
                vulnerabilities=result_page, page_info=page_info
            )
        else:
            return OxoVulnerabilitiesType(vulnerabilities=vulnerabilities)


class OxoAndroidStoreAssetType(graphene_sqlalchemy.SQLAlchemyObjectType):
    class Meta:
        model = models.AndroidStore
        only_fields = ("id", "package_name", "application_name")

    @staticmethod
    def resolve_package_name(
        root: models.AndroidStore, info: graphql_base.ResolveInfo
    ) -> Optional[str]:
        with models.Database() as session:
            return cast(
                models.AndroidStore, session.query(models.AndroidStore).get(root.id)
            ).package_name

    @staticmethod
    def resolve_application_name(
        root: models.AndroidStore, info: graphql_base.ResolveInfo
    ) -> Optional[str]:
        with models.Database() as session:
            return cast(
                models.AndroidStore, session.query(models.AndroidStore).get(root.id)
            ).application_name


class OxoAndroidStoreAssetInputType(graphene.InputObjectType):
    package_name = graphene.String()
    application_name = graphene.String()


class OxoIOSStoreAssetType(graphene_sqlalchemy.SQLAlchemyObjectType):
    class Meta:
        model = models.IosStore
        only_fields = ("id", "bundle_id", "application_name")

    @staticmethod
    def resolve_bundle_id(
        root: models.IosStore, info: graphql_base.ResolveInfo
    ) -> Optional[str]:
        with models.Database() as session:
            return cast(
                models.IosStore, session.query(models.IosStore).get(root.id)
            ).bundle_id

    @staticmethod
    def resolve_application_name(
        root: models.IosStore, info: graphql_base.ResolveInfo
    ) -> Optional[str]:
        with models.Database() as session:
            return cast(
                models.IosStore, session.query(models.IosStore).get(root.id)
            ).application_name


class OxoIOSStoreAssetInputType(graphene.InputObjectType):
    bundle_id = graphene.String()
    application_name = graphene.String()


class OxoAndroidFileAssetType(graphene_sqlalchemy.SQLAlchemyObjectType):
    class Meta:
        model = models.AndroidFile
        only_fields = ("id", "package_name", "path")

    @staticmethod
    def resolve_package_name(
        root: models.AndroidFile, info: graphql_base.ResolveInfo
    ) -> Optional[str]:
        with models.Database() as session:
            return cast(
                models.AndroidFile, session.query(models.AndroidFile).get(root.id)
            ).package_name

    @staticmethod
    def resolve_path(
        root: models.AndroidFile, info: graphql_base.ResolveInfo
    ) -> Optional[str]:
        with models.Database() as session:
            return cast(
                models.AndroidFile, session.query(models.AndroidFile).get(root.id)
            ).path


class OxoAndroidFileAssetInputType(graphene.InputObjectType):
    file = scalars.Upload()
    package_name = graphene.String()


class OxoIOSFileAssetType(graphene_sqlalchemy.SQLAlchemyObjectType):
    class Meta:
        model = models.IosFile
        only_fields = ("id", "bundle_id", "path")

    @staticmethod
    def resolve_bundle_id(
        root: models.IosFile, info: graphql_base.ResolveInfo
    ) -> Optional[str]:
        with models.Database() as session:
            return cast(
                models.IosFile, session.query(models.IosFile).get(root.id)
            ).bundle_id

    @staticmethod
    def resolve_path(
        root: models.IosFile, info: graphql_base.ResolveInfo
    ) -> Optional[str]:
        with models.Database() as session:
            return cast(models.IosFile, session.query(models.IosFile).get(root.id)).path


class OxoIOSFileAssetInputType(graphene.InputObjectType):
    file = scalars.Upload()
    bundle_id = graphene.String()


class OxoLinkAssetType(graphene_sqlalchemy.SQLAlchemyObjectType):
    class Meta:
        model = models.Link
        only_fields = ("url", "method")


class OxoUrlsAssetType(graphene_sqlalchemy.SQLAlchemyObjectType):
    links = graphene.List(OxoLinkAssetType, required=False)

    class Meta:
        model = models.Urls
        only_fields = ("id",)

    @staticmethod
    def resolve_links(
        root: models.Urls, info: graphql_base.ResolveInfo
    ) -> list[OxoLinkAssetType]:
        with models.Database() as session:
            links = session.query(models.Link).filter_by(urls_asset_id=root.id).all()
            return [
                OxoLinkAssetType(url=link.url, method=link.method) for link in links
            ]


class OxoIPRangeAssetType(graphene_sqlalchemy.SQLAlchemyObjectType):
    class Meta:
        model = models.IPRange
        only_fields = ("host", "mask")


class OxoNetworkAssetType(graphene_sqlalchemy.SQLAlchemyObjectType):
    networks = graphene.List(OxoIPRangeAssetType, required=False)

    class Meta:
        model = models.Network
        only_fields = ("id",)

    @staticmethod
    def resolve_networks(
        root: models.Network, info: graphql_base.ResolveInfo
    ) -> list[OxoIPRangeAssetType]:
        with models.Database() as session:
            ips = (
                session.query(models.IPRange).filter_by(network_asset_id=root.id).all()
            )
            return [OxoIPRangeAssetType(host=ip.host, mask=ip.mask) for ip in ips]


class OxoDomainNameAssetType(graphene_sqlalchemy.SQLAlchemyObjectType):
    class Meta:
        model = models.DomainName
        only_fields = "name"


class OxoDomainNameAssetsType(graphene_sqlalchemy.SQLAlchemyObjectType):
    domain_names = graphene.List(OxoDomainNameAssetType, required=False)

    class Meta:
        model = models.DomainAsset
        only_fields = ("id",)

    @staticmethod
    def resolve_domain_names(
        root: models.DomainAsset, info: graphql_base.ResolveInfo
    ) -> list[OxoDomainNameAssetType]:
        """Resolve domain names query.

        Args:
            self: The domain asset object.
            info: GraphQL resolve info.

        Returns:
            List of domain names.
        """
        with models.Database() as session:
            domain_names = (
                session.query(models.DomainName)
                .filter_by(domain_asset_id=root.id)
                .all()
            )
            return [
                OxoDomainNameAssetType(name=domain_name.name)
                for domain_name in domain_names
            ]


class OxoAssetType(graphene.Union):
    class Meta:
        model = models.Asset
        types = (
            OxoAndroidFileAssetType,
            OxoIOSFileAssetType,
            OxoAndroidStoreAssetType,
            OxoIOSStoreAssetType,
            OxoUrlsAssetType,
            OxoNetworkAssetType,
            OxoDomainNameAssetsType,
        )


class OxoAgentArgumentType(graphene_sqlalchemy.SQLAlchemyObjectType):
    """Graphene object type for a list of agent arguments."""

    value = common.Bytes(required=False)

    class Meta:
        """Meta class for the agent arguments object type."""

        model = models.AgentArgument
        only_fields = (
            "name",
            "type",
            "description",
        )

    @staticmethod
    def resolve_value(
        root: models.AgentArgument, info: graphql_base.ResolveInfo
    ) -> Optional[bytes]:
        """Resolve agent argument value query.

        Args:
            self (models.AgentArgument): The agent argument object.
            info (graphql_base.ResolveInfo): GraphQL resolve info.

        Returns:
            common.Bytes: The value of the agent argument.
        """
        return root.value


class OxoAgentArgumentsType(common.ObjectType):
    """Graphene object type for a list of agent arguments."""

    args = graphene.List(OxoAgentArgumentType, required=True)


class OxoAgentType(graphene_sqlalchemy.SQLAlchemyObjectType):
    """SQLAlchemy object type for an agent."""

    args = graphene.Field(OxoAgentArgumentsType, required=True)

    class Meta:
        """Meta class for the agent object type."""

        model = models.Agent
        only_fields = ("key",)

    @staticmethod
    def resolve_args(
        root: models.Agent, info: graphql_base.ResolveInfo
    ) -> OxoAgentArgumentsType:
        """Resolve agent arguments query.

        Args:
            self (models.Agent): The agent object.
            info (graphql_base.ResolveInfo): GraphQL resolve info.

        Returns:
            AgentArgumentsType: List of agent arguments.
        """
        with models.Database() as session:
            args = session.query(models.AgentArgument).filter(
                models.AgentArgument.agent_id == root.id
            )
            return OxoAgentArgumentsType(args=args)


class OxoAgentsType(common.ObjectType):
    """Graphene object type for a list of agents."""

    agents = graphene.List(OxoAgentType, required=True)
    page_info = graphene.Field(
        common.PageInfo,
        required=False,
    )


class OxoAgentGroupType(graphene_sqlalchemy.SQLAlchemyObjectType):
    """SQLAlchemy object type for an agent group."""

    key = graphene.String()
    agents = graphene.Field(
        OxoAgentsType,
        required=True,
        page=graphene.Int(required=False),
        number_elements=graphene.Int(required=False),
    )
    asset_types = graphene.List(graphene.String)
    yaml_source = graphene.String()

    class Meta:
        """Meta class for the agent group object type."""

        model = models.AgentGroup

        only_fields = (
            "id",
            "name",
            "description",
            "created_time",
        )

    @staticmethod
    def resolve_key(root: models.AgentGroup, info: graphql_base.ResolveInfo) -> str:
        """Resolve key query.
        Args:
            self (models.AgentGroup): The agent group object.
            info (graphql_base.ResolveInfo): GraphQL resolve info.
        Returns:
            str: The key of the agent group.
        """
        return (
            f"agentgroup//{root.name}"
            if root.name is not None
            else f"agentgroup//{root.id}"
        )

    @staticmethod
    def resolve_agents(
        root: models.AgentGroup,
        info: graphql_base.ResolveInfo,
        page: int | None = None,
        number_elements: int = DEFAULT_NUMBER_ELEMENTS,
    ) -> OxoAgentsType:
        """Resolve agents query.
        Args:
            self (models.AgentGroup): The agent group object.
            info (graphql_base.ResolveInfo): GraphQL resolve info.
        Returns:
            AgentsType: List of agents.
        """
        if number_elements <= 0:
            return OxoAgentsType(agents=[])

        with models.Database() as session:
            group = cast(
                models.AgentGroup,
                session.query(models.AgentGroup)
                .filter(models.AgentGroup.id == root.id)
                .first(),
            )
            agents = group.agents
            if page is not None and number_elements > 0:
                p = common.Paginator(agents, number_elements)
                result_page = p.get_page(page)
                page_info = common.PageInfo(
                    count=p.count,
                    num_pages=p.num_pages,
                    has_next=result_page.has_next(),
                    has_previous=result_page.has_previous(),
                )
                return OxoAgentsType(agents=result_page, page_info=page_info)
            else:
                return OxoAgentsType(agents=agents)

    @staticmethod
    def resolve_asset_types(
        root: models.AgentGroup, info: graphql_base.ResolveInfo
    ) -> list[str]:
        """Resolve asset types query.
        Args:
            self (models.AgentGroup): The agent group object.
            info (graphql_base.ResolveInfo): GraphQL resolve info.
        Returns:
            List[str]: The asset types of the agent group.
        """
        with models.Database() as session:
            asset_types = cast(
                models.AgentGroup, session.query(models.AgentGroup).get(root.id)
            ).asset_types
            return [
                cast(models.AssetTypeEnum, asset.type).name for asset in asset_types
            ]

    @staticmethod
    def resolve_yaml_source(
        root: models.AgentGroup, info: graphql_base.ResolveInfo
    ) -> str:
        """Resolve yaml source query.
        Args:
            self: The agent group object.
            info: GraphQL resolve info.
        Returns:
            The yaml source of the agent group.
        """
        yaml = ruamel.yaml.YAML(typ="safe")
        yaml.width = YAML_WIDTH
        agent_group_definition: dict[str, Any] = {"kind": "AgentGroup", "agents": []}

        if root.name is not None:
            agent_group_definition["name"] = root.name

        if root.description is not None:
            agent_group_definition["description"] = root.description

        with models.Database() as session:
            agent_group = cast(
                models.AgentGroup, session.query(models.AgentGroup).get(root.id)
            )
            agents = agent_group.agents
            for agent in agents:
                agent_definition: dict[str, Any] = {
                    "key": agent.key,
                    "args": [],
                }

                args = (
                    session.query(models.AgentArgument)
                    .filter_by(agent_id=agent.id)
                    .all()
                )
                for arg in args:
                    value = models.AgentArgument.from_bytes(arg.type, arg.value)
                    arg_dict = {
                        "name": arg.name,
                        "type": arg.type,
                        "description": arg.description,
                    }
                    if value is not None:
                        arg_dict["value"] = value
                    agent_definition["args"].append(arg_dict)

                agent_group_definition["agents"].append(agent_definition)

        string_yaml_io = io.StringIO()
        yaml.dump(agent_group_definition, string_yaml_io)
        agent_group_definition_yaml = string_yaml_io.getvalue()
        return agent_group_definition_yaml


class OxoAgentGroupsType(common.ObjectType):
    agent_groups = graphene.List(OxoAgentGroupType, required=True)
    page_info = graphene.Field(common.PageInfo, required=False)


class OxoIPRangeInputType(graphene.InputObjectType):
    host = graphene.String(required=True)
    mask = graphene.String(required=False)


class OxoLinkInputType(graphene.InputObjectType):
    url = graphene.String(required=True)
    method = graphene.String(required=False, default_value="GET")


class OxoDomainNameInputType(graphene.InputObjectType):
    name = graphene.String(required=True)


class OxoAssetInputType(graphene.InputObjectType):
    android_apk_file = graphene.List(OxoAndroidFileAssetInputType)
    android_aab_file = graphene.List(OxoAndroidFileAssetInputType)
    ios_file = graphene.List(OxoIOSFileAssetInputType)
    android_store = graphene.List(OxoAndroidStoreAssetInputType)
    ios_store = graphene.List(OxoIOSStoreAssetInputType)
    link = graphene.List(OxoLinkInputType)
    ip = graphene.List(OxoIPRangeInputType)
    domain = graphene.List(OxoDomainNameInputType)


class OxoAgentArgumentInputType(graphene.InputObjectType):
    """Input object type for an agent argument."""

    name = graphene.String(required=True)
    type = graphene.String(required=True)
    description = graphene.String(required=False)
    value = common.Bytes(required=False)


class OxoAgentGroupAgentCreateInputType(graphene.InputObjectType):
    """Input object type for creating an agent group agent."""

    key = graphene.String(required=True)
    args = graphene.List(OxoAgentArgumentInputType, required=False, default_value=[])


class OxoAgentGroupCreateInputType(graphene.InputObjectType):
    """Input object type for creating an agent group."""

    name = graphene.String(required=False)
    description = graphene.String(required=True)
    agents = graphene.List(OxoAgentGroupAgentCreateInputType, required=True)
    asset_types = graphene.List(OxoAssetTypeEnum, required=False, default_value=[])


class OxoAgentScanInputType(graphene.InputObjectType):
    """Input object type for scan"""

    title = graphene.String(required=False)
    asset_ids = graphene.List(graphene.Int, required=True)
    agent_group_id = graphene.Int(required=True)


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
    risk_rating = graphene.String()
    assets = graphene.List(OxoAssetType)
    agent_group = graphene.Field(OxoAgentGroupType)

    class Meta:
        """Meta class for the scan object type."""

        model = models.Scan
        description = "Scan object."
        only_fields = (
            "id",
            "title",
            "created_time",
        )

    @staticmethod
    def resolve_progress(root: models.Scan, info: graphql_base.ResolveInfo) -> str:
        """Resolve progress query.

        Args:
            self (models.Scan): The scan object.
            info (graphql_base.ResolveInfo): GraphQL resolve info.

        Returns:
            str: The progress of the scan.
        """

        return cast(models.ScanProgress, root.progress).name

    @staticmethod
    def resolve_risk_rating(
        root: models.Scan, info: graphql_base.ResolveInfo
    ) -> str | None:
        """Resolve risk rating query.
        Args:
            self (models.Scan): The scan object.
            info (graphql_base.ResolveInfo): GraphQL resolve info.
        Returns:
            str: The risk rating of the scan.
        """
        return root.risk_rating.name if root.risk_rating is not None else None

    @staticmethod
    def resolve_assets(
        root: models.Scan,
        info: graphql_base.ResolveInfo,
    ) -> list[models.Asset]:
        """Resolve asset query.

        Args:
            self (models.Scan): The scan object.
            info (graphql_base.ResolveInfo): GraphQL resolve info.

        Returns:
            List[OxoAssetType]: The asset of the scan.
        """
        with models.Database() as session:
            assets = (
                cast("orm.Query[models.Asset]", session.query(models.Asset))
                .filter_by(scan_id=root.id)
                .all()
            )
            return assets

    @staticmethod
    def resolve_vulnerabilities(
        root: models.Scan,
        info: graphql_base.ResolveInfo,
        detail_titles: list[str] | None = None,
        vuln_ids: list[int] | None = None,
        page: int | None = None,
        number_elements: int = DEFAULT_NUMBER_ELEMENTS,
    ) -> OxoVulnerabilitiesType:
        """Resolve vulnerabilities query.

        Args:
            self: The scan object.
            info: GraphQL resolve info.
            detail_titles: List of detail titles. Defaults to None.
            vuln_ids: List of vulnerability ids. Defaults to None.
            page: Page number. Defaults to None.
            number_elements: Number of elements. Defaults to DEFAULT_NUMBER_ELEMENTS.

        Returns:
            OxoVulnerabilitiesType: List of vulnerabilities.
        """
        if number_elements <= 0:
            return OxoVulnerabilitiesType(vulnerabilities=[])

        with models.Database() as session:
            vulnerabilities = session.query(models.Vulnerability).filter(
                models.Vulnerability.scan_id == root.id
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
                result_page = p.get_page(page)
                page_info = common.PageInfo(
                    count=p.count,
                    num_pages=p.num_pages,
                    has_next=result_page.has_next(),
                    has_previous=result_page.has_previous(),
                )
                return OxoVulnerabilitiesType(
                    vulnerabilities=result_page, page_info=page_info
                )
            else:
                return OxoVulnerabilitiesType(vulnerabilities=vulnerabilities)

    @staticmethod
    def resolve_kb_vulnerabilities(
        root: models.Scan,
        info: graphql_base.ResolveInfo,
        detail_title: str | None = None,
        page: int | None = None,
        number_elements: int = DEFAULT_NUMBER_ELEMENTS,
    ) -> list[OxoAggregatedKnowledgeBaseVulnerabilityType]:
        """Resolve knowledge base vulnerabilities query.

        Args:
            self: The scan object.
            info: GraphQL resolve info.
            detail_title: The detail title. Defaults to None.

        Returns:
            list[OxoAggregatedKnowledgeBaseVulnerabilityType]: List of aggregated knowledge base vulnerabilities.
        """
        aggregated_kb = OxoScanType._build_kb_vulnerabilities(root, detail_title)
        return aggregated_kb

    @staticmethod
    def resolve_message_status(
        root: models.Scan, info: graphql_base.ResolveInfo
    ) -> Optional[str]:
        """Resolve message status query.

        Args:
            self (models.Scan): The scan object.
            info (graphql_base.ResolveInfo): GraphQL resolve info.

        Returns:
            str: The message status of the scan.
        """
        with models.Database() as session:
            scan_statuses = session.query(models.ScanStatus).filter(
                models.ScanStatus.scan_id == root.id
            )
            message_statuses = [
                s.value for s in scan_statuses if s.key == "message_status"
            ]
            if message_statuses is not None and len(message_statuses) > 0:
                return cast(Optional[str], message_statuses[-1])
        return None

    @staticmethod
    def resolve_agent_group(
        root: models.Scan, info: graphql_base.ResolveInfo
    ) -> Optional[models.AgentGroup]:
        """Resolve agent group.

        Args:
            self: The scan object.
            info: GraphQL resolve info.

        Returns:
            str: The message status of the scan.
        """
        with models.Database() as session:
            if root.agent_group_id is not None:
                return cast(
                    Optional[models.AgentGroup],
                    session.query(models.AgentGroup).get(root.agent_group_id),
                )
        return None

    @staticmethod
    def _build_kb_vulnerabilities(
        scan: models.Scan, detail_title: str | None = None
    ) -> list[OxoAggregatedKnowledgeBaseVulnerabilityType]:
        """Build knowledge base vulnerabilities.

        Args:
            scan: The scan object.
            detail_title: The detail title. Defaults to None.

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
                        key=lambda vector: cast(
                            float, common.compute_cvss_v3_base_score(vector)
                        ),
                    )
                else:
                    highest_cvss_v3_vector = kb.cvss_v3_vector or None
                references = (
                    session.query(models.Reference)
                    .filter(
                        models.Reference.vulnerability_id
                        == cast(models.Vulnerability, kb_vulnerabilities.first()).id
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


class OxoScansType(common.ObjectType):
    """Graphene object type for a list of scans."""

    scans = graphene.List(OxoScanType, required=True)
    page_info = graphene.Field(common.PageInfo, required=False)


class EnumLookup(Protocol):
    """Name lookup on a dynamically constructed Graphene enum."""

    def __getitem__(self, name: str) -> enum.Enum: ...


class VulnerabilitiesData(Protocol):
    """Query backing a GraphQL vulnerability list."""

    vulnerabilities: orm.Query[models.Vulnerability]


class AggregatedKnowledgeBase(Protocol):
    """Data passed to aggregated vulnerability resolvers."""

    highest_risk_rating: utils_rik_rating.RiskRating
    vulnerabilities: VulnerabilitiesData


class AndroidStoreInput(Protocol):
    """Decoded Android store input."""

    package_name: str
    application_name: Optional[str]


class IOSStoreInput(Protocol):
    """Decoded iOS store input."""

    bundle_id: str
    application_name: Optional[str]


class AndroidFileInput(Protocol):
    """Decoded uploaded Android input."""

    file: datastructures.FileStorage
    package_name: Optional[str]


class IOSFileInput(Protocol):
    """Decoded uploaded iOS input."""

    file: datastructures.FileStorage
    bundle_id: Optional[str]


class AssetInput(Protocol):
    """Decoded GraphQL asset input container."""

    android_apk_file: Optional[list[AndroidFileInput]]
    android_aab_file: Optional[list[AndroidFileInput]]
    ios_file: Optional[list[IOSFileInput]]
    android_store: Optional[list[AndroidStoreInput]]
    ios_store: Optional[list[IOSStoreInput]]
    link: Optional[list[dict[str, str]]]
    ip: Optional[list[dict[str, str | int | None]]]
    domain: Optional[list[dict[str, str]]]


class AgentGroupInput(Protocol):
    """Decoded GraphQL agent group input container."""

    name: Optional[str]
    description: str
    agents: list[models.AgentGroupAgent]
    asset_types: list[str]


class AgentScanInput(Protocol):
    """Decoded GraphQL scan input container."""

    title: Optional[str]
    asset_ids: list[int]
    agent_group_id: int
