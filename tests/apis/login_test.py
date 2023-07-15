"""Unittests for testing the login API"""
from ostorlab.apis import login


def testLogin_always_returnData():
    login_api_test = login.UsernamePasswordLoginAPIRequest(
        username="me", password="myPassword123", otp_token="Token"
    )

    assert login_api_test.data == {
        "username": "me",
        "password": "myPassword123",
        "otp_token": "Token",
    }
