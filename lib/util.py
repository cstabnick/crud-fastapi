import psycopg2
from typing import List
import config
from fastapi import HTTPException

from lib.model import ITModel

class ITUtil:
    class AsyncIteratorWrapper:
        def __init__(self, obj):
            self._it = iter(obj)
        def __aiter__(self):
            return self
        async def __anext__(self):
            try:
                value = next(self._it)
            except StopIteration:
                raise StopAsyncIteration
            return value

    @staticmethod 
    def clean_print_sql(sql, args):
        if type(args) == list:
            for arg in args:
                if arg is None:
                    sql = sql.replace(f"%s", "null", 1)
                elif type(arg) == bytes:
                    sql = sql.replace(f"%s", "'" + arg.decode() + "'::bytea", 1)
                elif type(arg) == str:
                    sql = sql.replace(f"%s", "'" + str(arg) + "'", 1)
                else: 
                    sql = sql.replace(f"%s", str(arg), 1)
            print(sql)
        elif type(args) == dict:
            for arg in args:
                if args[arg] is None:
                    sql = sql.replace(f"%({arg})s", "null", 1)
                elif type(args[arg]) == bytes:
                    sql = sql.replace(f"%({arg})s", "'" + args[arg].decode() + "'::bytea", 1)
                elif type(args[arg]) == str:
                    sql = sql.replace(f"%({arg})s", "'" + str(args[arg]) + "'", 1)
                else: 
                    sql = sql.replace(f"%({arg})s", str(args[arg]), 1)
            print(sql)

    @staticmethod
    def pg_select_one(sql, args=[], commit=False):
        # ITUtil.clean_print_sql(sql, args)

        conn = psycopg2.connect(config.db_conn)
        cur = conn.cursor()
        cur.execute(sql, args)
        fetchone = cur.fetchone()
        
        record = {}
        if fetchone is not None:
            for i in range(len(cur.description)):
                col_name = cur.description[i].name
                value = fetchone[i]
                record[col_name] = value

        if commit:
            conn.commit()

        return record

    @staticmethod
    def pg_select_set(sql, args=[]):
        # ITUtil.clean_print_sql(sql, args)

        conn = psycopg2.connect(config.db_conn)
        cur = conn.cursor()
        cur.execute(sql, args)
        fetchall = cur.fetchall()
        
        records = []
        for row in fetchall:
            record = {}
            
            for i in range(len(cur.description)):
                col_name = cur.description[i].name
                value = row[i]
                record[col_name] = value

            records += [record]

        return records

    @staticmethod
    def pg_exec_no_return(sql, args=[]):
        # ITUtil.clean_print_sql(sql, args)

        conn = psycopg2.connect(config.db_conn)
        cur = conn.cursor()

        cur.execute(sql, args)
        # check if it even worked?

        conn.commit()
        
        return True

    @staticmethod
    def pg_insert_return(sql, args=[]):
        # ITUtil.clean_print_sql(sql, args)

        conn = psycopg2.connect(config.db_conn)
        cur = conn.cursor()

        cur.execute(sql, args)
        
        fetchone = cur.fetchone()

        record = {}
        for i in range(len(cur.description)):
            col_name = cur.description[i].name
            value = fetchone[i]
            record[col_name] = value

        conn.commit()
        
        return record

    @staticmethod 
    def pg_update_return(sql, args):
        return ITUtil.pg_insert_return(sql, args)

    @staticmethod
    def get_by_model(
        model: ITModel, 
        limit: int, 
        skip: int, 
        return_one: bool = False, 
        query_args: dict = None, 
        include_deleted: bool = False
    ) -> List[dict]:
        sql = ""
        if limit > 100:
            limit = 100

        class_name = str(model.__class__)

        start = class_name.rindex(".") + 1
        end = class_name.index("Model")
        pg_table = class_name[start:end].lower()

        fields_to_ignore = model.fields_not_returned() + model.fields_not_in_db() + model.fields_not_in_db_base()

        fields = list(model.__class__.__fields__)
        fields = list(filter(lambda i: i not in fields_to_ignore, fields))

        select_fields = ", ".join(fields)

        sql += f"select {select_fields} \nfrom {pg_table} \nwhere true \n"

        if query_args:
            sql += "and "
            sql += "\nand ".join([f"{qa_key} = %({qa_key})s" for qa_key in query_args.keys()])

        if not include_deleted:
            sql += "\nand is_deleted = false "

        if return_one:
            sql += "\nlimit 1 " 
        else:
            sql += f"\nlimit {limit} offset {skip}"

        res = ITUtil.pg_select_set(sql, query_args)

        if return_one and len(res) > 0: 
            res = [res[0]]
        
        # remove any nondesireables
        nr = model.fields_not_returned()
        [[r.pop(i, None) for i in nr] for r in res]

        return res

    @staticmethod
    def get_by_model_id(model: ITModel, id_map: map):
        records = ITUtil.get_by_model(model, 1, 0, True, id_map)
        if len(records) > 0:
            return records[0]
        else:
            return {}

    @staticmethod
    def create_by_model(model: ITModel, after_insert_sql: list = []):
        sql = ""

        class_name = str(model.__class__)

        start = class_name.rindex(".") + 1
        end = class_name.index("Model")
        pg_table = class_name[start:end].lower()
        
        fields = [i for i in model.__class__.__fields__.copy()]
        [fields.remove(i) for i in model.fields_not_in_db() + model.fields_not_in_db_base()]
        table_id = pg_table[0:-1] + "_id"
        fields.remove(table_id)
        fields.remove("created_at")
        fields.remove("updated_at")

        field_names = ', '.join(fields)
        field_values = ', '.join(["null" if model.__dict__[i] is None else "%(" + str(i) + ")s" for i in fields])

        sql += f"""
            insert into 
            {pg_table} (
                {table_id}, {field_names}
                , created_at
                , updated_at
                , is_deleted
                )
            select 
                new_id('{pg_table}'), {field_values}
                , now()
                , now()
                , false
            """


        for i in range(0, len(after_insert_sql)):
            sql += after_insert_sql[i]


        sql += """
            returning *
            """

        try: 
            res = ITUtil.pg_insert_return(sql, model.__dict__.copy())

            # remove any nondesireables
            [res.pop(i, None) for i in model.fields_not_returned()]

            return res
        except psycopg2.errors.UniqueViolation:
            raise HTTPException(status_code=409, detail=f"This {pg_table[0:-1]} already exists")
        