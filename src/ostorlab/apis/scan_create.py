"""Create mobile scan API."""
import enum
import json
from typing import Dict, Optional, BinaryIO, List

from . import request

SCAN_PROFILES = {
    'fast_scan': 'Fast Scan',
    'full_scan': 'Full Scan',
    # aliases
    'fast': 'Fast Scan',
    'full': 'Full Scan'
}


class MobileAssetType(enum.Enum):
    ANDROID = enum.auto()
    IOS = enum.auto()


class CreateMobileScanAPIRequest(request.APIRequest):
    """Create mobile scan API from a file."""

    def __init__(self, title: str, asset_type: MobileAssetType, scan_profile: str, application: BinaryIO,
                 test_credential_ids: Optional[List[int]] = None):
        self._title = title
        self._asset_type = asset_type
        self._scan_profile = scan_profile
        self._application = application
        self._test_credential_ids = test_credential_ids

    @property
    def query(self) -> Optional[str]:
        """Defines the query to create a mobile scan.

        Returns:
            The query to create a mobile scan
        """

        return """
mutation MobileScan($title: String!, $assetType: String!, $application: Upload!, $scanProfile: String!, $credentialIds: [Int]) {
  createMobileScan(title: $title, assetType: $assetType, application: $application, scanProfile: $scanProfile, credentialIds: $credentialIds) {
    scan {
      id
    }
  }
}
        """

    @property
    def data(self) -> Optional[Dict]:
        """Sets the query and variables to create the scan.

        Returns:
            The query and variables to create a scan.
         """
        data = {
            'operations': json.dumps({'query': self.query,
                                      'variables': {'title': self._title,
                                                    'assetType': self._asset_type.name.lower(),
                                                    'application': None,
                                                    'scanProfile': self._scan_profile,
                                                    'credentialIds': self._test_credential_ids
                                                    }
                                      }
                                     ),
            'map': json.dumps({
                '0': ['variables.application'],
            })
        }
        return data

    @property
    def files(self) -> Optional[Dict]:
        """Sets the file for multipart upload to create the mobile scan.

        Returns:
            The file mapping to create a scan.
        """
        return {'0': self._application}
