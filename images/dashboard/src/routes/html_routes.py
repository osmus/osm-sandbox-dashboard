from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/login_dashboard", response_class=HTMLResponse, tags=["Testing pages"])
async def login(request: Request):
    return templates.TemplateResponse("login_dashboard.html", {"request": request})
