import os
import psycopg2
from psycopg2 import OperationalError
from argon2 import PasswordHasher
from datetime import datetime

db_port = os.getenv("SANDBOX_PG_DB_PORT")
db_user = os.getenv("SANDBOX_PG_DB_USER")
db_password = os.getenv("SANDBOX_PG_DB_PASSWORD")
db_name = os.getenv("SANDBOX_PG_DB_NAME")

# Start hasher de Argon2
argon2Hasher = PasswordHasher(
    time_cost=16, memory_cost=2**16, parallelism=2, hash_len=32, salt_len=16
)


def check_database_instance(db_host: str) -> str:
    try:
        connection = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            dbname=db_name,
        )
        connection.close()
        return "running"
    except OperationalError as e:
        if "could not connect to server" in str(e):
            return "not running"
        else:
            return "not found"
    except Exception as e:
        return f"error: {e}"


def save_user_sandbox_db(stack_name, user_name) -> str:
    # Hash the password
    pass_crypt = argon2Hasher.hash(user_name)
    # Connect to db
    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=f"{stack_name}-db",
        port=db_port,
    )
    cur = conn.cursor()
    # Insert a new user
    query = """
    INSERT INTO users (
        email, display_name, pass_crypt, data_public, email_valid, status,
        terms_seen, terms_agreed, tou_agreed, creation_time, changesets_count
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (email) DO NOTHING;
    """
    values = (
        f"{user_name}@sandbox.org",
        user_name,
        pass_crypt,
        True,
        True,
        "active",
        True,
        datetime.now(),
        datetime.now(),
        datetime.now(),
        0,
    )
    # Save
    cur.execute(query, values)
    conn.commit()
    cur.close()
    conn.close()
