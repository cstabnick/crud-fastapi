from lib.util import ITUtil
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ITUsers:
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
    def update_session(user_id: int):
        return ITUtil.pg_select_one("select update_session(%(user_id)s) as session_id", {"user_id": user_id}, True)
