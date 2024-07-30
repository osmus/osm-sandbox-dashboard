import uuid
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.openapi.models import SecuritySchemeType, SecurityScheme
from database import engine
from models import boxes, sessions, resources, users
from routes.boxes_routes import router as boxes_routes
from routes.login_routes import router as login_routes
from routes.resources_routes import router as resources_routes
from routes.auth_routes import router as auth_routes
from routes.html_routes import router as html_router

app = FastAPI()
app.title = "OSM-Sandbox API"
app.version = "0.1.0"

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
boxes.Base.metadata.create_all(bind=engine)
sessions.Base.metadata.create_all(bind=engine)
resources.Base.metadata.create_all(bind=engine)
users.Base.metadata.create_all(bind=engine)

# Define the OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/login")


# Home route
@app.get("/", tags=["Home"])
def home(request: Request):
    response = {
        "status": "ok",
    }
    return JSONResponse(content=response)


# Include routes
app.include_router(auth_routes, prefix="/v1")
app.include_router(resources_routes, prefix="/v1")
app.include_router(boxes_routes, prefix="/v1")
app.include_router(login_routes, prefix="/v1")
app.include_router(html_router)

# Run the app
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
