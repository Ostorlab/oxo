"""Unittests for the create scan API request."""

from ostorlab.apis import scan_create
from io import BytesIO


def testCreateMobileScanAPIRequest_always_returnsQuery():
    title = "Mobile Scan Title"
    asset_type = scan_create.MobileAssetType.ANDROID
    scan_profile = "fast_scan"
    test_credential_ids = [1, 2, 3]

    create_mobile_scan_request = scan_create.CreateMobileScanAPIRequest(
        title=title,
        asset_type=asset_type,
        scan_profile=scan_profile,
        application=BytesIO(b"application_content"),
        test_credential_ids=test_credential_ids,
    )

    expected_query = """
mutation MobileScan($title: String!, $assetType: String!, $application: Upload!, $scanProfile: String!, $credentialIds: [Int]) {
  createMobileScan(title: $title, assetType: $assetType, application: $application, scanProfile: $scanProfile, credentialIds: $credentialIds) {
    scan {
      id
    }
  }
}
        """

    assert create_mobile_scan_request.query == expected_query


def test_CreateMobileScanAPIRequest_always_returnsFiles():
    title = "Mobile Scan Title"
    asset_type = scan_create.MobileAssetType.ANDROID
    scan_profile = "fast_scan"
    test_credential_ids = [1, 2, 3]

    application_content = b"application_content"
    application = BytesIO(application_content)

    create_mobile_scan_request = scan_create.CreateMobileScanAPIRequest(
        title=title,
        asset_type=asset_type,
        scan_profile=scan_profile,
        application=application,
        test_credential_ids=test_credential_ids,
    )

    expected_files = {"0": application}

    assert create_mobile_scan_request.files == expected_files
