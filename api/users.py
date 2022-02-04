from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from typing import ItemsView, List
import bcrypt

from models.users import ITUsers
from lib.error import ITError
from lib.util import ITUtil
from lib.api_generic import APIGeneric

router = APIRouter()
APIGeneric.define_generic_api("users", router, ["delete", "read"])

class ITUsersAPI: 
    @staticmethod 
    @router.post("/users/update", response_model=ITUsers.UsersModel)
    def update_user(update_model: ITUsers.UsersModel):
        current_model = ITUsers.read_user(update_model.user_id)

        ignore_fields = ITUsers.UsersModel.not_allowed_update_fields()
        ignore_fields += ["created_at", "updated_at"]

        provided_keys = list(filter(lambda i: i not in ignore_fields, dict(update_model).keys()))

        dict_update_model = dict(update_model)
        update_keys = []
        for key in provided_keys:
            if key in dict_update_model and dict_update_model[key] is not None:
                if key in current_model and current_model[key] is not None:
                    if dict_update_model[key] != current_model[key]:
                        update_keys += [key]
                else: 
                    update_keys += [key]

        # TODO: Create ITUtil.update_by_model


    @staticmethod
    @router.post("/users/login", response_model=ITUsers.UsersModel, responses={401: {"model": ITError}})
    def login_user(user: ITUsers.UsersModel):
        login_sql = """
            select user_id, password 
            from users 
            where email = %s 
            and is_deleted = false
        """
        
        qry = ITUtil.pg_select_one(login_sql, [user.email])

        if qry and len(qry) > 0:
            hashed = bytes(qry["password"])
        else:
            return JSONResponse(status_code=401, content=ITError("Bad!"))

        if bcrypt.checkpw(user.password.encode(), hashed):
            user = ITUtil.get_by_model(ITUsers.UsersModel(), 1, 0, True, {"user_id": qry["user_id"]})[0]
            user['current_session_id'] = ITUsers.update_session(user['user_id'])['session_id']
            return user
        else:
            return JSONResponse(status_code=401, content=ITError("Bad!"))

    @staticmethod
    @router.post("/users/create", response_model=ITUsers.UsersModel, status_code=status.HTTP_201_CREATED, responses={409: {"model": ITError}})
    def create_user(user: ITUsers.UsersModel):
        password = user.password.encode()

        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password, salt)
        user.password = hashed
        user = ITUtil.create_by_model(user)
        user['current_session_id'] = ITUsers.update_session(user['user_id'])['session_id']

        return user

