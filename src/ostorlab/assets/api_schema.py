"""API Schema asset."""

import dataclasses

from ostorlab.assets import asset

PROTO_FIELD = "api_schema"
CLASS_NAME = "API Schema"


@dataclasses.dataclass
@asset.selector("v3.asset.file.api_schema")
class ApiSchema(asset.Asset):
    """API Schema target asset."""

    endpoint_url: str
    content: bytes | None = None
    content_url: str | None = None
    schema_type: str | None = None

    def __str__(self) -> str:
        str_representation = CLASS_NAME
        if self.schema_type is not None:
            str_representation = f"{str_representation} ({self.schema_type})"
        str_representation = f"{str_representation}: {self.endpoint_url}"

        return str_representation

    @property
    def proto_field(self) -> str:
        return PROTO_FIELD
