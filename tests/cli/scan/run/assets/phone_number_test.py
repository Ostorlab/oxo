"""Tests for scan run phone-number command and the phone number asset message bus flow."""

from click import testing

from ostorlab.agent import agent
from ostorlab.agent import definitions as agent_definitions
from ostorlab.agent.message import message as agent_message
from ostorlab.cli import rootcli
from ostorlab.runtimes import definitions as runtime_definitions
from ostorlab.testing import agent as agent_testing


def testScanRunPhoneNumber_whenNoOptionsProvided_showsUsageAndExitsWithError(mocker):
    """Test oxo scan run phone-number command with no arguments.
    Should show usage and exit with exit_code = 2."""
    runner = testing.CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    result = runner.invoke(
        rootcli.rootcli,
        ["scan", "run", "--agent=agent1", "phone-number"],
    )

    assert result.exit_code == 2
    assert "Missing argument" in result.output or "Usage:" in result.output


def testScanRunPhoneNumber_whenValidNumberProvided_invokesRuntime(mocker):
    """Test oxo scan run phone-number with a valid number triggers a scan."""
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
            "phone-number",
            "+12125551234",
        ],
    )

    assert mock_scan.called
    assert result.exit_code == 0


def testScanRunPhoneNumber_whenMultipleNumbersProvided_invokesRuntimeWithAllAssets(
    mocker,
):
    """Test oxo scan run phone-number with multiple numbers passes all assets to runtime."""
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
            "phone-number",
            "+12125551234",
            "+33612345678",
        ],
    )

    assert mock_scan.called
    call_assets = mock_scan.call_args[1]["assets"]
    assert len(call_assets) == 2
    assert result.exit_code == 0


def testPhoneNumberAgent_whenReceivesPhoneNumberMessage_processesNumber(
    agent_run_mock: agent_testing.AgentRunInstance,
):
    """A fake agent subscribed to v3.asset.phone_number receives the message and can
    read the number field — no real MQ or Docker needed."""

    received: list = []

    class FakePhoneNumberAgent(agent.Agent):
        def process(self, message: agent_message.Message) -> None:
            received.append(message.data["number"])

    fake_agent = FakePhoneNumberAgent(
        agent_definitions.AgentDefinition(
            name="fake_phone_number_agent",
            in_selectors=["v3.asset.phone_number"],
            out_selectors=[],
        ),
        runtime_definitions.AgentSettings(
            key="agent/ostorlab/fake_phone_number_agent",
            bus_url="amqp://guest:guest@localhost:5672/",
            bus_exchange_topic="ostorlab_test",
            healthcheck_port=5399,
        ),
    )

    msg = agent_message.Message.from_data(
        "v3.asset.phone_number",
        {"number": "+12125551234"},
    )
    fake_agent.process(msg)

    assert received == ["+12125551234"]


def testPhoneNumberAgent_whenReceivesPhoneNumberMessage_emitsVulnerability(
    agent_run_mock: agent_testing.AgentRunInstance,
):
    """Simulates a full agent cycle: receive phone number asset, emit a vulnerability.
    Uses agent_run_mock to intercept bus messages without a real MQ."""

    class FakePhoneNumberAgent(agent.Agent):
        def process(self, message: agent_message.Message) -> None:
            number = message.data["number"]
            self.emit(
                "v3.report.vulnerability",
                {
                    "title": "Test finding",
                    "technical_detail": f"Found issue on {number}",
                    "risk_rating": "INFO",
                },
            )

    fake_agent = FakePhoneNumberAgent(
        agent_definitions.AgentDefinition(
            name="fake_phone_number_agent",
            in_selectors=["v3.asset.phone_number"],
            out_selectors=["v3.report.vulnerability"],
        ),
        runtime_definitions.AgentSettings(
            key="agent/ostorlab/fake_phone_number_agent",
            bus_url="amqp://guest:guest@localhost:5672/",
            bus_exchange_topic="ostorlab_test",
            healthcheck_port=5399,
        ),
    )

    msg = agent_message.Message.from_data(
        "v3.asset.phone_number",
        {"number": "+12125551234"},
    )
    fake_agent.process(msg)

    assert len(agent_run_mock.emitted_messages) == 1
    vuln = agent_run_mock.emitted_messages[0]
    assert vuln.selector == "v3.report.vulnerability"
    assert "+12125551234" in vuln.data["technical_detail"]
