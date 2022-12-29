#!/usr/bin/env python
#
# File: $Id$
#
"""
Initial pytest fixtures
"""
# system imports
#
import os
from unittest import mock

# 3rd party imports
#
import pytest
import yaml
from starlette.testclient import TestClient


####################################################################
#
@pytest.fixture
def inbound_test_data():
    # XXX Consider using a json fixture file
    #
    return {
        "FromName": "Postmarkapp Support",
        "MessageStream": "inbound",
        "From": "support@postmarkapp.com",
        "FromFull": {
            "Email": "support@postmarkapp.com",
            "Name": "Postmarkapp Support",
            "MailboxHash": "",
        },
        "To": '"Firstname Lastname" <yourhash+SampleHash@inbound.postmarkapp.com>',
        "ToFull": [
            {
                "Email": "yourhash+SampleHash@inbound.postmarkapp.com",
                "Name": "Firstname Lastname",
                "MailboxHash": "SampleHash",
            }
        ],
        "Cc": '"First Cc" <firstcc@postmarkapp.com>, secondCc@postmarkapp.com>',
        "CcFull": [
            {
                "Email": "firstcc@postmarkapp.com",
                "Name": "First Cc",
                "MailboxHash": "",
            },
            {
                "Email": "secondCc@postmarkapp.com",
                "Name": "",
                "MailboxHash": "",
            },
        ],
        "Bcc": '"First Bcc" <firstbcc@postmarkapp.com>, secondbcc@postmarkapp.com>',
        "BccFull": [
            {
                "Email": "firstbcc@postmarkapp.com",
                "Name": "First Bcc",
                "MailboxHash": "",
            },
            {
                "Email": "secondbcc@postmarkapp.com",
                "Name": "",
                "MailboxHash": "",
            },
        ],
        "OriginalRecipient": "yourhash+SampleHash@inbound.postmarkapp.com",
        "Subject": "Test subject",
        "MessageID": "73e6d360-66eb-11e1-8e72-a8904824019b",
        "ReplyTo": "replyto@postmarkapp.com",
        "MailboxHash": "SampleHash",
        "Date": "Fri, 1 Aug 2014 16:45:32 -04:00",
        "TextBody": "This is a test text body.",
        "HtmlBody": r"<html><body><p>This is a test html body.</p></body></html>",
        "StrippedTextReply": "This is the reply text",
        "Tag": "TestTag",
        "Headers": [
            {"Name": "X-Header-Test", "Value": ""},
            {"Name": "X-Spam-Status", "Value": "No"},
            {"Name": "X-Spam-Score", "Value": "-0.1"},
            {
                "Name": "X-Spam-Tests",
                "Value": "DKIM_SIGNED,DKIM_VALID,DKIM_VALID_AU,SPF_PASS",
            },
        ],
        "Attachments": [
            {
                "Name": "test.txt",
                "Content": "VGhpcyBpcyBhdHRhY2htZW50IGNvbnRlbnRzLCBiYXNlLTY0IGVuY29kZWQu",
                "ContentType": r"text/plain",
                "ContentLength": 45,
            }
        ],
    }


####################################################################
#
@pytest.fixture(scope="session")
def service_name():
    return "test_service_1.com"  # XXX consider using factory boy


####################################################################
#
@pytest.fixture(scope="session")
def service_api_key():
    return "boobazbapbipboom"  # XXX consider using factory boy


####################################################################
#
@pytest.fixture(scope="session")
def spool_dir(tmp_path_factory, service_name):
    fn = tmp_path_factory.mktemp("spool")
    (fn / service_name).mkdir()
    yield fn


####################################################################
#
@pytest.fixture(scope="session")
def db_dir(tmp_path_factory):
    fn = tmp_path_factory.mktemp("db")
    yield fn


####################################################################
#
@pytest.fixture(scope="session")
def config_data(service_name, service_api_key, spool_dir, db_dir):
    """
    Keyword Arguments:
    service_name    --
    service_api_key --
    """
    config = {
        "mail_services": [service_name],
        "spool_dir": spool_dir,
        "db_dir": db_dir,
        "credentials": {
            "postmark": {
                "api_keys": [
                    {
                        "expiry": 0,
                        "key": service_api_key,
                        "permissions": {service_name: ["inbound"]},
                    }
                ]
            }
        },
    }
    yield config


####################################################################
#
@pytest.fixture(scope="session")
def config_file(tmp_path_factory, config_data):
    """
    the path to the config file for our tests
    """
    fn = tmp_path_factory.mktemp("config") / "config.yaml"
    with fn.open(mode="w") as file:
        yaml.dump(config_data, file)
    yield fn


####################################################################
#
@pytest.fixture(scope="module")
def config_env_var(config_file):
    """
    All of our tests will run pointing to our test config file
    """
    with mock.patch.dict(os.environ, {"CONFIG_FILE": str(config_file)}):
        yield


####################################################################
#
@pytest.fixture(scope="module")
def test_app(config_env_var):
    # import after we have mocked our test env vars.
    #
    from app.main import app

    client = TestClient(app)
    yield client
