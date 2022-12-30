#!/usr/bin/env python
#
# File: $Id$
#
"""
Webhook destination for Postmark to deliver email.
"""
# system imports
#
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

# 3rd party imports
#
import aiofiles
import yaml
from aiologger import Logger
from dotenv import dotenv_values
from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.security.api_key import (
    APIKey,
    APIKeyCookie,
    APIKeyHeader,
    APIKeyQuery,
)
from starlette.responses import JSONResponse, RedirectResponse
from starlette.status import HTTP_403_FORBIDDEN

# project imports
from .utils import short_hash_email

########
#
# FastAPI app initialization
#
logger = Logger.with_default_handlers(name="postmarkd")

# Load our configuration in to the dict CONFIG. The .env file in the directory
# that uvicorn is being launched from provides the defaults. Variables set in
# the environment will override those defaults.
#
ENV = {
    **dotenv_values(Path.cwd() / ".env"),
    **os.environ,  # override loaded values with environment variables
}

CONFIG_FILE = Path(ENV.get("CONFIG_FILE", "/usr/local/etc/postmark.yaml"))
CONFIG = yaml.load(CONFIG_FILE.read_text(), Loader=yaml.Loader)
SPOOL_DIR = Path(CONFIG.get("spool_dir", "/var/spool/postmark"))
COOKIE_DOMAIN = CONFIG.get("cookie_domain", "localtest.me")

# Initialze the FastAPI app and setup our API key based authentication.
#
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


####################################################################
#
def map_api_keys_to_users(credentials: Dict[str, Dict]) -> Dict[str, Dict]:
    """
    We create a dict where the keys are all the listed api keys and the
    value is a dict of "expiry", "username", and "permissions" so we can
    quickly look up an api key.
    """
    api_keys = {}
    for user, creds in credentials.items():
        for api_key in creds["api_keys"]:
            api_keys[api_key["key"]] = {
                "user": user,
                "expiry": api_key["expiry"],
                "permissions": api_key["permissions"],
            }
    return api_keys


API_KEYS = map_api_keys_to_users(CONFIG["credentials"])
API_KEY_NAME = "api_key"
api_key_query = APIKeyQuery(name=API_KEY_NAME, auto_error=False)
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
api_key_cookie = APIKeyCookie(name=API_KEY_NAME, auto_error=False)
#
# End FastAPI app initialization
#
########


####################################################################
#
async def get_api_key(
    api_key_query: str = Security(api_key_query),
    api_key_header: str = Security(api_key_header),
    api_key_cookie: str = Security(api_key_cookie),
):

    # XXX We should also make sure that api_key has not expired.
    #
    if api_key_query in API_KEYS:
        return (api_key_query, API_KEYS[api_key_query])
    elif api_key_header in API_KEYS:
        return (api_key_header, API_KEYS[api_key_header])
    elif api_key_cookie in API_KEYS:
        return (api_key_cookie, API_KEYS[api_key_cookie])
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )


####################################################################
#
@app.on_event("startup")
async def startup():
    await logger.info("Postmark Webhooks server starting up")


####################################################################
#
@app.on_event("shutdown")
async def shutdown():
    await logger.info("Postmark Webhooks server shutting down")
    await logger.shutdown()


####################################################################
#
@app.get("/")
async def root():
    """
    Root URL.. nothing here, but say it.
    """
    return "Hello."


####################################################################
#
@app.post("/inbound/{stream}/")
async def inbound(
    email_post: Request,
    stream: str,
    api_key_data: APIKey = Depends(get_api_key),
):
    """
    This method will be called when Postmark receives email for us
    and is deliverying to us as a POST. The content will be json.

    The `stream` variable tells us which mail service this is for. If `stream`
    does not match any of the configured mail services, a 404 is returned.

    We store these emails in the received email directory. The file
    name will be the timestamp of when it was received and the first 8
    characters of the sha256 of the raw email message.

    The directory is the configured `spool_dir`
    """
    # Make sure that the api key used is allowed to post to `inbound` for
    # `<stream>`
    #
    api_key, api_key_info = api_key_data
    if stream in api_key_info["permissions"]:
        if "inbound" not in api_key_info["permissions"][stream]:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="Permission denied credentials",
            )
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Permission denied credentials",
        )

    email = await email_post.json()

    short_hash = short_hash_email(email)
    now = datetime.now().isoformat()
    email_file_name = f"{now}-{short_hash}.json"
    stream_spool_dir = SPOOL_DIR / stream
    stream_spool_dir.mkdir(exist_ok=True)
    fname = stream_spool_dir / email_file_name

    # We need to make sure that the file is written before we send our
    # response back to Postmark.. but we should not block other async
    # processing while waiting for the file to be written.
    #
    async with aiofiles.open(fname, "w") as f:
        await f.write(json.dumps(email))

    # XXX here is where would send a signal or spawn an async task to notify
    #     anyone that is listening that mail was received and needs to be
    #     processed. This notification should not block us sending our
    #     response back to postmark.
    #

    response = JSONResponse({"status": "all good"})
    response.set_cookie(
        API_KEY_NAME,
        value=api_key,
        domain=COOKIE_DOMAIN,
        httponly=True,
        max_age=1800,
        expires=1800,
    )
    return response


####################################################################
#
def list_messages():
    """ """
    pass


####################################################################
#
@app.get("/logout")
async def logout():
    """
    Redirects to `/` and deletes the API key cookie.
    """
    response = RedirectResponse(url="/")
    response.delete_cookie(API_KEY_NAME, domain=COOKIE_DOMAIN)
    return response
