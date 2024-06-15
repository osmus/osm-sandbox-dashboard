import uuid
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

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


# Home route
@app.get("/", tags=["Home"])
def home(request: Request):
    response = {
        "status": "0k",
    }
    return JSONResponse(content=response)


# Include routes
app.include_router(login_route)
app.include_router(stacks_route)
