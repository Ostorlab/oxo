"""Tests for scan run api-schema command."""

from click import testing as click_testing
from pytest_mock import plugin

from ostorlab.cli import rootcli


def testScanRunApiSchema_whenApiSchemaFileAndUrlAreProvided_callScanWithValidAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Test oxo scan run api-schema command with --file and --url option. Should call scan with valid asset."""

    runner = click_testing.CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=True
    )

    with runner.isolated_filesystem():
        with open("schema.graphql", "w", encoding="utf-8") as f:
            f.write("query {}")
            f.seek(0)

        runner.invoke(
            rootcli.rootcli,
            [
                "scan",
                "run",
                "--agent=agent/ostorlab/api_autodiscovery",
                "api-schema",
                "--file",
                "schema.graphql",
                "--url",
                "https://rickandmortyapi.com/graphql",
            ],
        )

        assert scan_mocked.call_count == 1
        assert scan_mocked.call_args_list is not None
        assert len(scan_mocked.call_args_list) == 1
        assert len(scan_mocked.call_args_list[0].kwargs.get("assets", [])) == 1
        assert (
            scan_mocked.call_args_list[0].kwargs.get("assets")[0].content == b"query {}"
        )
        assert (
            scan_mocked.call_args_list[0].kwargs.get("assets")[0].endpoint_url
            == "https://rickandmortyapi.com/graphql"
        )
