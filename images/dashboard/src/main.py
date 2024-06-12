import uuid
from fastapi import FastAPI, Request

# Import database utils
from database import engine

# Import models
from models import stacks_models
from models import sessions_models

# Import routes
from routes.stacks_route import router as stacks_route
from routes.login_route import router as login_route

app = FastAPI()
app.title = "OSM-Sandbox API User"
app.version = "0.1.0"

# Create tables
stacks_models.Base.metadata.create_all(bind=engine)
sessions_models.Base.metadata.create_all(bind=engine)

# Include routes
app.include_router(login_route)
app.include_router(stacks_route)
