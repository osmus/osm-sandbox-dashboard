import os
import uuid
from fastapi import FastAPI, Request, Query, Depends
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

# Import database utils
from database import engine, get_db
# Import utils
from utils.sandbox_database import check_database_instance
from utils.osm_credentials import get_osm_credentials
from utils.sandbox_sessions import save_session
# Import models
from models import stacks_models
from models import sessions_models
# Import routes
from routes.stacks_route import router as stacks_route
from routes.oauth_route import router as oauth_route

app = FastAPI()
app.title = "OSM-Sandbox API User"
app.version = "0.1.0"

# Create tables
stacks_models.Base.metadata.create_all(bind=engine)
sessions_models.Base.metadata.create_all(bind=engine)

# Get OSM credentials
client_id, client_secret, redirect_uri, osm_instance_url, osm_instance_scopes = get_osm_credentials()

# Custom static files to set cache control
class CustomStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "public, max-age=86400"
        return response

static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", CustomStaticFiles(directory=static_path), name="static")

templates_path = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_path)

# Middleware to add unique ID cookie
@app.middleware("http")
async def add_unique_id_cookie(request: Request, call_next):
    response = await call_next(request)
    if "unique_id" not in request.cookies:
        unique_id = str(uuid.uuid4())
        response.set_cookie(key="unique_id", value=unique_id)
    return response

# Home route
@app.get("/", tags=["Home"])
def home(request: Request, stack: str = Query(None), db: Session = Depends(get_db)):
    unique_id = request.cookies.get("unique_id")
    if unique_id and stack:
        save_session(db, unique_id, stack)
    req_obj = {
        "request": request,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "osm_instance_url": osm_instance_url,
        "osm_instance_scopes": osm_instance_scopes,
        "stack": stack,
        "unique_id": unique_id
    }
    return templates.TemplateResponse("index.html", req_obj)

# Include routes
app.include_router(stacks_route)
app.include_router(oauth_route)
