from typing import Optional, List
from datetime import datetime
import bcrypt
from fastapi.responses import JSONResponse

from lib.error import ITError
from lib.util import ITUtil
from lib.model import ITModel

class ITUsers:
    class UsersModel(ITModel):
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
        def not_allowed_update_fields():
            return ["email"] 
        
        @staticmethod
        def fields_not_returned():
            return ["password"]
            
    @staticmethod
    def update_session(user_id: int):
        return ITUtil.pg_select_one("select update_session(%(user_id)s) as session_id", {"user_id": user_id}, True)

    @staticmethod
    def update_user(user: UsersModel, null_fields: Optional[List[str]]=[]):
        current_model = ITUsers.read_user(user.user_id)

        ignore_fields = ITUsers.UsersModel.not_allowed_update_fields()
        ignore_fields += ["created_at", "updated_at"]

        provided_keys = list(filter(lambda i: i not in ignore_fields, dict(user).keys()))

        dict_user = dict(user)
        update_keys = []
        for key in provided_keys:
            if key in dict_user and dict_user[key] is not None:
                if key in current_model and current_model[key] is not None:
                    if dict_user[key] != current_model[key]:
                        update_keys += [key]
                else: 
                    update_keys += [key]

        update_obj = {}
        for i in dict_user.keys():
            if i in null_fields:
                update_obj[i] = None
                continue

            if i in update_keys:
                update_obj[i] = dict_user[i]

        if update_obj == {}:
            return ITUsers.read_user(dict_user['user_id'])  

        if 'password' in update_obj:
            password = update_obj['password'].encode()

            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password, salt)
            update_obj['password'] = hashed

        field_values = '\n, '.join([f"{key} = null" if update_obj[key] is None else f"{key} = %(" + str(key) + ")s" for key in update_obj.keys()])
        update_obj['user_id'] = dict_user['user_id']

        sql = f"""
            update users 
            set {field_values}
            , updated_at = now() 
            where user_id = %(user_id)s 
            returning user_id
            """

        res = ITUtil.pg_update_return(sql, update_obj)
        if res and 'user_id' in res:
            return ITUsers.read_user(res['user_id'])  

    @staticmethod
    def login_user(user: UsersModel):
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
    def create_user(user: UsersModel):
        password = user.password.encode()

        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password, salt)
        user.password = hashed
        user = ITUtil.create_by_model(user)
        user['current_session_id'] = ITUsers.update_session(user['user_id'])['session_id']

        return user
