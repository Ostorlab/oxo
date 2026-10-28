"""Tests for scan run asn command and the ASN asset message bus flow."""

from click import testing
from pytest_mock import plugin

from ostorlab.agent import agent
from ostorlab.agent import definitions as agent_definitions
from ostorlab.agent.message import message as agent_message
from ostorlab.cli import rootcli
from ostorlab.runtimes import definitions as runtime_definitions
from ostorlab.testing import agent as agent_testing


def testScanRunASN_whenNoOptionsProvided_showsUsageAndExitsWithError(
    mocker: plugin.MockerFixture,
) -> None:
    """Test oxo scan run asn command with no arguments.
    Should show usage and exit with exit_code = 2."""
    runner = testing.CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    result = runner.invoke(
        rootcli.rootcli,
        ["scan", "run", "--agent=agent1", "asn"],
    )

    assert result.exit_code == 2
    assert "Missing argument" in result.output or "Usage:" in result.output


def testScanRunASN_whenValidASNProvided_invokesRuntime(
    mocker: plugin.MockerFixture,
) -> None:
    """Test oxo scan run asn with a valid ASN triggers a scan."""
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    mock_scan = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )
    runner = testing.CliRunner()
    result = runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "--runtime=local",
            "run",
            "--agent=agent1",
            "asn",
            "15169",
        ],
    )

    assert mock_scan.called
    assert result.exit_code == 0


def testScanRunASN_whenMultipleASNsProvided_invokesRuntimeWithAllAssets(
    mocker: plugin.MockerFixture,
) -> None:
    """Test oxo scan run asn with multiple ASNs passes all assets to runtime."""
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    mock_scan = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )
    runner = testing.CliRunner()
    result = runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "--runtime=local",
            "run",
            "--agent=agent1",
            "asn",
            "15169",
            "13335",
        ],
    )

    assert mock_scan.called
    call_assets = mock_scan.call_args[1]["assets"]
    assert len(call_assets) == 2
    assert result.exit_code == 0


def testASNAgent_whenReceivesASNMessage_processesASN(
    agent_run_mock: agent_testing.AgentRunInstance,
) -> None:
    """A fake agent subscribed to v3.asset.asn receives the message and can
    read the asn field — no real MQ or Docker needed."""

    received: list[str] = []

    class FakeASNAgent(agent.Agent):
        def process(self, message: agent_message.Message) -> None:
            received.append(message.data["asn"])

    fake_agent = FakeASNAgent(
        agent_definitions.AgentDefinition(
            name="fake_asn_agent",
            in_selectors=["v3.asset.asn"],
            out_selectors=[],
        ),
        runtime_definitions.AgentSettings(
            key="agent/ostorlab/fake_asn_agent",
            bus_url="amqp://guest:guest@localhost:5672/",
            bus_exchange_topic="ostorlab_test",
            healthcheck_port=5399,
        ),
    )

    msg = agent_message.Message.from_data(
        "v3.asset.asn",
        {"asn": "15169"},
    )
    fake_agent.process(msg)

    assert received == ["15169"]


def testASNAgent_whenReceivesASNMessage_emitsVulnerability(
    agent_run_mock: agent_testing.AgentRunInstance,
) -> None:
    """Simulates a full agent cycle: receive ASN asset, emit a vulnerability.
    Uses agent_run_mock to intercept bus messages without a real MQ."""

    class FakeASNAgent(agent.Agent):
        def process(self, message: agent_message.Message) -> None:
            asn = message.data["asn"]
            self.emit(
                "v3.report.vulnerability",
                {
                    "title": "Test finding",
                    "technical_detail": f"Found issue on {asn}",
                    "risk_rating": "INFO",
                },
            )

    fake_agent = FakeASNAgent(
        agent_definitions.AgentDefinition(
            name="fake_asn_agent",
            in_selectors=["v3.asset.asn"],
            out_selectors=["v3.report.vulnerability"],
        ),
        runtime_definitions.AgentSettings(
            key="agent/ostorlab/fake_asn_agent",
            bus_url="amqp://guest:guest@localhost:5672/",
            bus_exchange_topic="ostorlab_test",
            healthcheck_port=5399,
        ),
    )

    msg = agent_message.Message.from_data(
        "v3.asset.asn",
        {"asn": "15169"},
    )
    fake_agent.process(msg)

    assert len(agent_run_mock.emitted_messages) == 1
    vuln = agent_run_mock.emitted_messages[0]
    assert vuln.selector == "v3.report.vulnerability"
    assert "15169" in vuln.data["technical_detail"]
