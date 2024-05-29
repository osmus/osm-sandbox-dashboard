import os
import psycopg2
from psycopg2 import OperationalError

db_port = os.getenv("SANDBOX_PG_DB_PORT")
db_user = os.getenv("SANDBOX_PG_DB_USER")
db_password = os.getenv("SANDBOX_PG_DB_PASSWORD")
db_name = os.getenv("SANDBOX_PG_DB_NAME")

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
