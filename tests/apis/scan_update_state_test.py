"""Tests for scan update state API request."""

import json

from ostorlab.apis import scan_update_state


def testScanUpdateStateAPIRequest_whenMinimal_queryContainsUpdateScanStateMutation() -> (
    None
):
    """Test minimal query contains the correct mutation and no asset details."""
    api_request = scan_update_state.ScanUpdateStateAPIRequest(
        scan_id=1, progress="started"
    )

    assert api_request.query is not None
    assert "mutation UpdateScanState" in api_request.query
    assert "$scanId: Int!" in api_request.query
    assert "$progress: String!" in api_request.query
    assert "$scannerId: String" in api_request.query
    assert "deviceId: null" in api_request.query
    assert "asset" not in api_request.query
    assert "agentGroup" not in api_request.query


def testScanUpdateStateAPIRequest_whenFullDetails_queryContainsAssetAndAgentGroup() -> (
    None
):
    """Test full details query includes asset and agentGroup fields."""
    api_request = scan_update_state.ScanUpdateStateAPIRequest(
        scan_id=1, progress="locked", full_details=True
    )

    assert api_request.query is not None
    assert "mutation UpdateScanState" in api_request.query
    assert "$scanId: Int!" in api_request.query
    assert "deviceId: null" not in api_request.query
    assert "asset" in api_request.query
    assert "agentGroup" in api_request.query
    assert "... on UrlAssetType { urls apiSchema apiSchemaUrl }" in api_request.query
    assert "... on AndroidApkAssetType" in api_request.query
    assert "... on IosIpaAssetType" in api_request.query


def testScanUpdateStateAPIRequest_whenFullDetails_queryContainsMultiAssetMembers() -> (
    None
):
    """Test full details query selects every multi asset member.

    Each member carries its own __typename, since that is what it is resolved by, and
    the api schemas are selected with the url of the schema document they hold.
    """
    api_request = scan_update_state.ScanUpdateStateAPIRequest(
        scan_id=1, progress="locked", full_details=True
    )

    assert api_request.query is not None
    assert "... on MultiAssetsAssetType" in api_request.query
    assert "files { __typename path contentUrl }" in api_request.query
    assert "androidPackageName { __typename packageName }" in api_request.query
    assert "iosBundleId { __typename bundleId }" in api_request.query
    assert "androidApk { __typename path contentUrl }" in api_request.query
    assert "androidAab { __typename path contentUrl }" in api_request.query
    assert "iosIpa { __typename path contentUrl }" in api_request.query
    assert "harmonyosBundleName { __typename bundleName }" in api_request.query
    assert "harmonyosApk { __typename path contentUrl }" in api_request.query
    assert "harmonyosAab { __typename path contentUrl }" in api_request.query
    assert "harmonyosHap { __typename path contentUrl }" in api_request.query
    assert "harmonyosApp { __typename path contentUrl }" in api_request.query
    assert "harmonyosRpk { __typename path contentUrl }" in api_request.query
    assert (
        "repositories { __typename provider repositoryUrl commitHash }"
        in api_request.query
    )
    assert "repositoryArchives { __typename path contentUrl }" in api_request.query
    assert "urlAssets: urls { __typename urls }" in api_request.query
    assert "ips { __typename host version mask }" in api_request.query
    assert "ipv4s { __typename host version mask }" in api_request.query
    assert "ipv6s { __typename host version mask }" in api_request.query
    assert "apiSchemas { endpointUrl contentUrl }" in api_request.query


def testScanUpdateStateAPIRequest_whenScanIdAndProgressProvided_dataContainsCorrectVariables() -> (
    None
):
    """Test scan update state API request data contains correct variables."""
    api_request = scan_update_state.ScanUpdateStateAPIRequest(
        scan_id=42, progress="finished"
    )

    data = api_request.data
    assert data is not None
    assert "query" in data
    assert "variables" in data
    variables = json.loads(data["variables"])
    assert variables["scanId"] == 42
    assert variables["progress"] == "finished"
    assert variables["scannerId"] is None


def testScanUpdateStateAPIRequest_whenScannerIdProvided_dataContainsScannerId() -> None:
    """Test scan update state API request data contains the scanner id when provided."""
    api_request = scan_update_state.ScanUpdateStateAPIRequest(
        scan_id=42,
        progress="locked",
        full_details=True,
        scanner_id="GGBD-DJJD-DKJK-DJDD",
    )

    data = api_request.data
    assert data is not None
    assert "variables" in data
    variables = json.loads(data["variables"])
    assert variables["scannerId"] == "GGBD-DJJD-DKJK-DJDD"
    assert "$scannerId: String" in api_request.query
    assert "scannerId: $scannerId" in api_request.query


def testScanUpdateStateAPIRequest_whenFullDetails_dataContainsSameVariables() -> None:
    """Test full details mode produces the same data structure."""
    api_request = scan_update_state.ScanUpdateStateAPIRequest(
        scan_id=7, progress="locked", full_details=True
    )

    data = api_request.data
    assert data is not None
    assert "query" in data
    assert "variables" in data
    variables = json.loads(data["variables"])
    assert variables["scanId"] == 7
    assert variables["progress"] == "locked"
    assert variables["scannerId"] is None


def testScanUpdateStateAPIRequest_whenFullDetails_multiAssetSelectsNoConflictingName() -> (
    None
):
    """Test no multi asset member shares a response name with a sibling asset fragment.

    Fields sharing a response name in one selection set must have the same response
    shape, even on types that cannot both be the concrete one. A member selecting an
    asset under a name a sibling fragment selects a scalar under makes the whole query
    invalid, so every scan reservation fails, not only the multi asset ones. Aliasing
    the member is what keeps the two apart.
    """
    api_request = scan_update_state.ScanUpdateStateAPIRequest(
        scan_id=1, progress="locked", full_details=True
    )
    lines = api_request.query.split("\n")
    multi_asset_start = next(
        index
        for index, line in enumerate(lines)
        if "... on MultiAssetsAssetType" in line
    )
    multi_asset_end = next(
        index
        for index in range(multi_asset_start + 1, len(lines))
        if lines[index].strip() == "}"
    )

    response_names = {
        line.strip().split(" ")[0].split("{")[0].rstrip(":")
        for line in lines[multi_asset_start + 1 : multi_asset_end]
        if line.strip() != ""
    }
    sibling_names = set()
    for line in lines[:multi_asset_start]:
        stripped = line.strip()
        if stripped.startswith("... on ") is True and stripped.endswith("}") is True:
            selection = stripped[stripped.index("{") + 1 : stripped.rindex("}")]
            sibling_names.update(
                token
                for token in selection.split()
                if token not in ("{", "}") and token.endswith(":") is False
            )

    assert response_names & sibling_names == set()
