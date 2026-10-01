"""Google Gemini API and Google Vertex AI (managed Gemini) providers."""

from __future__ import annotations

from typing import Any

from google.oauth2 import service_account
from pydantic_ai import models
from pydantic_ai.models import google
from pydantic_ai.providers import google as google_provider
from pydantic_ai.providers import google_cloud as google_cloud_provider

from ostorlab.ai import credentials
from ostorlab.ai import errors
from ostorlab.ai.providers import base

VERTEX_AI_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]

_VERTEX_LABEL = "Google Vertex provider"


def build_google(request: base.BuildRequest) -> models.Model:
    """Build a Gemini API model (``google`` and its ``gemini`` alias)."""
    return google.GoogleModel(
        model_name=request.model_name,
        provider=google_provider.GoogleProvider(
            api_key=request.credential,
        ),
        settings=request.settings,
    )


def build_google_vertex(request: base.BuildRequest) -> models.Model:
    """Build a Vertex AI model from an Express key or a service-account JSON.

    The credential accepts three forms:
      - a plain Vertex Express key string.
      - a JSON object ``{"api_key": ...}``, which must not also carry ``project`` or
        ``location``.
      - a JSON object holding a ``service_account`` (or the service account itself, via
        ``type: service_account``), with an optional top-level ``project`` (else read
        from the service account's ``project_id``) and a required top-level
        ``location``.
    """
    return google.GoogleModel(
        model_name=request.model_name,
        provider=_build_vertex_provider(request),
        settings=request.settings,
    )


def build_service_account_credentials(
    service_account_info: dict[str, Any],
    model: str,
    provider_label: str = _VERTEX_LABEL,
) -> service_account.Credentials:
    """Build scoped Vertex credentials, failing at build time rather than at request time."""
    try:
        scoped_credentials: service_account.Credentials = (
            service_account.Credentials.from_service_account_info(  # type: ignore[no-untyped-call]
                service_account_info,
                scopes=VERTEX_AI_SCOPES,
            )
        )
    except (ValueError, KeyError) as exc:
        raise errors.ModelConfigurationError(
            f"Failed to build service account credentials for {provider_label} "
            f"(model={model}): {exc}"
        ) from exc
    return scoped_credentials


def _build_vertex_provider(
    request: base.BuildRequest,
) -> google_cloud_provider.GoogleCloudProvider:
    model = request.model_name
    stripped_credential = request.credential.strip()
    # Anything JSON-shaped is parsed, so a malformed object or an array fails here
    # instead of being sent to Vertex as an Express key.
    if stripped_credential.startswith(("{", "[")) is False:
        return google_cloud_provider.GoogleCloudProvider(api_key=stripped_credential)

    creds = credentials.parse_json_object(stripped_credential, _VERTEX_LABEL, model)
    if "api_key" in creds and (
        "service_account" in creds or creds.get("type") == "service_account"
    ):
        raise errors.ModelConfigurationError(
            "Google Vertex 'api_key' cannot be combined with 'service_account' "
            f"(model={model})."
        )
    if "api_key" in creds:
        if creds.get("project") is not None or creds.get("location") is not None:
            raise errors.ModelConfigurationError(
                "Google Vertex 'api_key' cannot be combined with 'project' or "
                f"'location' (model={model})."
            )
        if isinstance(creds["api_key"], str) is False or creds["api_key"].strip() == "":
            raise errors.ModelConfigurationError(
                f"Google Vertex 'api_key' must be a non-empty string (model={model})."
            )
        return google_cloud_provider.GoogleCloudProvider(
            api_key=creds["api_key"].strip()
        )

    service_account_info = _extract_service_account_info(creds, model)
    project = (
        creds.get("project")
        if creds.get("project") is not None
        else service_account_info.get("project_id")
    )
    if project is None:
        raise errors.ModelConfigurationError(
            "Missing 'project' for Google Vertex provider: provide a top-level "
            f"'project' or a 'project_id' in the service account (model={model})."
        )
    location = creds.get("location")
    if location is None:
        raise errors.ModelConfigurationError(
            "Missing 'location' for Google Vertex provider: provide a top-level "
            f"'location' in the service account (model={model})."
        )
    return google_cloud_provider.GoogleCloudProvider(
        credentials=build_service_account_credentials(service_account_info, model),
        project=project,
        location=location,
    )


def _extract_service_account_info(creds: dict[str, Any], model: str) -> dict[str, Any]:
    """Return the service account object, whether nested or supplied inline."""
    if isinstance(creds.get("service_account"), dict):
        return dict(creds["service_account"])
    if creds.get("type") == "service_account":
        return dict(creds)
    raise errors.ModelConfigurationError(
        "Missing required credential 'service_account' or 'api_key' for Google "
        f"Vertex provider (model={model})."
    )
