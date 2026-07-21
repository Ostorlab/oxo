"""Unit tests for the MultiAsset asset class."""

from ostorlab.assets import android_store
from ostorlab.assets import api_schema as api_schema_asset
from ostorlab.assets import file as file_asset
from ostorlab.assets import ipv4
from ostorlab.assets import link as link_asset
from ostorlab.assets import multi_asset
from ostorlab.assets import repository as repository_asset


def testMultiAsset_whenCreatedWithDefaults_hasEmptyNestedAssets() -> None:
    asset = multi_asset.MultiAsset()

    assert asset.files == []
    assert asset.android_package_name is None
    assert asset.ios_bundle_id is None
    assert asset.harmonyos_bundle_name is None
    assert asset.android_apk is None
    assert asset.android_aab is None
    assert asset.ios_ipa is None
    assert asset.harmonyos_hap is None
    assert asset.harmonyos_apk is None
    assert asset.harmonyos_aab is None
    assert asset.harmonyos_app is None
    assert asset.harmonyos_rpk is None
    assert asset.repositories == []
    assert asset.repository_archives == []
    assert asset.urls == []
    assert asset.ips == []
    assert asset.ipv4s == []
    assert asset.ipv6s == []
    assert asset.api_schemas == []


def testMultiAsset_whenCreatedWithNestedAssets_storesAllNestedAssets() -> None:
    nested_file = file_asset.File(content_url="https://ostorlab.co/app.apk")
    nested_android_store = android_store.AndroidStore(package_name="a.b.c")
    nested_repository = repository_asset.Repository(
        repository_url="https://github.com/Ostorlab/oxo",
        commit_hash="deadbeef",
        provider="GITHUB",
    )
    nested_link = link_asset.Link(url="https://ostorlab.co", method="GET")
    nested_ipv4 = ipv4.IPv4(host="192.168.1.1")

    asset = multi_asset.MultiAsset(
        files=[nested_file],
        android_package_name=nested_android_store,
        repositories=[nested_repository],
        urls=[nested_link],
        ipv4s=[nested_ipv4],
    )

    assert asset.files == [nested_file]
    assert asset.android_package_name == nested_android_store
    assert asset.repositories == [nested_repository]
    assert asset.urls == [nested_link]
    assert asset.ipv4s == [nested_ipv4]


def testMultiAsset_whenCreatedWithApiSchemas_storesApiSchemas() -> None:
    nested_api_schema = api_schema_asset.ApiSchema(
        endpoint_url="https://ostorlab.co/graphql",
        content_url="https://ostorlab.co/schema.json",
        schema_type="graphql",
    )

    asset = multi_asset.MultiAsset(api_schemas=[nested_api_schema])

    assert asset.api_schemas == [nested_api_schema]


def testMultiAsset_whenApiSchemaNested_isListedInStringRepresentation() -> None:
    asset = multi_asset.MultiAsset(
        api_schemas=[
            api_schema_asset.ApiSchema(
                endpoint_url="https://ostorlab.co/graphql", schema_type="graphql"
            )
        ]
    )

    assert (
        str(asset) == "MultiAsset: [API Schema (graphql): https://ostorlab.co/graphql]"
    )


def testMultiAsset_whenProtoFieldAccessed_returnsMultiAssetProtoField() -> None:
    asset = multi_asset.MultiAsset()

    assert asset.proto_field == "multi_asset"
    assert asset.selector == "v3.asset.multi_asset"


def testMultiAsset_whenConvertedToString_listsNestedAssets() -> None:
    asset = multi_asset.MultiAsset(
        android_package_name=android_store.AndroidStore(package_name="a.b.c"),
        urls=[link_asset.Link(url="https://ostorlab.co", method="GET")],
    )

    assert (
        str(asset)
        == "MultiAsset: [Android Store: (a.b.c), Link https://ostorlab.co with method GET]"
    )
