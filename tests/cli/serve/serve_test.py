"""Unit tests for the serve command."""

from click.testing import CliRunner
from pytest_mock import plugin

from ostorlab.cli import rootcli
from ostorlab.runtimes.local.models import models


def testOstorlabServe_whenRefreshApiKeyFlagIsProvided_refreshApiKey(
    mocker: plugin.MockerFixture,
) -> None:
    """Test the serve command with the refresh-api-key flag. Should refresh the API key."""
    mocked_refresh_api_key = mocker.patch(
        "ostorlab.runtimes.local.models.models.APIKey.refresh"
    )
    mocker.patch("ostorlab.serve_app.app.create_app")
    runner = CliRunner()

    result = runner.invoke(rootcli.rootcli, ["serve", "--refresh-api-key"])

    assert mocked_refresh_api_key.called is True
    assert "API key refreshed" in result.output


def testOstorlabServe_whenRefreshApiKeyFlagIsNotProvided_getOrCreateApiKey(
    mocker: plugin.MockerFixture,
) -> None:
    """Test the serve command without the refresh-api-key flag. Should get or create the API key."""
    mocked_refresh_api_key = mocker.patch(
        "ostorlab.runtimes.local.models.models.APIKey.refresh"
    )
    mocker.patch("ostorlab.serve_app.app.create_app")
    runner = CliRunner()

    result = runner.invoke(rootcli.rootcli, ["serve"])

    assert mocked_refresh_api_key.called is False
    assert "API key refreshed" not in result.output


def testOstorlabServe_whenStarting_shouldPersistPredifinedAgentGroups(
    mocker: plugin.MockerFixture, db_engine_path: str
) -> None:
    """Test the serve command, when starting server, should persist the predefined agent groups."""

    mocker.patch.object(models, "ENGINE_URL", db_engine_path)
    serve_run_mock = mocker.patch("flask.app.Flask.run")
    runner = CliRunner()

    runner.invoke(rootcli.rootcli, ["serve"])

    assert serve_run_mock.call_count == 1
    with models.Database() as session:
        agent_groups = (
            session.query(models.AgentGroup).order_by(models.AgentGroup.name).all()
        )

        web_autodiscovery_network_asset_types = [
            models.AssetTypeEnum.LINK,
            models.AssetTypeEnum.IP,
            models.AssetTypeEnum.DOMAIN,
        ]
        # autodiscovery
        assert agent_groups[0].name == "predefined_oxo_autodiscovery"
        assert agent_groups[0].description == "Enumerate domain scan"
        assert len(agent_groups[0].asset_types) == 3
        assert (
            agent_groups[0].asset_types[0].type in web_autodiscovery_network_asset_types
        )
        assert (
            agent_groups[0].asset_types[1].type in web_autodiscovery_network_asset_types
        )
        assert (
            agent_groups[0].asset_types[2].type in web_autodiscovery_network_asset_types
        )
        assert len(agent_groups[0].agents) == 7
        assert agent_groups[0].agents[0].key == "agent/ostorlab/subfinder"
        assert agent_groups[0].agents[1].key == "agent/ostorlab/dnsx"
        assert agent_groups[0].agents[2].key == "agent/ostorlab/all_tlds"
        assert agent_groups[0].agents[3].key == "agent/ostorlab/amass"
        assert agent_groups[0].agents[4].key == "agent/ostorlab/whois_domain"
        assert agent_groups[0].agents[5].key == "agent/ostorlab/whatweb"
        assert agent_groups[0].agents[6].key == "agent/ostorlab/nmap"
        assert (
            session.query(models.AgentArgument)
            .filter_by(agent_id=agent_groups[0].agents[0].id)
            .count()
            == 0
        )
        assert (
            session.query(models.AgentArgument)
            .filter_by(agent_id=agent_groups[0].agents[1].id)
            .count()
            == 0
        )
        assert (
            session.query(models.AgentArgument)
            .filter_by(agent_id=agent_groups[0].agents[2].id)
            .count()
            == 0
        )
        assert (
            session.query(models.AgentArgument)
            .filter_by(agent_id=agent_groups[0].agents[3].id)
            .count()
            == 0
        )
        assert (
            session.query(models.AgentArgument)
            .filter_by(agent_id=agent_groups[0].agents[4].id)
            .count()
            == 0
        )
        assert (
            session.query(models.AgentArgument)
            .filter_by(agent_id=agent_groups[0].agents[5].id)
            .count()
            == 0
        )
        assert (
            session.query(models.AgentArgument)
            .filter_by(agent_id=agent_groups[0].agents[6].id)
            .count()
            == 0
        )

        # network
        assert agent_groups[1].name == "predefined_oxo_network"
        assert (
            agent_groups[1].description == "Agent Group for Extensive network scanning."
        )
        assert len(agent_groups[1].asset_types) == 3
        assert (
            agent_groups[1].asset_types[0].type in web_autodiscovery_network_asset_types
        )
        assert (
            agent_groups[1].asset_types[1].type in web_autodiscovery_network_asset_types
        )
        assert (
            agent_groups[1].asset_types[2].type in web_autodiscovery_network_asset_types
        )
        assert len(agent_groups[1].agents) == 6
        assert agent_groups[1].agents[0].key == "agent/ostorlab/nmap"
        assert agent_groups[1].agents[1].key == "agent/ostorlab/asteroid"
        assert agent_groups[1].agents[2].key == "agent/ostorlab/metasploit"
        assert agent_groups[1].agents[3].key == "agent/ostorlab/openvas"
        assert agent_groups[1].agents[4].key == "agent/ostorlab/nuclei"
        assert agent_groups[1].agents[5].key == "agent/ostorlab/tsunami"
        args = (
            session.query(models.AgentArgument)
            .filter_by(agent_id=agent_groups[1].agents[0].id)
            .all()
        )
        assert len(args) == 4
        assert args[0].name == "fast_mode"
        assert args[0].type == "boolean"
        assert (
            models.AgentArgument.from_bytes(type=args[0].type, value=args[0].value)
            is True
        )
        assert args[1].name == "ports"
        assert args[1].type == "string"
        assert (
            models.AgentArgument.from_bytes(type=args[1].type, value=args[1].value)
            == "0-65535"
        )
        assert args[2].name == "timing_template"
        assert args[2].type == "string"
        assert (
            models.AgentArgument.from_bytes(type=args[2].type, value=args[2].value)
            == "T3"
        )
        assert args[3].name == "scripts"
        assert args[3].type == "array"
        assert models.AgentArgument.from_bytes(
            type=args[3].type, value=args[3].value
        ) == ["banner"]
        assert (
            session.query(models.AgentArgument)
            .filter_by(agent_id=agent_groups[1].agents[1].id)
            .count()
            == 0
        )
        assert (
            session.query(models.AgentArgument)
            .filter_by(agent_id=agent_groups[1].agents[2].id)
            .count()
            == 0
        )
        assert (
            session.query(models.AgentArgument)
            .filter_by(agent_id=agent_groups[1].agents[3].id)
            .count()
            == 0
        )
        assert (
            session.query(models.AgentArgument)
            .filter_by(agent_id=agent_groups[1].agents[4].id)
            .count()
            == 0
        )
        assert (
            session.query(models.AgentArgument)
            .filter_by(agent_id=agent_groups[1].agents[5].id)
            .count()
            == 0
        )

        # sbom
        assert len(agent_groups) == 4
        assert agent_groups[2].name == "predefined_oxo_sbom"
        assert agent_groups[2].description == "SBOM scan"
        assert len(agent_groups[2].asset_types) == 1
        assert agent_groups[2].asset_types[0].type == models.AssetTypeEnum.FILE
        assert len(agent_groups[2].agents) == 1
        assert agent_groups[2].agents[0].key == "agent/ostorlab/osv"
        args = (
            session.query(models.AgentArgument)
            .filter_by(agent_id=agent_groups[2].agents[0].id)
            .all()
        )
        assert len(args) == 1
        assert args[0].name == "nvd_api_key"
        assert args[0].type == "string"

        # web
        assert agent_groups[3].name == "predefined_oxo_web"
        assert (
            agent_groups[3].description
            == "Agent Group for extensive Web Testing with crawling, fuzzing and known vulnerability discovery."
        )
        assert len(agent_groups[3].asset_types) == 3
        assert (
            agent_groups[3].asset_types[0].type in web_autodiscovery_network_asset_types
        )
        assert (
            agent_groups[3].asset_types[1].type in web_autodiscovery_network_asset_types
        )
        assert (
            agent_groups[3].asset_types[2].type in web_autodiscovery_network_asset_types
        )
        assert len(agent_groups[3].agents) == 7
        assert agent_groups[3].agents[0].key == "agent/ostorlab/zap"
        assert agent_groups[3].agents[1].key == "agent/ostorlab/nuclei"
        assert agent_groups[3].agents[2].key == "agent/ostorlab/asteroid"
        assert agent_groups[3].agents[3].key == "agent/ostorlab/metasploit"
        assert agent_groups[3].agents[4].key == "agent/ostorlab/tsunami"
        assert agent_groups[3].agents[5].key == "agent/ostorlab/semgrep"
        assert agent_groups[3].agents[6].key == "agent/ostorlab/trufflehog"
        args = (
            session.query(models.AgentArgument)
            .filter_by(agent_id=agent_groups[3].agents[0].id)
            .all()
        )
        assert len(args) == 1
        assert args[0].name == "scan_profile"
        assert args[0].type == "string"
        assert (
            models.AgentArgument.from_bytes(type=args[0].type, value=args[0].value)
            == "full"
        )
        assert (
            session.query(models.AgentArgument)
            .filter_by(agent_id=agent_groups[3].agents[1].id)
            .count()
            == 0
        )
        assert (
            session.query(models.AgentArgument)
            .filter_by(agent_id=agent_groups[3].agents[2].id)
            .count()
            == 0
        )
        assert (
            session.query(models.AgentArgument)
            .filter_by(agent_id=agent_groups[3].agents[3].id)
            .count()
            == 0
        )
        assert (
            session.query(models.AgentArgument)
            .filter_by(agent_id=agent_groups[3].agents[4].id)
            .count()
            == 0
        )
        assert (
            session.query(models.AgentArgument)
            .filter_by(agent_id=agent_groups[3].agents[5].id)
            .count()
            == 0
        )
        assert (
            session.query(models.AgentArgument)
            .filter_by(agent_id=agent_groups[3].agents[6].id)
            .count()
            == 0
        )

        count_agent_groups_before = len(agent_groups)

        runner.invoke(rootcli.rootcli, ["serve"])

        assert serve_run_mock.call_count == 2
        assert session.query(models.AgentGroup).count() == count_agent_groups_before
