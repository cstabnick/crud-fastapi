from os import stat
from fastapi import FastAPI, HTTPException
from fastapi.params import Depends
import psycopg2
import bcrypt

from api import users

app = FastAPI()

app.include_router(users.router)
