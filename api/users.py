from fastapi import APIRouter, status
from typing import List, Optional

from models.users import ITUsers
from lib.error import ITError
from lib.api_generic import APIGeneric

router = APIRouter()

class ITUsersAPI: 
    @staticmethod 
    @router.post("/users/update", response_model=ITUsers.UsersModel)
    def update_user(user: ITUsers.UsersModel, null_fields: Optional[List[str]]=[]):
        return ITUsers.update_user(user, null_fields)

    @staticmethod
    @router.post("/users/login", response_model=ITUsers.UsersModel, responses={401: {"model": ITError}})
    def login_user(user: ITUsers.UsersModel):
        return ITUsers.login_user(user)

    @staticmethod
    @router.post("/users/create", response_model=ITUsers.UsersModel, status_code=status.HTTP_201_CREATED, responses={409: {"model": ITError}})
    def create_user(user: ITUsers.UsersModel):
        return ITUsers.create_user(user)

APIGeneric.define_generic_api("users", router, ITUsersAPI, ITUsers, ["delete", "read"])
