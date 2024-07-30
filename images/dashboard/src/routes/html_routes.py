from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/login", response_class=HTMLResponse, tags=["Testing page"])
async def read_root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse, tags=["Testing page"])
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
