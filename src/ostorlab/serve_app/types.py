"""Graphene types for the local runtime."""

import collections
import enum
from typing import Optional, List

import graphene
import graphene_sqlalchemy
from graphql.execution import base as graphql_base

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


class OxoKnowledgeBaseVulnerabilityType(graphene_sqlalchemy.SQLAlchemyObjectType):
    """SQLAlchemy object type for a knowledge base vulnerability."""

    class Meta:
        """Meta class for the knowledge base vulnerability object type."""

        model = models.Vulnerability
        only_fields = (
            "title",
            "short_description",
            "description",
            "recommendation",
            "references",
        )


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
        return OxoKnowledgeBaseVulnerabilityType(
            title=self.title,
            short_description=self.short_description,
            description=self.description,
            recommendation=self.recommendation,
            references=self.references,
        )


class OxoVulnerabilitiesType(graphene.ObjectType):
    """Graphene object type for a list of vulnerabilities."""

    vulnerabilities = graphene.List(OxoVulnerabilityType, required=True)


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
                vulnerabilities = vulnerabilities.offset(
                    (page - 1) * number_elements
                ).limit(number_elements)
                return OxoVulnerabilitiesType(vulnerabilities=vulnerabilities)
            else:
                return OxoVulnerabilitiesType(vulnerabilities=vulnerabilities)

    def resolve_kb_vulnerabilities(
        self: models.Scan,
        info: graphql_base.ResolveInfo,
        detail_title: Optional[str] = None,
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
                vulnerabilities = vulnerabilities.filter(
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
                aggregated_kb.append(
                    OxoAggregatedKnowledgeBaseVulnerabilityType(
                        highest_risk_rating=highest_risk_rating,
                        highest_cvss_v3_vector=highest_cvss_v3_vector,
                        highest_cvss_v3_base_score=common.compute_cvss_v3_base_score(
                            highest_cvss_v3_vector
                        ),
                        kb=kb,
                        vulnerabilities=OxoVulnerabilitiesType(
                            vulnerabilities=vulnerabilities
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

    class Meta:
        """Meta class for the agent arguments object type."""

        model = models.AgentArgument
        only_fields = (
            "id",
            "name",
            "type",
            "description",
            "value",
        )


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
        return f"agentgroup/{self.name}"

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
