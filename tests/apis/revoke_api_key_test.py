"""Unittests for the api key revokin."""
from ostorlab.apis import revoke_api_key


def testRevokeAPIKeyAPIRequest_alaways_returnQuery():
    api_key_id = "API_KEY_123"
    revoke_api_key_request = revoke_api_key.RevokeAPIKeyAPIRequest(
        api_key_id=api_key_id
    )

    expected_query = """
         mutation RevokeApiKey($apiKeyId: String!) {
               revokeApiKey(apiKeyId: $apiKeyId) {
                  result
               }
            }
        """

    assert revoke_api_key_request.query == expected_query


def testRevokeAPIKeyAPIRequest_always_returnData():
    api_key_id = "API_KEY_123"
    revoke_api_key_request = revoke_api_key.RevokeAPIKeyAPIRequest(
        api_key_id=api_key_id
    )

    expected_variables = '{"apiKeyId": "API_KEY_123"}'

    assert revoke_api_key_request.data["variables"] == expected_variables

    expected_query = """
         mutation RevokeApiKey($apiKeyId: String!) {
               revokeApiKey(apiKeyId: $apiKeyId) {
                  result
               }
            }
        """

    assert revoke_api_key_request.data["query"] == expected_query
