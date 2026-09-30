"""AWS Bedrock provider."""

from __future__ import annotations

from pydantic_ai import models
from pydantic_ai.models import bedrock
from pydantic_ai.providers import bedrock as bedrock_provider

from ostorlab.ai import credentials
from ostorlab.ai import errors
from ostorlab.ai.providers import base

_PROVIDER_LABEL = "Bedrock provider"


def build_aws_bedrock(request: base.BuildRequest) -> models.Model:
    """Build a Bedrock model from a JSON credential.

    The credential holds ``region`` plus either ``api_key`` (bearer token) or
    ``aws_access_key_id`` and ``aws_secret_access_key`` (IAM).
    """
    creds = credentials.parse_json_object(
        request.credential, _PROVIDER_LABEL, request.model_name
    )
    if "region" not in creds:
        raise errors.ModelConfigurationError(
            "Missing required credential 'region' for Bedrock provider."
        )
    if "api_key" in creds:
        provider = bedrock_provider.BedrockProvider(
            api_key=creds["api_key"],
            region_name=creds["region"],
        )
    else:
        credentials.require_keys(
            creds,
            ["aws_access_key_id", "aws_secret_access_key"],
            "Bedrock IAM auth",
        )
        provider = bedrock_provider.BedrockProvider(
            region_name=creds["region"],
            aws_access_key_id=creds["aws_access_key_id"],
            aws_secret_access_key=creds["aws_secret_access_key"],
        )
    return bedrock.BedrockConverseModel(
        model_name=request.model_name,
        provider=provider,
        settings=request.settings,
    )
