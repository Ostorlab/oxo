"""API Schema asset."""

import dataclasses
from typing import Optional

from ostorlab.assets import asset

PROTO_FIELD = "api_schema"
CLASS_NAME = "API Schema"


@dataclasses.dataclass
@asset.selector("v3.asset.file.api_schema")
class ApiSchema(asset.Asset):
    """API Schema target asset."""

    def __init__(
        self,
        endpoint_url: str,
        content: Optional[bytes] = None,
        content_url: Optional[str] = None,
        schema_type: Optional[str] = None,
    ):
        self.content = content
        self.endpoint_url = endpoint_url
        self.schema_type = schema_type
        self.content_url = content_url

    def __str__(self) -> str:
        str_representation = CLASS_NAME
        if self.schema_type is not None:
            str_representation = f"{str_representation} ({self.schema_type})"
        str_representation = f"{str_representation}: {self.endpoint_url}"

        return str_representation

    @property
    def proto_field(self) -> str:
        return PROTO_FIELD
