import graphene


class ScanOrderByEnum(graphene.Enum):
    """Enum for the elements to order a scan by."""

    ScanId = 1
    Title = 2
    CreatedTime = 3
    Progress = 4


class ScanType(graphene.ObjectType):
    """Graphene object type for a scan."""

    id = graphene.Int()
    title = graphene.String()
    asset = graphene.String()
    progress = graphene.String()
    created_time = graphene.DateTime()


class ScansType(graphene.ObjectType):
    """Graphene object type for a list of scans."""

    scans = graphene.List(ScanType, required=True)


class VulnerabilityOrderByEnum(graphene.Enum):
    """Enum for the elements to order a vulnerability by."""

    VulnerabilityId = 1
    Title = 2
    RiskRating = 3


class VulnerabilityType(graphene.ObjectType):
    """Graphene object type for a vulnerability."""

    id = graphene.Int()
    technical_detail = graphene.String()
    risk_rating = graphene.String()
    cvss_v3_vector = graphene.String()
    dna = graphene.String()
    title = graphene.String()
    short_description = graphene.String()
    description = graphene.String()
    recommendation = graphene.String()
    references = graphene.String()
    location = graphene.String()


class VulnerabilitiesType(graphene.ObjectType):
    """Graphene object type for a list of vulnerabilities."""

    vulnerabilities = graphene.List(VulnerabilityType, required=True)
