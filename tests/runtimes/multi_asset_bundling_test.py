"""Unit tests for the multi_asset section of a target group definition."""

import io

import pytest

from ostorlab.agent.message.proto.v3.asset.multi_asset import multi_asset_pb2
from ostorlab.agent.schema import validator
from ostorlab.runtimes import definitions


def _parse_multi_asset_message(yaml_definition: str) -> multi_asset_pb2.Message:
    """Parse a target group yaml and return its multi asset proto message."""
    targets = definitions.AssetsDefinition.from_yaml(
        io.StringIO(yaml_definition)
    ).targets
    message = multi_asset_pb2.Message()
    message.ParseFromString(targets[0].to_proto())
    return message


def testFromYaml_whenMultiAssetSection_shouldBuildSingleMultiAssetTarget() -> None:
    yaml_definition = io.StringIO("""
kind: targetGroup
assets:
  multi_asset:
    ipv4:
      - host: 8.8.8.8
    link:
      - url: https://example.com/login
        method: POST
    androidStore:
      package_name: com.example.app
""")

    targets = definitions.AssetsDefinition.from_yaml(yaml_definition).targets

    assert len(targets) == 1
    assert targets[0].selector == "v3.asset.multi_asset"
    assert len(targets[0].ipv4s) == 1
    assert targets[0].urls[0].method == "POST"
    assert targets[0].android_package_name.package_name == "com.example.app"


def testFromYaml_whenMultiAssetAndStandaloneAssets_shouldEmitBoth() -> None:
    yaml_definition = io.StringIO("""
kind: targetGroup
assets:
  ip:
    - host: 1.1.1.1
  domain:
    - name: standalone.com
  multi_asset:
    ipv4:
      - host: 8.8.8.8
""")

    targets = definitions.AssetsDefinition.from_yaml(yaml_definition).targets

    selectors = [target.selector for target in targets]
    assert selectors == [
        "v3.asset.ip.v4",
        "v3.asset.domain_name",
        "v3.asset.multi_asset",
    ]


def testFromYaml_whenIpIpv4AndIpv6_shouldClassifyIpByVersionIntoIpv4sOrIpv6s() -> None:
    message = _parse_multi_asset_message("""
kind: targetGroup
assets:
  multi_asset:
    ip:
      - host: 10.0.0.1
    ipv4:
      - host: 8.8.8.8
      - host: 192.168.1.0
        mask: 24
    ipv6:
      - host: "2001:4860:4860::8888"
""")

    # A host under `ip` is classified by its address version, so 10.0.0.1 lands in
    # ipv4s alongside the entries from the explicit `ipv4` key.
    assert len(message.ips) == 0
    assert [ip.host for ip in message.ipv4s] == ["10.0.0.1", "8.8.8.8", "192.168.1.0"]
    assert message.ipv4s[2].mask == "24"
    assert [ip.host for ip in message.ipv6s] == ["2001:4860:4860::8888"]


def testFromYaml_whenRepeatedAssets_shouldSerializeAllOfThem() -> None:
    message = _parse_multi_asset_message("""
kind: targetGroup
assets:
  multi_asset:
    link:
      - url: https://example.com/login
    file:
      - url: https://host/a.bin
    repository:
      - repository_url: https://github.com/Ostorlab/oxo
        commit_hash: abc123
    repositoryArchive:
      - url: https://host/archive.zip
""")

    assert len(message.urls) == 1
    assert message.urls[0].method == "GET"
    assert len(message.files) == 1
    assert len(message.repositories) == 1
    assert message.repositories[0].commit_hash == "abc123"
    assert len(message.repository_archives) == 1


def testFromYaml_whenApiSchemaAssets_shouldMapToApiSchemasProtoField() -> None:
    message = _parse_multi_asset_message("""
kind: targetGroup
assets:
  multi_asset:
    apiSchema:
      - endpoint_url: https://example.com/graphql
        schema_type: graphql
      - endpoint_url: https://example.com/openapi
        schema_type: openapi
""")

    assert len(message.api_schemas) == 2
    assert message.api_schemas[0].endpoint_url == "https://example.com/graphql"
    assert message.api_schemas[0].schema_type == "graphql"
    assert message.api_schemas[1].endpoint_url == "https://example.com/openapi"
    assert message.api_schemas[1].schema_type == "openapi"


def testFromYaml_whenApiSchemaWithoutEndpointUrl_shouldRaiseValidationError() -> None:
    yaml_definition = io.StringIO("""
kind: targetGroup
assets:
  multi_asset:
    apiSchema:
      - path: /schema.json
""")

    with pytest.raises(validator.ValidationError, match="endpoint_url"):
        definitions.AssetsDefinition.from_yaml(yaml_definition)


@pytest.mark.parametrize(
    "yaml_key,yaml_body,proto_field",
    [
        ("androidStore", "package_name: com.a.b", "android_package_name"),
        ("iosStore", "bundle_id: com.a.b", "ios_bundle_id"),
        ("harmonyosStore", "bundle_name: com.a.b", "harmonyos_bundle_name"),
        ("androidApkFile", "url: https://host/x.apk", "android_apk"),
        ("androidAabFile", "url: https://host/x.aab", "android_aab"),
        ("iosFile", "url: https://host/x.ipa", "ios_ipa"),
        ("harmonyosHapFile", "url: https://host/x.hap", "harmonyos_hap"),
        ("harmonyosApkFile", "url: https://host/x.apk", "harmonyos_apk"),
        ("harmonyosAabFile", "url: https://host/x.aab", "harmonyos_aab"),
        ("harmonyosAppFile", "url: https://host/x.app", "harmonyos_app"),
        ("harmonyosRpkFile", "url: https://host/x.rpk", "harmonyos_rpk"),
    ],
)
def testFromYaml_whenMobileAsset_shouldMapToItsProtoOneofField(
    yaml_key: str, yaml_body: str, proto_field: str
) -> None:
    message = _parse_multi_asset_message(f"""
kind: targetGroup
assets:
  multi_asset:
    {yaml_key}:
      {yaml_body}
""")

    assert [field.name for field, _ in message.ListFields()] == [proto_field]


def testFromYaml_whenMultiAssetHasTwoMobileAssets_shouldRaiseValidationError() -> None:
    yaml_definition = io.StringIO("""
kind: targetGroup
assets:
  multi_asset:
    androidStore:
      package_name: com.example.app
    iosStore:
      bundle_id: com.example.ios
""")

    with pytest.raises(validator.ValidationError) as exc_info:
        definitions.AssetsDefinition.from_yaml(yaml_definition)

    assert "at most one mobile asset" in str(exc_info.value)


def testFromYaml_whenMultiAssetHasUnsupportedKey_shouldRaiseValidationError() -> None:
    yaml_definition = io.StringIO("""
kind: targetGroup
assets:
  multi_asset:
    domain:
      - name: example.com
""")

    with pytest.raises(validator.ValidationError, match="additionalProperties"):
        definitions.AssetsDefinition.from_yaml(yaml_definition)


def testFromYaml_whenMultiAssetFileHasNoPathNorUrl_shouldRaiseValidationError() -> None:
    yaml_definition = io.StringIO("""
kind: targetGroup
assets:
  multi_asset:
    file:
      - {}
""")

    with pytest.raises(validator.ValidationError) as exc_info:
        definitions.AssetsDefinition.from_yaml(yaml_definition)

    assert "requires either a valid path or a url" in str(exc_info.value)


@pytest.mark.parametrize(
    "yaml_snippet,expected_message",
    [
        ("link:\n      - {}", "non-empty 'url'"),
        ("repository:\n      - {}", "non-empty 'repository_url'"),
        ("ipv4:\n      - {}", "missing required 'host'"),
        ("ipv4:\n      - host: not-an-ip", "invalid IP address"),
        ("ipv4:\n      - host: '2001:db8::1'", "ipv4 entry has an IPv6 address"),
        ("ipv6:\n      - host: 8.8.8.8", "ipv6 entry has an IPv4 address"),
        ("androidStore:\n      {}", "missing required field 'package_name'"),
    ],
)
def testFromYaml_whenInvalidMultiAssetEntry_shouldRaiseValidationError(
    yaml_snippet: str, expected_message: str
) -> None:
    yaml_definition = io.StringIO(f"""
kind: targetGroup
assets:
  multi_asset:
    {yaml_snippet}
""")

    with pytest.raises(validator.ValidationError, match=expected_message):
        definitions.AssetsDefinition.from_yaml(yaml_definition)


def testFromYaml_whenNoMultiAssetSection_shouldOnlyEmitIndividualAssets() -> None:
    yaml_definition = io.StringIO("""
kind: targetGroup
assets:
  ip:
    - host: 8.8.8.8
  link:
    - url: https://example.com
      method: GET
""")

    targets = definitions.AssetsDefinition.from_yaml(yaml_definition).targets

    assert len(targets) == 2
    assert all(target.selector != "v3.asset.multi_asset" for target in targets) is True


def testFromYaml_whenStandaloneRepositoryAndArchive_shouldEmitStandaloneRepositoryAndArchive() -> None:
    yaml_definition = io.StringIO("""
kind: targetGroup
assets:
  repository:
    - repository_url: https://bitbucket.org/mouad-osto/first_repo
      commit_hash: b3bcad48ac9dda7583357e9e0657651dd1f9f032
      provider: bitbucket
  repositoryArchive:
    - url: https://example.com/archive.zip
""")

    targets = definitions.AssetsDefinition.from_yaml(yaml_definition).targets

    assert len(targets) == 2
    assert targets[0].selector == "v3.asset.repository"
    assert targets[1].selector == "v3.asset.file.repository_archive"
