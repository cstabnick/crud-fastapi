from fastapi import APIRouter, HTTPException, Request
from typing import List
import bcrypt

from lib.users import ITUsers
from lib.util import ITUtil

router = APIRouter()

class ITUsersAPI: 
    @staticmethod
    @router.post("/users/login")
    def login_user(user: ITUsers.UsersModel, response_model=ITUsers.UsersModel):
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
            raise HTTPException(status_code=401, detail="Bad!")

        if bcrypt.checkpw(user.password.encode(), hashed):
            user = ITUtil.get_by_model(ITUsers.UsersModel(), 1, 0, True, {"user_id": qry["user_id"]})[0]
            user['current_session_id'] = ITUsers.update_session(user['user_id'])['session_id']
            return user
        else:
            raise HTTPException(status_code=401, detail="Bad!")

    @staticmethod
    @router.post("/users/create", response_model=ITUsers.UsersModel)
    def create_user(user: ITUsers.UsersModel, request: Request):
        password = user.password.encode()

        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password, salt)
        user.password = hashed
        user = ITUtil.create_by_model(user)
        user['current_session_id'] = ITUsers.update_session(user['user_id'])['session_id']

        return user

    @staticmethod
    @router.delete("/users/{user_id}")
    def delete_user(user_id: int):
        sql = """
            update users set is_deleted = true where user_id = %s
        """
        return ITUtil.pg_exec_no_return(sql, [user_id])

    @staticmethod
    @router.get("/users", response_model=List[ITUsers.UsersModel])
    def read_users(limit: int = 100, skip: int = 0):
        users = ITUtil.get_by_model(ITUsers.UsersModel(), limit, skip)
        return users

    @staticmethod
    @router.get("/users/{user_id}", response_model=ITUsers.UsersModel)
    def read_user(user_id: int):
        user = ITUtil.get_by_model(ITUsers.UsersModel(), 1, 0, True, {"user_id": user_id})[0]
        return user
        