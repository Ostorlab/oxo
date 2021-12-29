"""TODO(mohsine):Wrtite docstring."""
import enum
import json
from typing import Dict, Optional, BinaryIO

from . import request


class MobileAssetType(enum.Enum):
    ANDROID = enum.auto()
    IOS = enum.auto()


class Plan(enum.Enum):
    FREE = enum.auto()


class CreateMobileScanAPIRequest(request.APIRequest):
    """TODO(mohsine):Wrtite docstring."""

    def __init__(self, title: str, asset_type: MobileAssetType, plan: Plan, application: BinaryIO):
        self._title = title
        self._asset_type = asset_type
        self._plan = plan
        self._application = application

    @property
    def query(self) -> Optional[str]:
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
        data = {
            'operations': json.dumps({'query': self.query,
                                      'variables': {'title': self._title,
                                                    'assetType': self._asset_type.name.lower(),
                                                    'application': None,
                                                    'plan': self._plan.name.lower(),
                                                    }
                                      }
                                     ),
            '0': self._application,
            'map': json.dumps({
                '0': ['variables.application'],
            })
        }
        return data
