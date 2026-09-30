"""Unit tests for ostorlab.ai.providers.bedrock."""

from __future__ import annotations

import json

import pytest
from pydantic_ai.models import bedrock as pydantic_bedrock

from ostorlab.ai import errors
from ostorlab.ai import factory


@pytest.mark.parametrize(
    "credential",
    [
        {"region": "us-east-1", "api_key": "bearer"},
        {
            "region": "us-east-1",
            "aws_access_key_id": "AKIA",
            "aws_secret_access_key": "secret",
        },
    ],
)
def testBuildModel_whenBedrockCredentialValid_shouldBuildConverseModelInRegion(
    credential: dict[str, str],
) -> None:
    model = factory.build_model("aws_bedrock/anthropic.claude", json.dumps(credential))

    assert isinstance(model, pydantic_bedrock.BedrockConverseModel)
    assert model.client.meta.region_name == "us-east-1"


@pytest.mark.parametrize(
    ("credential", "message"),
    [
        ("{not json", "Invalid JSON"),
        (json.dumps(["region"]), "must be a JSON object"),
        (json.dumps({"api_key": "k"}), "'region'"),
        (
            json.dumps({"region": "us-east-1", "aws_access_key_id": "AKIA"}),
            "aws_secret_access_key",
        ),
    ],
)
def testBuildModel_whenBedrockCredentialInvalid_shouldRaise(
    credential: str, message: str
) -> None:
    with pytest.raises(errors.ModelConfigurationError, match=message):
        factory.build_model("aws_bedrock/anthropic.claude", credential)
