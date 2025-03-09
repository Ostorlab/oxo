"""API Schema asset."""

import dataclasses
from typing import Optional, Union

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
    def from_dict(cls, data: dict[str, Union[str, bytes]]) -> "ApiSchema":
        """Constructs an ApiSchema asset from a dictionary."""

        endpoint_url = data.get("endpoint_url", "")
        if endpoint_url == "":
            raise ValueError("endpoint_url is missing.")
        args = {
            "endpoint_url": endpoint_url.decode()
            if type(endpoint_url) is bytes
            else endpoint_url
        }
        content = data.get("content")
        if content is not None:
            args["content"] = content
        content_url = data.get("content_url")
        if content_url is not None:
            args["content_url"] = (
                content_url.decode() if type(content_url) is bytes else content_url
            )
        schema_type = data.get("schema_type")
        if schema_type is not None:
            args["schema_type"] = (
                schema_type.decode() if type(schema_type) is bytes else schema_type
            )
        return cls(**args)  # type: ignore

    @property
    def proto_field(self) -> str:
        return PROTO_FIELD
