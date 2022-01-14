import time
from fastapi import APIRouter, HTTPException, Request
from typing import Optional, List

from pydantic import BaseModel
import psycopg2
import bcrypt
from datetime import datetime

from lib.users import ITUsers
from lib.util import ITUtil

router = APIRouter()

class ITUsersAPI: 
    class UsersModel(BaseModel):
        user_id: Optional[int]
        username: Optional[str]
        password: Optional[str]
        email: Optional[str]
        created_at: Optional[datetime]
        updated_at: Optional[datetime]
        
        current_session_id: Optional[int]

        @staticmethod
        def fields_not_in_db():
            return ["current_session_id"]

        @staticmethod        
        def required_on_create_fields():
            return ["username", "password", "email"]
        
        @staticmethod
        def fields_not_returned():
            return ["password"]
    
    @staticmethod
    @router.post("/users/login")
    def login_user(user: UsersModel, response_model=UsersModel):
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
            user = ITUtil.get_by_model(ITUsersAPI.UsersModel(), 1, 0, True, {"user_id": qry["user_id"]})[0]
            user['current_session_id'] = ITUsers.update_session(user['user_id'])['session_id']
            return user
        else:
            raise HTTPException(status_code=401, detail="Bad!")

    @staticmethod
    @router.post("/users/create", response_model=UsersModel)
    def create_user(user: UsersModel, request: Request):
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
    @router.get("/users", response_model=List[UsersModel])
    def read_users(limit: int = 100, skip: int = 0):
        users = ITUtil.get_by_model(ITUsersAPI.UsersModel(), limit, skip)
        return users

    @staticmethod
    @router.get("/users/{user_id}", response_model=UsersModel)
    def read_user(user_id: int):
        return ITUtil.get_by_model(ITUsersAPI.UsersModel(), 1, 0, True, {"user_id": user_id})
        