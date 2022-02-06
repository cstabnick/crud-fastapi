from pydantic import BaseModel, Field
from typing import Optional, List, final

class ITModel(BaseModel):
    
    @final
    @staticmethod
    def fields_not_in_db_base():
        return []

    @staticmethod
    def fields_not_in_db():
        return []

    @staticmethod        
    def required_on_create_fields():
        return []

    @staticmethod
    def not_allowed_update_fields():
        return []
    
    @staticmethod
    def fields_not_returned():
        return []
        