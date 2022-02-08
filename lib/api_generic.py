from pydantic import BaseModel
import pydantic
from typing import List
from fastapi import APIRouter
from lib.util import ITUtil

# include any models needed for generic apis
from models.users import ITUsers

class APIGeneric:
    
    @staticmethod
    def define_generic_api(db_table_name: str, router: APIRouter, it_api_class, it_class, endpoints_to_create: list = ["create", "read", "update", "delete"]):
        db_table_name_singular = db_table_name[0:-1]
        db_table_id = db_table_name_singular + "_id"

        upper_table_name = db_table_name.title()   
        it_class_name = f"IT{upper_table_name}"
        model_name = f"{it_class_name}.{upper_table_name}Model"        
                
        #pydantic.create_model()
        #model_construct = model.__init__()
        python = ""

        if "delete" in endpoints_to_create:
            python += f"""
   
def delete_{db_table_name_singular}({db_table_id}: int):
    sql = \"\"\"
        update {db_table_name} set is_deleted = true where {db_table_id} = %s
    \"\"\"
    return ITUtil.pg_exec_no_return(sql, [{db_table_id}])
setattr(it_class, 'delete_{db_table_name_singular}', staticmethod(delete_{db_table_name_singular}))

@router.delete("/{db_table_name}/{{{db_table_id}}}")
def delete_{db_table_name_singular}_api({db_table_id}: int):
    return {it_class_name}.delete_{db_table_name_singular}({db_table_id})
setattr(it_api_class, 'delete_{db_table_name_singular}_api', staticmethod(delete_{db_table_name_singular}_api))

            """

        if "read" in endpoints_to_create:
            python += f"""

def read_{db_table_name}(limit: int = 100, skip: int = 0):
    return ITUtil.get_by_model({model_name}(), limit, skip)
setattr(it_class, 'read_{db_table_name}', staticmethod(read_{db_table_name}))

@router.get("/{db_table_name}", response_model=List[{model_name}])
def read_{db_table_name}_api(limit: int = 100, skip: int = 0):
    return {it_class_name}.read_{db_table_name}(limit, skip)
setattr(it_api_class, 'read_{db_table_name}_api', staticmethod(read_{db_table_name}_api))


def read_{db_table_name_singular}({db_table_id}: int):
    return ITUtil.get_by_model_id({model_name}(), {{"{db_table_id}": {db_table_id}}})
setattr(it_class, 'read_{db_table_name_singular}', staticmethod(read_{db_table_name_singular}))

@router.get("/{db_table_name}/{{{db_table_id}}}", response_model={model_name})
def read_{db_table_name_singular}_api({db_table_id}: int):
    return {it_class_name}.read_{db_table_name_singular}({db_table_id})
setattr(it_api_class, 'read_{db_table_name_singular}_api', staticmethod(read_{db_table_name_singular}_api))
                
            """
        exec(python)