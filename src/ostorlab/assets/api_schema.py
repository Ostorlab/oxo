"""File asset."""

import dataclasses
from typing import Optional

from ostorlab.assets import asset


@dataclasses.dataclass
@asset.selector("v3.asset.file.api_schema")
class ApiSchema(asset.Asset):
    """API Schema target asset."""

    def __init__(
        self,
        content: Optional[bytes] = None,
        url: Optional[str] = None,
        schema_type: Optional[str] = None,
    ):
        self.content = content
        self.url = url
        self.schema_type = schema_type

    def __str__(self) -> str:
        str_representation = "API Schema"
        if self.schema_type is not None:
            str_representation = f"{str_representation}:{self.schema_type}"
        if self.url is not None:
            str_representation = f"{str_representation}:{self.url}"

        return str_representation

    @property
    def proto_field(self) -> str:
        return "api_schema"
