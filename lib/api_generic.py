from pydantic import BaseModel
import pydantic
from typing import List
from fastapi import APIRouter

from lib.util import ITUtil
import models

class APIGeneric:
    @staticmethod
    def define_generic_api(db_table_name: str, router: APIRouter, endpoints_to_create: list = []):
        db_table_name_singular = db_table_name[0:-1]
        db_table_id = db_table_name_singular + "_id"

        if endpoints_to_create == []:
            endpoints_to_create = ["create", "read", "update", "delete"]

        model_name = f"models.{db_table_name}.IT{db_table_name.title()}.{db_table_name.title()}Model"        

        #pydantic.create_model()
        #model_construct = model.__init__()
        python = ""

        if "delete" in endpoints_to_create:
            python += f"""
            
@staticmethod
@router.delete("/{db_table_name}/{{{db_table_id}}}}}")
def delete_{db_table_name_singular}({db_table_id}: int):
    sql = \"\"\"
        update {db_table_name} set is_deleted = true where {db_table_id} = %s
    \"\"\"
    return ITUtil.pg_exec_no_return(sql, [{db_table_id}])
            """

        if "read" in endpoints_to_create:
            python += f"""
@staticmethod
@router.get("/{db_table_name}", response_model=List[{model_name}])
def read_{db_table_name}(limit: int = 100, skip: int = 0):
    {db_table_name} = ITUtil.get_by_model({model_name}(), limit, skip)
    return {db_table_name}

@staticmethod
@router.get("/{db_table_name}/{{{db_table_id}}}", response_model={model_name})
def read_{db_table_name_singular}({db_table_id}: int):
    return ITUtil.get_by_model_id({model_name}(), {{"{db_table_id}": {db_table_id}}})
            
            """
        exec(python)


