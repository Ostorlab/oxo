import graphene


class ScanOrderByEnum(graphene.Enum):
    ScanId = 1
    Title = 2
    CreatedTime = 3
    RiskRating = 4
    Progress = 6


class ScanType(graphene.ObjectType):
    id = graphene.Int()
    title = graphene.String()
    asset = graphene.String()
    progress = graphene.String()
    created_time = graphene.DateTime()


class ScansType(graphene.ObjectType):
    scans = graphene.List(ScanType, required=True)


class VulnerabilityOrderByEnum(graphene.Enum):
    VulnerabilityId = 1
    Title = 2
    RiskRating = 3


class VulnerabilityType(graphene.ObjectType):
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
    vulnerabilities = graphene.List(VulnerabilityType, required=True)
