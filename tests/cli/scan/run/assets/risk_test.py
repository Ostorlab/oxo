"""Tests for scan run risk command."""

import pathlib

from click import testing
from pytest_mock import MockerFixture

from ostorlab.cli import rootcli
from ostorlab.assets import risk as risk_asset


def testScanRunRisk_whenNoOptionsProvided_shouldShowUsageError(
    scan_run_cli_runner: testing.CliRunner,
) -> None:
    """Test oxo scan run risk command with no options.
    Should show error for missing required options."""
    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        ["scan", "run", "--agent=agent1", "risk"],
    )

    assert result.exit_code == 2
    assert "Missing option" in result.output


def testScanRunRisk_whenValidSeverityAndDescription_shouldCallScanWithRiskAsset(
    scan_run_cli_runner: testing.CliRunner,
    mocker: MockerFixture,
) -> None:
    """Test oxo scan run risk command with severity and description."""
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=HIGH",
            "--description=Server exposed to internet",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    assert isinstance(assets[0], risk_asset.Risk)
    assert assets[0].rating == "HIGH"
    assert assets[0].description == "Server exposed to internet"


def testScanRunRisk_whenIpProvided_shouldCallScanWithRiskAssetContainingIp(
    scan_run_cli_runner: testing.CliRunner,
    mocker: MockerFixture,
) -> None:
    """Test oxo scan run risk command with --ip flag populates ipv4 field."""
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=CRITICAL",
            "--description=Test risk",
            "--ip=8.8.8.8",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    assert isinstance(assets[0], risk_asset.Risk)
    assert assets[0].ipv4 == {"host": "8.8.8.8", "mask": "32", "version": 4}


def testScanRunRisk_whenDomainProvided_shouldCallScanWithRiskAssetContainingDomain(
    scan_run_cli_runner: testing.CliRunner,
    mocker: MockerFixture,
) -> None:
    """Test oxo scan run risk command with --domain flag populates domain_name field."""
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=MEDIUM",
            "--description=Weak TLS",
            "--domain=example.com",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    assert isinstance(assets[0], risk_asset.Risk)
    assert assets[0].domain_name == {"name": "example.com"}


def testScanRunRisk_whenLinkProvided_shouldCallScanWithRiskAssetContainingLink(
    scan_run_cli_runner: testing.CliRunner,
    mocker: MockerFixture,
) -> None:
    """Test oxo scan run risk command with --link flag populates link field."""
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=LOW",
            "--description=Test link risk",
            "--link=https://example.com",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    assert isinstance(assets[0], risk_asset.Risk)
    assert assets[0].link == {"url": "https://example.com", "method": "GET"}


def testScanRunRisk_whenRuntimeCannotRun_shouldExitWithError(
    mocker: MockerFixture,
) -> None:
    """Test oxo scan run risk when runtime cannot run the agents."""
    runner = testing.CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch(
        "ostorlab.runtimes.local.runtime.LocalRuntime.can_run", return_value=False
    )

    result = runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "--runtime=local",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=HIGH",
            "--description=Test",
        ],
    )

    assert result.exit_code == 1


def testScanRunRisk_whenDescriptionFileProvided_shouldReadFromFile(
    scan_run_cli_runner: testing.CliRunner,
    mocker: MockerFixture,
    tmp_path: pathlib.Path,
) -> None:
    """Test oxo scan run risk command with --description-file reads description from file."""
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )
    desc_file = tmp_path / "description.txt"
    desc_file.write_text("Detailed risk description from file")

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=HIGH",
            f"--description-file={desc_file}",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    assert assets[0].description == "Detailed risk description from file"


def testScanRunRisk_whenBothDescriptionAndFile_shouldShowError(
    scan_run_cli_runner: testing.CliRunner,
    tmp_path: pathlib.Path,
) -> None:
    """Test oxo scan run risk with both --description and --description-file shows error."""
    desc_file = tmp_path / "description.txt"
    desc_file.write_text("File content")

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=HIGH",
            "--description=Inline",
            f"--description-file={desc_file}",
        ],
    )

    assert result.exit_code == 2


def testScanRunRisk_whenNeitherDescriptionNorFile_shouldShowError(
    scan_run_cli_runner: testing.CliRunner,
) -> None:
    """Test oxo scan run risk with neither --description nor --description-file shows error."""
    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=HIGH",
        ],
    )

    assert result.exit_code == 2


def testScanRunRisk_whenInvalidSeverityProvided_shouldShowError(
    scan_run_cli_runner: testing.CliRunner,
) -> None:
    """Test oxo scan run risk with an invalid --severity value is rejected by click.Choice."""
    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=INVALID",
            "--description=Test",
        ],
    )

    assert result.exit_code == 2


def testScanRunRisk_whenAndroidApkProvided_shouldCallScanWithRiskAssetContainingAndroidApk(
    scan_run_cli_runner: testing.CliRunner,
    mocker: MockerFixture,
    tmp_path: pathlib.Path,
) -> None:
    """Test oxo scan run risk command with --android-apk populates android_apk field."""
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )
    apk_file = tmp_path / "app.apk"
    apk_file.write_bytes(b"apk content")

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=HIGH",
            "--description=Vulnerable APK",
            f"--android-apk={apk_file}",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    assert isinstance(assets[0], risk_asset.Risk)
    assert assets[0].android_apk["content"] == b"apk content"
    assert assets[0].android_apk["path"] == str(apk_file)


def testScanRunRisk_whenIpv6Provided_shouldCallScanWithRiskAssetContainingIpv6(
    scan_run_cli_runner: testing.CliRunner,
    mocker: MockerFixture,
) -> None:
    """Test oxo scan run risk command with --ip IPv6 address populates ipv6 field."""
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=HIGH",
            "--description=IPv6 exposure",
            "--ip=2001:db8::1",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    assert isinstance(assets[0], risk_asset.Risk)
    assert assets[0].ipv6 == {
        "host": "2001:0db8:0000:0000:0000:0000:0000:0001",
        "mask": "128",
        "version": 6,
    }


def testRiskAsset_protoField_shouldBeRisk() -> None:
    """Test that Risk asset proto_field returns 'risk' for use in vulnerability location."""
    r = risk_asset.Risk(description="test", rating="HIGH")

    assert r.proto_field == "risk"


def testRiskAsset_serialization_shouldProduceValidProtobuf() -> None:
    """Test that Risk asset serializes to valid protobuf bytes."""
    r = risk_asset.Risk(description="test risk", rating="HIGH")
    proto_bytes = r.to_proto()

    assert isinstance(proto_bytes, bytes)
    assert len(proto_bytes) > 0


def testRiskAsset_serializationWithIp_shouldProduceValidProtobuf() -> None:
    """Test that Risk asset with embedded IP serializes correctly."""
    r = risk_asset.Risk(
        description="server exposed",
        rating="CRITICAL",
        ipv4={"host": "8.8.8.8", "mask": "32", "version": 4},
    )
    proto_bytes = r.to_proto()

    assert isinstance(proto_bytes, bytes)
    assert len(proto_bytes) > 0


def testRiskAsset_selector_shouldBeCorrect() -> None:
    """Test that Risk asset has the correct selector."""
    r = risk_asset.Risk(description="test", rating="HIGH")
    assert r.selector == "v3.report.risk"


def testScanRunRisk_whenAndroidApkUrlProvided_shouldCallScanWithRiskAssetContainingContentUrl(
    scan_run_cli_runner: testing.CliRunner,
    mocker: MockerFixture,
) -> None:
    """Test oxo scan run risk command with --android-apk-url populates android_apk content_url field."""
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=HIGH",
            "--description=Vulnerable APK",
            "--android-apk-url=https://example.com/app.apk",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert len(assets) == 1
    assert isinstance(assets[0], risk_asset.Risk)
    assert assets[0].android_apk == {"content_url": "https://example.com/app.apk"}


def testScanRunRisk_whenAndroidApkFileAndUrlBothProvided_shouldShowError(
    scan_run_cli_runner: testing.CliRunner,
    tmp_path: pathlib.Path,
) -> None:
    """Test oxo scan run risk with both --android-apk and --android-apk-url shows error."""
    apk_file = tmp_path / "app.apk"
    apk_file.write_bytes(b"apk content")

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=HIGH",
            "--description=Test",
            f"--android-apk={apk_file}",
            "--android-apk-url=https://example.com/app.apk",
        ],
    )

    assert result.exit_code == 2


def testScanRunRisk_whenAndroidAabUrlProvided_shouldCallScanWithRiskAssetContainingContentUrl(
    scan_run_cli_runner: testing.CliRunner,
    mocker: MockerFixture,
) -> None:
    """Test oxo scan run risk command with --android-aab-url populates android_aab content_url field."""
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=HIGH",
            "--description=Vulnerable AAB",
            "--android-aab-url=https://example.com/app.aab",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert isinstance(assets[0], risk_asset.Risk)
    assert assets[0].android_aab == {"content_url": "https://example.com/app.aab"}


def testScanRunRisk_whenIosIpaUrlProvided_shouldCallScanWithRiskAssetContainingContentUrl(
    scan_run_cli_runner: testing.CliRunner,
    mocker: MockerFixture,
) -> None:
    """Test oxo scan run risk command with --ios-ipa-url populates ios_ipa content_url field."""
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=HIGH",
            "--description=Vulnerable IPA",
            "--ios-ipa-url=https://example.com/app.ipa",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert isinstance(assets[0], risk_asset.Risk)
    assert assets[0].ios_ipa == {"content_url": "https://example.com/app.ipa"}


def testScanRunRisk_whenFileUrlProvided_shouldCallScanWithRiskAssetContainingContentUrl(
    scan_run_cli_runner: testing.CliRunner,
    mocker: MockerFixture,
) -> None:
    """Test oxo scan run risk command with --file-url populates file content_url field."""
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=HIGH",
            "--description=Vulnerable file",
            "--file-url=https://example.com/binary",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert isinstance(assets[0], risk_asset.Risk)
    assert assets[0].file == {"content_url": "https://example.com/binary"}


def testScanRunRisk_whenLinkMethodProvided_shouldCallScanWithCorrectMethod(
    scan_run_cli_runner: testing.CliRunner,
    mocker: MockerFixture,
) -> None:
    """Test oxo scan run risk command with --link-method overrides default GET."""
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=HIGH",
            "--description=Test link risk",
            "--link=https://example.com/api",
            "--link-method=POST",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert isinstance(assets[0], risk_asset.Risk)
    assert assets[0].link == {"url": "https://example.com/api", "method": "POST"}


def testScanRunRisk_whenLinkHeadersProvided_shouldCallScanWithHeaders(
    scan_run_cli_runner: testing.CliRunner,
    mocker: MockerFixture,
) -> None:
    """Test oxo scan run risk command with --link-header populates extra_headers field."""
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=HIGH",
            "--description=Test link with headers",
            "--link=https://example.com/api",
            "--link-header=X-Api-Key: secret",
            "--link-header=Accept: application/json",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert isinstance(assets[0], risk_asset.Risk)
    assert assets[0].link["extra_headers"] == [
        {"name": "X-Api-Key", "value": "secret"},
        {"name": "Accept", "value": "application/json"},
    ]


def testScanRunRisk_whenInvalidLinkHeaderFormat_shouldShowError(
    scan_run_cli_runner: testing.CliRunner,
) -> None:
    """Test oxo scan run risk with a malformed --link-header shows error."""
    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=HIGH",
            "--description=Test",
            "--link=https://example.com",
            "--link-header=BadHeader",
        ],
    )

    assert result.exit_code == 2


def testScanRunRisk_whenApiSchemaFileProvided_shouldCallScanWithContentAndPath(
    scan_run_cli_runner: testing.CliRunner,
    mocker: MockerFixture,
    tmp_path: pathlib.Path,
) -> None:
    """Test oxo scan run risk command with --api-schema-file populates content and path."""
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )
    schema_file = tmp_path / "openapi.yaml"
    schema_file.write_bytes(b"openapi: 3.0.0")

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=HIGH",
            "--description=API exposure",
            f"--api-schema-file={schema_file}",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert isinstance(assets[0], risk_asset.Risk)
    assert assets[0].api_schema["content"] == b"openapi: 3.0.0"
    assert assets[0].api_schema["path"] == str(schema_file)


def testScanRunRisk_whenApiSchemaUrlProvided_shouldCallScanWithContentUrl(
    scan_run_cli_runner: testing.CliRunner,
    mocker: MockerFixture,
) -> None:
    """Test oxo scan run risk command with --api-schema-url populates content_url field."""
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=HIGH",
            "--description=API exposure",
            "--api-schema-url=https://example.com/openapi.yaml",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert isinstance(assets[0], risk_asset.Risk)
    assert assets[0].api_schema == {"content_url": "https://example.com/openapi.yaml"}


def testScanRunRisk_whenApiSchemaEndpointAndTypeProvided_shouldCallScanWithFields(
    scan_run_cli_runner: testing.CliRunner,
    mocker: MockerFixture,
) -> None:
    """Test oxo scan run risk command with --api-schema-endpoint and --api-schema-type."""
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=HIGH",
            "--description=API exposure",
            "--api-schema-endpoint=https://api.example.com",
            "--api-schema-type=openapi",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert isinstance(assets[0], risk_asset.Risk)
    assert assets[0].api_schema["endpoint_url"] == "https://api.example.com"
    assert assets[0].api_schema["schema_type"] == "openapi"


def testScanRunRisk_whenApiSchemaHeadersProvided_shouldCallScanWithExtraHeaders(
    scan_run_cli_runner: testing.CliRunner,
    mocker: MockerFixture,
) -> None:
    """Test oxo scan run risk command with --api-schema-header populates extra_headers."""
    scan_mocked = mocker.patch(
        "ostorlab.runtimes.local.LocalRuntime.scan", return_value=None
    )

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=HIGH",
            "--description=API exposure",
            "--api-schema-endpoint=https://api.example.com",
            "--api-schema-header=Authorization: Bearer token",
        ],
    )

    assert result.exit_code == 0
    assert scan_mocked.call_count == 1
    assets = scan_mocked.call_args[1].get("assets")
    assert isinstance(assets[0], risk_asset.Risk)
    assert assets[0].api_schema["extra_headers"] == [
        {"name": "Authorization", "value": "Bearer token"}
    ]


def testScanRunRisk_whenApiSchemaFileAndUrlBothProvided_shouldShowError(
    scan_run_cli_runner: testing.CliRunner,
    tmp_path: pathlib.Path,
) -> None:
    """Test oxo scan run risk with both --api-schema-file and --api-schema-url shows error."""
    schema_file = tmp_path / "openapi.yaml"
    schema_file.write_bytes(b"openapi: 3.0.0")

    result = scan_run_cli_runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1",
            "risk",
            "--severity=HIGH",
            "--description=Test",
            f"--api-schema-file={schema_file}",
            "--api-schema-url=https://example.com/openapi.yaml",
        ],
    )

    assert result.exit_code == 2
