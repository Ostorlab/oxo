"""Create mobile scan API."""
import enum
import json
from typing import Dict, Optional, BinaryIO

from . import request


PlanMapping = {
    'rapid_static': 'free',
    'full_analysis': 'static_dynamic_backend'
}


class MobileAssetType(enum.Enum):
    ANDROID = enum.auto()
    IOS = enum.auto()


class Plan(enum.Enum):
    FREE = enum.auto()
    STATIC_DYNAMIC_BACKEND = enum.auto()


class CreateMobileScanAPIRequest(request.APIRequest):
    """Create mobile scan API from a file."""

    def __init__(self, title: str, asset_type: MobileAssetType, plan: Plan, application: BinaryIO):
        self._title = title
        self._asset_type = asset_type
        self._plan = plan
        self._application = application

    @property
    def query(self) -> Optional[str]:
        """Defines the query to create a mobile scan.

        Returns:
            The query to create a mobile scan
        """
        return """
mutation MobileScan($title: String!, $assetType: String!, $application: Upload!, $plan: String!) {
      createMobileScan(title: $title, assetType:$assetType, application: $application, plan: $plan) {
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
                                                    'plan': self._plan.name.lower(),
                                                    }
                                      }
                                     ),
            'map': json.dumps({
                '0': ['variables.application'],
            })
        }
        return data

    @property
    def files(self) -> Optional[Dict] :
        """Sets the file for multipart upload to create the mobile scan.

                 Returns:
                       The file mapping to create a scan.
        """
        return {'0': self._application,}
