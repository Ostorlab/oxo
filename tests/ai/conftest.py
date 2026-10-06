"""Shared fixtures for ostorlab.ai tests."""

from __future__ import annotations

import datetime
from collections.abc import Callable
from collections.abc import Iterator
from typing import Any

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from google.oauth2 import service_account

from ostorlab.ai.providers import vertex_endpoint

VERTEX_ENDPOINT_URL = (
    "https://123.us-east1-456.prediction.vertexai.goog"
    "/v1beta1/projects/456/locations/us-east1/endpoints/123"
)


@pytest.fixture(autouse=True)
def stub_credentials_refresh(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub the OAuth token exchange so no test reaches Google."""

    def _fake_refresh(self: service_account.Credentials, request: object) -> None:
        self.token = "fake-access-token"
        # google.auth compares expiry against a naive UTC datetime.
        self.expiry = datetime.datetime.now(datetime.timezone.utc).replace(
            tzinfo=None
        ) + datetime.timedelta(hours=1)

    monkeypatch.setattr(service_account.Credentials, "refresh", _fake_refresh)


@pytest.fixture(autouse=True)
def clear_token_provider_cache() -> Iterator[None]:
    vertex_endpoint.get_token_provider.cache_clear()
    yield
    vertex_endpoint.get_token_provider.cache_clear()


@pytest.fixture
def fake_service_account_info() -> dict[str, str]:
    """A minimal but valid service account info dict backed by a real RSA key."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    return {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test-key-id",
        "private_key": private_key_pem,
        "client_email": "svc@test-project.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token",
    }


class StubVertexCredentials:
    """A stand-in for service account credentials that records refresh calls."""

    def __init__(self, valid: bool) -> None:
        self.valid = valid
        self.token: str | None = "initial-token" if valid is True else None
        self.refresh_count = 0

    def refresh(self, request: Any) -> None:
        """Mint a new token, mirroring what a real refresh leaves behind."""
        self.refresh_count += 1
        self.token = f"refreshed-token-{self.refresh_count}"
        self.valid = True


@pytest.fixture
def stub_vertex_credentials() -> Callable[[bool], StubVertexCredentials]:
    """Build stub Vertex credentials in either the valid or the not-yet-valid state."""

    def _build(valid: bool) -> StubVertexCredentials:
        return StubVertexCredentials(valid=valid)

    return _build
