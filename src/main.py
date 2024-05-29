import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from requests_oauthlib import OAuth2Session
from database import engine

from utils.sandbox_database import check_database_instance
from utils.osm_credentials import get_osm_credentials
from models import stacks_models
from routes.stacks_route import router as stacks_route
from routes.oauth_route import router as oauth_route

app = FastAPI()
app.title = "OSM-Sandbox API User"
app.version = "0.1.0"

app = FastAPI()
stacks_models.Base.metadata.create_all(bind=engine)

client_id, client_secret, redirect_uri, osm_instance_url, osm_instance_scopes = (
    get_osm_credentials()
)


class CustomStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "public, max-age=86400"
        return response


static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", CustomStaticFiles(directory=static_path), name="static")

templates_path = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_path)


@app.get("/", tags=["Home"])
def home(request: Request):
    req_obj = {
        "request": request,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "osm_instance_url": osm_instance_url,
        "osm_instance_scopes": osm_instance_scopes,
    }
    return templates.TemplateResponse("index.html", req_obj)


# Routes
app.include_router(stacks_route)
app.include_router(oauth_route)
