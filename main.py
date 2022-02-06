from os import stat
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.params import Depends
import psycopg2
import json
import bcrypt

from lib.util import ITUtil
from api import users

app = FastAPI()


@app.middleware("http")
async def log_request_response(request: Request, call_next):
    response = await call_next(request)
    # Consuming FastAPI response and grabbing body here
    resp_body = [section async for section in response.__dict__['body_iterator']]
    # Repairing FastAPI response
    response.__setattr__('body_iterator', ITUtil.AsyncIteratorWrapper(resp_body))

    # Formatting response body for logging
    try:
        resp_body = json.loads(resp_body[0].decode())
    except:
        resp_body = str(resp_body)

    # TODO: log json reps of request / response 

    return response

app.include_router(users.router)
