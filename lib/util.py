import psycopg2
import config

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
        if fetchone != None:
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