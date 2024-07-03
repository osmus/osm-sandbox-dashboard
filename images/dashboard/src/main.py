import uuid
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Import database utils
from database import engine

# Import models
from models import boxes
from models import sessions
from models import resources

# Import routes
from routes.boxes import router as stacks_route
from routes.login import router as login_route
from routes.resources import router as resources_route

app = FastAPI()
app.title = "OSM-Sandbox API User"
app.version = "0.1.0"

# Create tables
boxes.Base.metadata.create_all(bind=engine)
sessions.Base.metadata.create_all(bind=engine)
resources.Base.metadata.create_all(bind=engine)


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
app.include_router(resources_route)
