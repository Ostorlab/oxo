"""Tests for scan run api-schema command."""

from click import testing as click_testing
from pytest_mock import plugin

from ostorlab.cli import rootcli
from ostorlab.assets import api_schema


def testScanRunApiSchema_whenSchemaFileIsProvided_callScanWithValidAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Test oxo scan run api-schema command with --schema-file option. Should call scan with valid asset."""

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
                "--schema-file",
                "schema.graphql",
                "--url",
                "https://rickandmortyapi.com/graphql",
            ],
        )

        schema = api_schema.ApiSchema(
            content=b"query {}", endpoint_url="https://rickandmortyapi.com/graphql"
        )

        assert scan_mocked.call_count == 1
        assert scan_mocked.call_args_list is not None
        assert len(scan_mocked.call_args_list) == 1
        assert len(scan_mocked.call_args_list[0].kwargs.get("assets", [])) == 1
        assert schema.selector == "v3.asset.file.api_schema"
        assert schema.proto_field == "api_schema"
        assert schema.schema_type is None
        assert (
            scan_mocked.call_args_list[0].kwargs.get("assets")[0].content
            == schema.content
        )
        assert (
            scan_mocked.call_args_list[0].kwargs.get("assets")[0].endpoint_url
            == schema.endpoint_url
        )
        assert scan_mocked.call_args_list[0].kwargs.get("assets")[0].content_url is None


def testScanRunApiSchema_whenSchemaUrlIsProvided_callScanWithValidAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Test oxo scan run api-schema command with --schema-url option. Should call scan with valid asset."""

    runner = click_testing.CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=True
    )

    runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent/ostorlab/api_autodiscovery",
            "api-schema",
            "--schema-url",
            "https://cloud.google.com/storage/uploads/scheam.graphql",
            "--url",
            "https://rickandmortyapi.com/graphql",
        ],
    )

    schema = api_schema.ApiSchema(
        content_url="https://cloud.google.com/storage/uploads/scheam.graphql",
        endpoint_url="https://rickandmortyapi.com/graphql",
    )

    assert scan_mocked.call_count == 1
    assert scan_mocked.call_args_list is not None
    assert len(scan_mocked.call_args_list) == 1
    assert len(scan_mocked.call_args_list[0].kwargs.get("assets", [])) == 1
    assert schema.selector == "v3.asset.file.api_schema"
    assert schema.proto_field == "api_schema"
    assert schema.schema_type is None
    assert (
        scan_mocked.call_args_list[0].kwargs.get("assets")[0].content_url
        == schema.content_url
    )
    assert (
        scan_mocked.call_args_list[0].kwargs.get("assets")[0].endpoint_url
        == schema.endpoint_url
    )
    assert scan_mocked.call_args_list[0].kwargs.get("assets")[0].content is None


def testScanRunApiSchema_whenBothSchemaUrlAndSchemaFileAreProvided_callScanWithValidAsset(
    mocker: plugin.MockerFixture,
) -> None:
    """Test oxo scan run api-schema command when both --schema-url and --schema-file options are provided. Should call
    scan with valid asset.
    """

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
                "--schema-url",
                "https://cloud.google.com/storage/uploads/scheam.graphql",
                "--schema-file",
                "schema.graphql",
                "--url",
                "https://rickandmortyapi.com/graphql",
            ],
        )

        schema = api_schema.ApiSchema(
            content=b"query {}",
            content_url="https://cloud.google.com/storage/uploads/scheam.graphql",
            endpoint_url="https://rickandmortyapi.com/graphql",
        )

        assert scan_mocked.call_count == 1
        assert scan_mocked.call_args_list is not None
        assert len(scan_mocked.call_args_list) == 1
        assert len(scan_mocked.call_args_list[0].kwargs.get("assets", [])) == 1
        assert schema.selector == "v3.asset.file.api_schema"
        assert schema.proto_field == "api_schema"
        assert schema.schema_type is None
        assert (
            scan_mocked.call_args_list[0].kwargs.get("assets")[0].content_url
            == schema.content_url
        )
        assert (
            scan_mocked.call_args_list[0].kwargs.get("assets")[0].content
            == schema.content
        )
        assert (
            scan_mocked.call_args_list[0].kwargs.get("assets")[0].endpoint_url
            == schema.endpoint_url
        )


def testScanRunApiSchema_whenSchemaUrlAndSchemaFileAreMissing_raisesClickException(
    mocker: plugin.MockerFixture,
) -> None:
    """Test oxo scan run api-schema command without --schema-url and --schema-file option. Should log error and not
    create scan.
    """

    runner = click_testing.CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=True
    )

    result = runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent/ostorlab/api_autodiscovery",
            "api-schema",
            "--url",
            "https://rickandmortyapi.com/graphql",
        ],
    )

    assert scan_mocked.call_count == 0
    assert result.exit_code == 2
    assert "You must provide either --schema-file or --schema-url." in result.output
