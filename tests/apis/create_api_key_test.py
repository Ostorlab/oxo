"""Unittests for testing the create api key API"""
from ostorlab.apis import create_api_key


def testCreateApiKey_always_returnData():
    agent_create_api_key = create_api_key.CreateAPIKeyAPIRequest((2023, 7, 15))

    assert (
        agent_create_api_key.data["variables"]
        == '{"name": "Ostorlab CLI", "expiryDate": [2023, 7, 15]}'
    )

    assert (
        agent_create_api_key.data["query"]
        == """
         mutation CreateApiKey($name: String!, $expiryDate: DateTime) {
               createApiKey(name: $name, expiryDate: $expiryDate) {
                  apiKey {
                     secretKey
                     apiKey {
                        expiryDate
                        id
                     }
                  }
               }
            }
        """
    )
