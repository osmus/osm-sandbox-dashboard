import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
SANDBOX_DOMAIN = os.getenv("SANDBOX_DOMAIN", "none")
SANDBOX_PG_DB_PORT = os.getenv("SANDBOX_PG_DB_PORT", "none")
SANDBOX_PG_DB_USER = os.getenv("SANDBOX_PG_DB_USER", "none")
SANDBOX_PG_DB_PASSWORD = os.getenv("SANDBOX_PG_DB_PASSWORD", "none")
SANDBOX_PG_DB_NAME = os.getenv("SANDBOX_PG_DB_NAME", "none")
