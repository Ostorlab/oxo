from ostorlab.apis import test_credentials_create as test_credentials_create_api


def test_test_credential_email_2fa_to_variables():
    credential = test_credentials_create_api.TestCredentialEmail2FA(
        sender_email_address="sender@ex.com",
        email_address="user@ex.com",
        password="password",
    )
    expected = {
        "testCredentials": {
            "email2FA": {
                "senderEmailAddress": "sender@ex.com",
                "emailAddress": "user@ex.com",
                "password": "password",
            }
        }
    }
    assert credential.to_variables() == expected


def test_test_credential_sms_2fa_to_variables():
    credential = test_credentials_create_api.TestCredentialSMS2FA(
        sender_phone_number="+123"
    )
    expected = {
        "testCredentials": {
            "sms2FA": {
                "senderPhoneNumber": "+123",
            }
        }
    }
    assert credential.to_variables() == expected


def test_test_credential_totp_2fa_to_variables():
    credential = test_credentials_create_api.TestCredentialTOTP2FA(totp_seed="123456")
    expected = {
        "testCredentials": {
            "totp2FA": {
                "totpSeed": "123456",
            }
        }
    }
    assert credential.to_variables() == expected
