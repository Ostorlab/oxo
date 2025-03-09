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

    endpoint_url: str
    content: Optional[bytes] = None
    content_url: Optional[str] = None
    schema_type: Optional[str] = None

    def __str__(self) -> str:
        str_representation = CLASS_NAME
        if self.schema_type is not None:
            str_representation = f"{str_representation} ({self.schema_type})"
        str_representation = f"{str_representation}: {self.endpoint_url}"

        return str_representation

    @classmethod
    def from_dict(cls, data: dict[str, str | bytes]) -> "ApiSchema":
        """Constructs an ApiSchema asset from a dictionary."""

        def to_str(value: str | bytes | None) -> str | None:
            if value is None:
                return None
            if type(value) is bytes:
                value = value.decode()
            return str(value)

        endpoint_url = to_str(data.get("endpoint_url", ""))
        if endpoint_url == "":
            raise ValueError("endpoint_url is missing.")
        content_url = to_str(data.get("content_url"))
        content = data.get("content")
        schema_type = to_str(data.get("schema_type"))
        return cls(
            endpoint_url=endpoint_url,
            content=content,
            content_url=content_url,
            schema_type=schema_type,
        )

    @property
    def proto_field(self) -> str:
        return PROTO_FIELD
