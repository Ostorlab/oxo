"""Receive scanner config (Nats creds, container registry creds ...)."""

from typing import Dict, Optional
import json

from ostorlab.apis import request


class ScannerConfigAPIRequest(request.APIRequest):
    """Get scanner config."""

    def __init__(self, scanner_id: str):
        self._scanner_id = scanner_id

    @property
    def query(self) -> Optional[str]:
        """Defines the query to get the configs.

        Returns:
            The query to get the configs.
        """
        return """
         query scanners($scannerUuid: UUID!){
          scanners(scannerUuid: $scannerUuid){
            scanners{
              id
              name
              description
              config{
                registryConfiguration{
                  accountName
                  credentials
                  url
                }
                busUrl
                busClusterId
                busClientName
                subjectBusConfigs{
                    subjectBusConfigs{
                        subject
                        queue
                    }
                }
              }
            }
          }
        }
        """

    @property
    def data(self) -> Optional[Dict]:
        """Sets the query to get the configs.

        Returns:
              The query to get the configs.
        """
        data = {
            "query": self.query,
            "variables": json.dumps({"scannerUuid": self._scanner_id}),
        }
        return data
