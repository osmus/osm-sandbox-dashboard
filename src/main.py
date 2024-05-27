import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from requests_oauthlib import OAuth2Session
# from .utils.database_utils import check_database_instance

app = FastAPI()
app.title = "OSM-Sandbox API User"
app.version = "0.1.0"

client_id = os.getenv("OSM_CLIENT_ID")
client_secret = os.getenv("OSM_CLIENT_SECRET")
redirect_uri = os.getenv("REDIRECT_URI")
osm_instance_url = os.getenv("OSM_INSTANCE_URL")
osm_instance_scopes = "read_prefs"

oauth = OAuth2Session(
    client_id=client_id, redirect_uri=redirect_uri, scope=osm_instance_scopes
)

static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

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

@app.get("/oauth_authorization", tags=["api"])
async def get_user_info(code: str):
    try:
        token = oauth.fetch_token(
            f"{osm_instance_url}/oauth2/token", code=code, client_secret=client_secret
        )
        oauth.token = token
        user_details_response = oauth.get(
            f"{osm_instance_url}/api/0.6/user/details.json"
        )
        user_details = user_details_response.json()
        return JSONResponse(content=user_details)
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=400)

# @app.get("/instances/{instance_name}", tags=["api"])
# async def get_instance_status(instance_name: str):
#     print(instance_name)
#     status = check_database_instance(instance_name)
#     return {"instance_name": instance_name, "status": status}
