from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import check_password, delete_session_cookie, is_authenticated, sign_session_cookie
from app.runner import sync_runner

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "status": sync_runner.get_status()},
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = ""):
    if is_authenticated(request):
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": error},
    )


@router.post("/login")
async def login(request: Request, password: str = Form(...)):
    if not check_password(password):
        return RedirectResponse(url="/login?error=1", status_code=303)
    response = RedirectResponse(url="/", status_code=303)
    sign_session_cookie(response)
    return response


@router.post("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=303)
    delete_session_cookie(response)
    return response
