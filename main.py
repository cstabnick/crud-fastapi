from os import stat
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.params import Depends
import psycopg2
import json
import bcrypt

from api import users

app = FastAPI()

class async_iterator_wrapper:
    def __init__(self, obj):
        self._it = iter(obj)
    def __aiter__(self):
        return self
    async def __anext__(self):
        try:
            value = next(self._it)
        except StopIteration:
            raise StopAsyncIteration
        return value

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    response = await call_next(request)
    # Consuming FastAPI response and grabbing body here
    resp_body = [section async for section in response.__dict__['body_iterator']]
    # Repairing FastAPI response
    response.__setattr__('body_iterator', async_iterator_wrapper(resp_body))

    # Formatting response body for logging
    try:
        resp_body = json.loads(resp_body[0].decode())
    except:
        resp_body = str(resp_body)

    # TODO: log json reps of request / response 

    return response

app.include_router(users.router)
