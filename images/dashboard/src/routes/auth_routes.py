# routes/auth_routes.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi_login import LoginManager
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse, JSONResponse
import httpx
import os

from dependencies import get_db, get_current_user, get_admin_user, get_creator_user
from models.users import User, UserRole
from database import Base, engine

router = APIRouter()

# Initialize the database
Base.metadata.create_all(bind=engine)

# OSM OAuth configuration
OSM_CLIENT_ID = os.getenv("DASHBOARD_OSM_CLIENT_ID")
OSM_CLIENT_SECRET = os.getenv("DASHBOARD_OSM_CLIENT_SECRET")
OSM_CALLBACK_URL = os.getenv("DASHBOARD_OSM_CALLBACK_URL")

# FastAPI-Login configuration
SECRET = "your_secret_key"
manager = LoginManager(SECRET, token_url="/auth/token")


@manager.user_loader()
def load_user(username: str, db: Session = Depends(get_db)):
    return db.query(User).filter(User.username == username).first()


# Redirection route for OSM login
@router.get("/auth/osm")
async def osm_login():
    osm_auth_url = f"https://www.openstreetmap.org/oauth2/authorize?client_id={OSM_CLIENT_ID}&redirect_uri={OSM_CALLBACK_URL}&response_type=code&scope=read_prefs"
    return RedirectResponse(url=osm_auth_url)


# Callback URL to receive the authorization code
@router.get("/auth/callback")
async def osm_callback(code: str, db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://www.openstreetmap.org/oauth2/token",
            data={
                "client_id": OSM_CLIENT_ID,
                "client_secret": OSM_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": OSM_CALLBACK_URL,
            },
        )
        token_response.raise_for_status()
        token_data = token_response.json()
        access_token = token_data.get("access_token")

        user_response = await client.get(
            "https://api.openstreetmap.org/api/0.6/user/details.json",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_response.raise_for_status()
        user_data = user_response.json()

        osm_id = user_data.get("user").get("id")
        username = user_data.get("user").get("display_name")

        # Check if the user exists in the database
        user = db.query(User).filter(User.osm_id == osm_id).first()

        # If the user doesn't exist, create a new user
        if not user:
            user = User(osm_id=osm_id, username=username)
            db.add(user)
            db.commit()
            db.refresh(user)

        # Create an access token for the user
        access_token = manager.create_access_token(data={"sub": username})

        # Redirect to the dashboard page with the token
        return RedirectResponse(url=f"/dashboard?access_token={access_token}")


# Protect endpoints with roles
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello, {current_user.username}"}


@router.get("/admin")
async def admin_route(current_user: User = Depends(get_admin_user)):
    return {"message": f"Hello, Admin {current_user.username}"}


@router.get("/creator")
async def creator_route(current_user: User = Depends(get_creator_user)):
    return {"message": f"Hello, Creator {current_user.username}"}
