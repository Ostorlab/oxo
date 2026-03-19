import pytest
import click
from unittest.mock import MagicMock
from ostorlab.cli.ci_scan.run.assets import link
from ostorlab.apis import test_credentials_create as test_credentials_create_api


def test_prepare_test_credentials_link_with_single_credential():
    """Test _prepare_test_credentials in link.py with only TOTP."""
    ctx = MagicMock(spec=click.Context)
    ctx.obj = {
        "test_credentials": {
            "test_credentials_login": [],
            "test_credentials_password": [],
            "test_credentials_url": [],
            "test_credentials_role": [],
            "test_credentials_name": [],
            "test_credentials_value": [],
            "email_2fa_sender_email_address": [],
            "email_2fa_email_address": [],
            "email_2fa_password": [],
            "sms_2fa_sender": [],
            "totp_2fa_seed": ["seed123"],
        }
    }

    credentials = link._prepare_test_credentials(ctx)
    assert len(credentials) == 1
    assert isinstance(credentials[0], test_credentials_create_api.TestCredentialTOTP2FA)
    assert credentials[0].totp_seed == "seed123"
