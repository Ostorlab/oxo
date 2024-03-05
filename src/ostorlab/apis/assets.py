"""Create Asset via an API Request."""

import json
from typing import Dict, Optional

from ostorlab.apis import request
from ostorlab.assets import asset as base_asset
from ostorlab.assets import android_aab
from ostorlab.assets import android_apk
from ostorlab.assets import file
from ostorlab.assets import ios_ipa
from ostorlab.assets import domain_name
from ostorlab.assets import link
from ostorlab.assets import ip
from ostorlab.assets import ipv4
from ostorlab.assets import ipv6
from ostorlab.assets import ios_store
from ostorlab.assets import android_store


class CreateAssetAPIRequest(request.APIRequest):
    """Persist asset API request"""

    def __init__(self, asset: base_asset.Asset) -> None:
        """Constructs all the necessary attributes for the object."""
        self._asset = asset

    @property
    def query(self) -> Optional[str]:
        """Sets the query of the API request.

        Returns:
            The query to create the asset.
        """
        return """
        mutation CreateAsset($asset: AssetInputType!) {
              createAsset(asset: $asset) {
                asset {
                  ... on AndroidAssetType {
                    id
                  }
                  ... on IOSAssetType {
                    id
                  }
                  ... on AndroidFileAssetType {
                    id
                  }
                  ... on IOSFileAssetType {
                    id
                  }
                  ... on AndroidStoreAssetType {
                    id
                  }
                  ... on IOSStoreAssetType {
                    id
                  }
                  ... on UrlAssetType {
                    id
                  }
                  ... on NetworkAssetType {
                    id
                  }
                }
              }
            }
        """

    @property
    def data(self) -> Optional[Dict]:
        """Sets the body of the API request.

        Returns:
            The body of the create asset request.
        """
        variables = {"asset": {"tags": []}}
        asset_type_variables = self.__get_asset_variables()
        variables["asset"].update(asset_type_variables)

        if any(
            isinstance(self._asset, t)
            for t in (
                android_aab.AndroidAab,
                android_apk.AndroidApk,
                file.File,
                ios_ipa.IOSIpa,
            )
        ):
            map_variables = self._get_map_variables()
            data = {
                "operations": json.dumps(
                    {"query": self.query, "variables": json.dumps(variables)}
                ),
                "map": json.dumps(map_variables),
            }
        else:
            data = {"query": self.query, "variables": json.dumps(variables)}
        return data

    @property
    def files(self) -> Optional[Dict]:
        """Sets the file for multipart upload of the API request.

        Returns:
            The file mapping of the create asset request.
        """
        if any(
            isinstance(self._asset, t)
            for t in (
                android_aab.AndroidAab,
                android_apk.AndroidApk,
                file.File,
                ios_ipa.IOSIpa,
            )
        ):
            return {"0": self._asset.content}
        else:
            return None

    def __get_asset_variables(self) -> Dict[str, Dict]:
        """Creates asset variables for the API request, depending on the type of the asset."""
        asset_type_variables = {}
        if isinstance(self._asset, (android_aab.AndroidAab, android_apk.AndroidApk)):
            asset_type_variables = {"androidFile": {"file": None}}
        elif isinstance(self._asset, ios_ipa.IOSIpa):
            asset_type_variables = {"iosFile": {"file": None}}
        elif isinstance(self._asset, file.File):
            asset_type_variables = {"file": {"content": None, "path": self._asset.path}}
        elif isinstance(self._asset, domain_name.DomainName):
            asset_type_variables = {"domain": {"domain": self._asset.name}}
        elif isinstance(self._asset, link.Link):
            asset_type_variables = {"url": {"urls": [self._asset.url]}}
        elif isinstance(self._asset, ios_store.IOSStore):
            asset_type_variables = {
                "iosStore": {
                    "applicationName": "",
                    "packageName": self._asset.bundle_id,
                }
            }
        elif isinstance(self._asset, android_store.AndroidStore):
            asset_type_variables = {
                "androidStore": {
                    "applicationName": "",
                    "packageName": self._asset.package_name,
                }
            }
        elif isinstance(self._asset, ip.IP):
            asset_type_variables = {
                "ip": {
                    "host": self._asset.host,
                    "mask": self._asset.mask,
                    "version": self._asset.version,
                }
            }
        elif isinstance(self._asset, ipv4.IPv4):
            asset_type_variables = {
                "ipV4": {
                    "host": self._asset.host,
                    "mask": self._asset.mask,
                    "version": self._asset.version,
                }
            }
        elif isinstance(self._asset, ipv6.IPv6):
            asset_type_variables = {
                "ipV6": {
                    "host": self._asset.host,
                    "mask": self._asset.mask,
                    "version": self._asset.version,
                }
            }
        elif isinstance(self._asset, list):
            if all(isinstance(a, link.Link) for a in self._asset) is True:
                asset_type_variables = {
                    "url": {"urls": [url_asset.url for url_asset in self._asset]}
                }
            else:
                raise NotImplementedError("Make sure every asset has type URL.")
        else:
            raise NotImplementedError(f"Unknown asset type : {type(self._asset)}")

        return asset_type_variables

    def _get_map_variables(self):
        """Creates map variables for the API request, depending on the type of the asset."""
        map_variables = {}
        if isinstance(self._asset, (android_aab.AndroidAab, android_apk.AndroidApk)):
            map_variables = {"0": ["variables.asset.androidFile.file"]}
        elif isinstance(self._asset, ios_ipa.IOSIpa):
            map_variables = {"0": ["variables.asset.iosFile.file"]}
        elif isinstance(self._asset, file.File):
            map_variables = {"0": ["variables.asset.file.content"]}

        return map_variables
