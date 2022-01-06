from os import stat
from fastapi import FastAPI, HTTPException
from lib.users import ITUsers
from lib.util import ITUtil
from pydantic import BaseModel
import psycopg2
import bcrypt
from fastapi import APIRouter

router = APIRouter()

class ITUsersAPI:   
    
    class UsersModel(BaseModel):
        username: str
        password: str
        email: str

    class LoginModel(BaseModel):
        password: str
        email: str

    @staticmethod
    @router.post("/users/login")
    def login_user(user: LoginModel):
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
            return ITUsers.update_session(qry["user_id"])
        else:
            raise HTTPException(status_code=401, detail="Bad!")
   
    @staticmethod
    @router.post("/users/login")
    def login_user(user: LoginModel):
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
            return ITUsers.update_session(qry["user_id"])
        else:
            raise HTTPException(status_code=401, detail="Bad!")

    @staticmethod
    @router.post("/users/create")
    def create_user(user: UsersModel):
        password = user.password.encode()

        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password, salt)

        sql = """
            insert into users (user_id, email, username, password, is_deleted,
                created_at, updated_at)
            select new_id('users'), %(email)s, %(username)s, %(password)s, false,
                now(), now()
            returning user_id
            """

        try:
            res = ITUtil.pg_insert_return(sql, {"username": user.username, "password": hashed, "email": user.email})
            user_id = res['user_id']
            return ITUsers.update_session(user_id)

        except psycopg2.errors.UniqueViolation:
            raise HTTPException(status_code=409, detail="Looks like this user already exists")
    
    @staticmethod
    @router.delete("/users/{user_id}")
    def delete_user(user_id: int):
        sql = """
            update users set is_deleted = true where user_id = %s
        """
        return ITUtil.pg_exec_no_return(sql, [user_id])

    @staticmethod
    @router.get("/users")
    def read_users():
        sql = """
        select user_id, username , email, \"password\"::text 
        from users 
        where is_deleted = false
        order by user_id
        """
        return ITUtil.pg_select_set(sql)

    @staticmethod
    @router.get("/users/{user_id}")
    def read_user(user_id: int):
        sql = """
            select user_id, username , email 
            from users 
            where user_id = %(u_id)s
            and is_deleted = false
        """
        return ITUtil.pg_select_one(sql, {"u_id": user_id})

