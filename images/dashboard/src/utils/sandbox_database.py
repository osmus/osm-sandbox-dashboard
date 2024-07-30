import os
import psycopg2
from psycopg2 import OperationalError
from argon2 import PasswordHasher
from datetime import datetime
from config import (
    SANDBOX_PG_DB_PORT,
    SANDBOX_PG_DB_USER,
    SANDBOX_PG_DB_PASSWORD,
    SANDBOX_PG_DB_NAME,
    SANDBOX_DOMAIN,
)

# Start hasher de Argon2
argon2Hasher = PasswordHasher(
    time_cost=16, memory_cost=2**16, parallelism=2, hash_len=32, salt_len=16
)


def check_database_instance(db_host: str) -> str:
    """Check if box's database is running

    Args:
        db_host (str): box database host

    Returns:
        str: return status
    """
    try:
        connection = psycopg2.connect(
            host=db_host,
            port=SANDBOX_PG_DB_PORT,
            user=SANDBOX_PG_DB_USER,
            password=SANDBOX_PG_DB_PASSWORD,
            dbname=SANDBOX_PG_DB_NAME,
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


def save_user_sandbox_db(box_name: str, user_name: str) -> str:
    """Save a new user in the sandbox database

    Args:
        box_name (str): box name
        user_name (str): user name
    """
    # Hash the password
    pass_crypt = argon2Hasher.hash(user_name)
    # Connect to db
    conn = psycopg2.connect(
        dbname=SANDBOX_PG_DB_NAME,
        user=SANDBOX_PG_DB_USER,
        password=SANDBOX_PG_DB_PASSWORD,
        host=f"{box_name}-db",
        port=SANDBOX_PG_DB_PORT,
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
        f"{user_name}@{box_name}.{SANDBOX_DOMAIN}",
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
    cur.execute(query, values)
    conn.commit()
    cur.close()
    conn.close()
