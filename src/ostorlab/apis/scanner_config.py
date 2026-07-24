"""Receive scanner config (Nats creds, container registry creds ...)."""

import json
from typing import Any

from ostorlab.apis import request


class ScannerConfigAPIRequest(request.APIRequest):
    """Get scanner config."""

    def __init__(self, scanner_id: str):
        self._scanner_id = scanner_id

    @property
    def query(self) -> str | None:
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
                scanResourceRequirements
                apiKey
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
    def data(self) -> dict[str, Any] | None:
        """Sets the query to get the configs.

        Returns:
              The query to get the configs.
        """
        data = {
            "query": self.query,
            "variables": json.dumps({"scannerUuid": self._scanner_id}),
        }
        return data
