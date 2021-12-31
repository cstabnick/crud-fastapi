from os import stat
from fastapi import FastAPI, HTTPException
import psycopg2
import bcrypt
from pydantic import BaseModel

import config

app = FastAPI()

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

def pg_exec_no_return(sql, args=None):
    if args is None:
        args = []

    conn = psycopg2.connect(config.db_conn)
    cur = conn.cursor()

    cur.execute(sql, args)
    # check if it even worked?

    conn.commit()
    
    return True

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



class Users:
    @staticmethod
    def update_session(user_id: int):
        return pg_select_one("select update_session(%(user_id)s)", {"user_id": user_id}, True)

class LoginModel(BaseModel):
    password: str
    email: str
class UsersModel(BaseModel):
    username: str
    password: str
    email: str

@app.post("/users/login")
def login_user(user: LoginModel):
    qry = pg_select_one("select user_id, password from users where email = %s and is_deleted = false", [user.email])

    if qry and len(qry) > 0:
        hashed = bytes(qry["password"])
    else:
        raise HTTPException(status_code=401, detail="Bad!")

    if bcrypt.checkpw(user.password.encode(), hashed):
        return Users.update_session(qry["user_id"])

    else:
        raise HTTPException(status_code=401, detail="Bad!")
    
@app.post("/users/create")
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
        res = pg_insert_return(sql, {"username": user.username, "password": hashed, "email": user.email})
        user_id = res['user_id']
        return Users.update_session(user_id)

    except psycopg2.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Looks like this user already exists")

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    sql = """
        update users set is_deleted = true where user_id = %s
    """
    return pg_exec_no_return(sql, [user_id])

@app.get("/users")
def read_users():
    sql = """
    select user_id, username , email, \"password\"::text 
    from users 
    where is_deleted = false
    order by user_id
    """
    return pg_select_set(sql)

@app.get("/users/{user_id}")
def read_user(user_id: int):
    sql = """
        select user_id, username , email 
        from users 
        where user_id = %(u_id)s
        and is_deleted = false
    """
    return pg_select_one(sql, {"u_id": user_id})



    