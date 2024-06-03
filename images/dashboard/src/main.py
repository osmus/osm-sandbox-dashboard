import uuid
from fastapi import FastAPI, Request

# Import database utils
from database import engine

# Import models
from models import stacks_models
from models import sessions_models

# Import routes
from routes.stacks_route import router as stacks_route
from routes.oauth_route import router as oauth_route
from routes.main_route import router as main_route

app = FastAPI()
app.title = "OSM-Sandbox API User"
app.version = "0.1.0"

# Create tables
stacks_models.Base.metadata.create_all(bind=engine)
sessions_models.Base.metadata.create_all(bind=engine)


# Middleware to add unique ID cookie
@app.middleware("http")
async def add_unique_id_cookie(request: Request, call_next):
    response = await call_next(request)
    if "unique_id" not in request.cookies:
        unique_id = str(uuid.uuid4())
        response.set_cookie(key="unique_id", value=unique_id)
    return response


# Include routes
app.include_router(main_route)
app.include_router(stacks_route)
app.include_router(oauth_route)
