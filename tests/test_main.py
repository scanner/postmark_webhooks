#!/usr/bin/env python
#
# File: $Id$
#
"""
Tests for the `main` module of our FastAPI app.
"""
# system imports
#
import json

# Project imports
#
from app.utils import short_hash_email

# 3rd party imports
#


####################################################################
#
def test_root(test_app):
    response = test_app.get("/")
    assert response.status_code == 200
    assert response.json() == "Hello."


####################################################################
#
def test_logout(test_app):
    response = test_app.get("/logout")
    assert response.status_code == 200
    assert response.json() == "Hello."


####################################################################
#
def test_inbound_success(
    test_app, service_name, service_api_key, spool_dir, inbound_test_data
):
    """
    Keyword Arguments:
    test_app    --
    test_config --
    """

    response = test_app.post(
        f"/inbound/{service_name}/?api_key={service_api_key}",
        json=inbound_test_data,
    )
    assert response.status_code == 200
    assert response.json() == {"status": "all good"}

    msg_hash = short_hash_email(inbound_test_data)
    service_spool_dir = spool_dir / service_name

    # There should be one and only one file in the directory that
    # matches our hash.
    hash_msgs = list(service_spool_dir.glob(f"*-{msg_hash}.json"))
    assert len(hash_msgs) == 1

    msg = json.loads(hash_msgs[0].read_text())
    assert msg == inbound_test_data


####################################################################
#
def test_list(
    test_app, service_name, service_api_key, spool_dir, inbound_test_data
):
    """
    Keyword Arguments:
    test_app          --
    service_name      --
    service_api_key   --
    spool_dir         --
    inbound_test_data --
    """
    response = test_app.post(
        f"/inbound/{service_name}/?api_key={service_api_key}",
        json=inbound_test_data,
    )
    assert response.status_code == 200

    service_spool_dir = spool_dir / service_name
    msgs = [x.name for x in service_spool_dir.glob("*.json")]
    msgs = sorted(msgs)

    response = test_app.get(f"/list/{service_name}?api_key={service_api_key}")
    assert response.status_code == 200
    assert response.json() == msgs
