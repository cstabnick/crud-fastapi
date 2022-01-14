import psycopg2
from pydantic.main import BaseModel
import config
from fastapi import HTTPException

class ITUtil:
    @staticmethod
    def pg_select_one(sql, args=None, commit=False):
        if args is None:
            args = []

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
    def pg_select_set(sql, args=None):
        if args is None:
            args = []

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
    def pg_exec_no_return(sql, args=None):
        if args is None:
            args = []

        conn = psycopg2.connect(config.db_conn)
        cur = conn.cursor()

        cur.execute(sql, args)
        # check if it even worked?

        conn.commit()
        
        return True

    @staticmethod
    def pg_insert_return(sql, args=None):
        if args is None:
            args = []

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
    def get_by_model(model: BaseModel, limit: int, skip: int, return_one: bool = False, query_args: dict = None, include_deleted: bool = False):
        sql = ""
        if limit > 100:
            limit = 100

        class_name = str(model.__class__)

        start = class_name.rindex(".") + 1
        end = class_name.index("Model")
        pg_table = class_name[start:end].lower()
        
        fields = model.__class__.__fields__.copy()
        [fields.pop(i, None) for i in model.fields_not_returned()]
        [fields.pop(i, None) for i in model.fields_not_in_db()]

        select_fields = ", ".join([i for i in fields])

        sql += f"""
            select {select_fields}
            from {pg_table}
            where true 
            """

        if query_args:
            sql += " and "
            sql += " and ".join([f"{qa} = %({qa})s" for qa in query_args.keys()])

        if not include_deleted:
            sql += " and is_deleted = false "

        if return_one:
            sql += " limit 1 " 
        else:
            sql += f"""
                limit {limit} offset {skip}
                """

        res = ITUtil.pg_select_set(sql, query_args)

        if return_one: 
            res = [res[0]]
        
        # remove any nondesireables
        nr = model.fields_not_returned()
        [[r.pop(i, None) for i in nr] for r in res]

        if return_one:
            return res[0]
        else: 
            return res

    @staticmethod
    def create_by_model(model: BaseModel, after_insert_sql: list = []):
        sql = ""

        class_name = str(model.__class__)

        start = class_name.rindex(".") + 1
        end = class_name.index("Model")
        pg_table = class_name[start:end].lower()
        
        fields = [i for i in model.__class__.__fields__.copy()]
        [fields.remove(i) for i in model.fields_not_in_db()]
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
        