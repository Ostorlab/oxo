"""Tests for real application startup in an isolated database."""

from ostorlab.runtimes.local.models import models
from ostorlab.serve_app import app


def testCreateApp_whenDatabaseEmpty_createsDefaultAgentGroups() -> None:
    """Production startup seeds agent groups without the API fixtures' patch."""
    flask_app = app.create_app()

    assert flask_app.test_client().get("/graphql").status_code == 401
    with models.Database() as session:
        assert session.query(models.AgentGroup).count() > 0
        assert session.query(models.AgentGroupAssetType).count() > 0
