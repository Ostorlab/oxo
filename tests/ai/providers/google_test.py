"""Unit tests for ostorlab.ai.providers.google."""

from __future__ import annotations

import json

import pytest
from pydantic_ai.models import google as pydantic_google

from ostorlab.ai import errors
from ostorlab.ai import factory

_MODEL = "google_vertex/gemini-3.1-pro-preview"


def testBuildModel_whenGoogleVertexExpressKey_shouldBuildVertexModel() -> None:
    model = factory.build_model(_MODEL, "fake-express-key")

    assert isinstance(model, pydantic_google.GoogleModel)
    assert model.model_name == "gemini-3.1-pro-preview"
    assert model.system == "google-cloud"


def testBuildModel_whenGoogleVertexJsonApiKey_shouldBuildVertexModel() -> None:
    model = factory.build_model(_MODEL, json.dumps({"api_key": " fake-key "}))

    assert isinstance(model, pydantic_google.GoogleModel)
    assert model.system == "google-cloud"


@pytest.mark.parametrize("nested", [True, False])
def testBuildModel_whenGoogleVertexServiceAccount_shouldBuildVertexModel(
    fake_service_account_info: dict[str, str], nested: bool
) -> None:
    payload = (
        {"service_account": fake_service_account_info, "location": "europe-west1"}
        if nested is True
        else {**fake_service_account_info, "location": "europe-west1"}
    )

    model = factory.build_model(_MODEL, json.dumps(payload))

    assert isinstance(model, pydantic_google.GoogleModel)
    assert model.system == "google-cloud"


def testBuildModel_whenGoogleVertexServiceAccountWithoutLocation_shouldRaise(
    fake_service_account_info: dict[str, str],
) -> None:
    with pytest.raises(errors.ModelConfigurationError, match="Missing 'location'"):
        factory.build_model(
            _MODEL, json.dumps({"service_account": fake_service_account_info})
        )


def testBuildModel_whenGoogleVertexServiceAccountWithoutProject_shouldRaise(
    fake_service_account_info: dict[str, str],
) -> None:
    service_account_info = dict(fake_service_account_info)
    del service_account_info["project_id"]

    with pytest.raises(errors.ModelConfigurationError, match="Missing 'project'"):
        factory.build_model(
            _MODEL,
            json.dumps(
                {"service_account": service_account_info, "location": "us-east1"}
            ),
        )


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ("{not-valid-json", "Invalid JSON"),
        (json.dumps({"location": "us-east1"}), "'service_account' or 'api_key'"),
        (
            json.dumps({"api_key": "k", "location": "us-east1"}),
            "'project' or 'location'",
        ),
        (json.dumps({"api_key": "k", "project": "p"}), "'project' or 'location'"),
        (json.dumps({"api_key": 42}), "must be a non-empty string"),
        (json.dumps({"api_key": "   "}), "must be a non-empty string"),
        ("[1]", "must be a JSON object"),
        (json.dumps({"api_key": "k", "service_account": {}}), "'service_account'"),
    ],
)
def testBuildModel_whenGoogleVertexCredentialInvalid_shouldRaise(
    payload: str, message: str
) -> None:
    with pytest.raises(errors.ModelConfigurationError, match=message):
        factory.build_model(_MODEL, payload)


def testBuildModel_whenGoogleVertexServiceAccountUnusable_shouldRaiseAtBuildTime() -> (
    None
):
    payload = {"type": "service_account", "project_id": "p", "location": "us-east1"}

    with pytest.raises(
        errors.ModelConfigurationError, match="service account credentials"
    ):
        factory.build_model(_MODEL, json.dumps(payload))


def testBuildModel_whenGeminiApiKey_shouldBuildGeminiApiModel() -> None:
    model = factory.build_model("gemini/gemini-3.7-flash", "g-key")

    assert isinstance(model, pydantic_google.GoogleModel)
    assert model.system == "google"
