"""Tests for scan run ticket command."""

from click.testing import CliRunner
from pytest_mock import plugin

from ostorlab.cli import rootcli
from ostorlab.agent import definitions as agent_definitions
from ostorlab.assets import ticket


def testScanRunTicket_whenValidArgumentsAreProvided_callScanWithValidSettings(
    mocker: plugin.MockerFixture,
    nmap_agent_definition: agent_definitions.AgentDefinition,
) -> None:
    """Test oxo scan run ticket command with valid arguments."""
    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    mocker.patch(
        "ostorlab.cli.agent_fetcher.get_definition",
        return_value=nmap_agent_definition,
    )
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=True
    )

    runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "ticket",
            "--title=Sample Ticket",
            "--ticket-id=TCK-123",
            "--description=A sample ticket description",
            "--comment=alice:high priority",
            "--comment=bob:bug confirmed",
        ],
    )

    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    asset = assets[0]
    assert isinstance(asset, ticket.Ticket)
    assert asset.title == "Sample Ticket"
    assert asset.ticket_id == "TCK-123"
    assert asset.description == "A sample ticket description"
    assert len(asset.comments) == 2
    assert asset.comments[0].author == "alice"
    assert asset.comments[0].message == "high priority"
    assert asset.comments[1].author == "bob"
    assert asset.comments[1].message == "bug confirmed"
