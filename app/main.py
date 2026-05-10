from fastapi import FastAPI, Form, BackgroundTasks, Cookie, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app import auth, runner

app = FastAPI(docs_url=None, redoc_url=None)
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def _redirect_login() -> RedirectResponse:
    return RedirectResponse(url="/login", status_code=303)


# ── Pages ──────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, session: str | None = Cookie(default=None)):
    if not auth.verify_session(session):
        return _redirect_login()
    return templates.TemplateResponse("index.html", {"request": request, "page": "main"})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, session: str | None = Cookie(default=None)):
    if auth.verify_session(session):
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("index.html", {"request": request, "page": "login", "error": None})


@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, password: str = Form(...)):
    if auth.check_password(password):
        token = auth.create_session_token()
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key="session",
            value=token,
            httponly=True,
            samesite="lax",
            max_age=60 * 60 * 24,
        )
        return response
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "page": "login", "error": "비밀번호가 올바르지 않습니다."},
        status_code=401,
    )


@app.post("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session")
    return response


# ── API ────────────────────────────────────────────────────────────────────

@app.post("/api/sync")
async def trigger_sync(background_tasks: BackgroundTasks, session: str | None = Cookie(default=None)):
    if not auth.verify_session(session):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    status = await runner.get_status()
    if status["is_syncing"]:
        return JSONResponse({"message": "이미 동기화가 진행 중입니다."}, status_code=409)

    background_tasks.add_task(runner.run_sync)
    return JSONResponse({"message": "동기화를 시작합니다."}, status_code=202)


@app.get("/api/status")
async def get_status(session: str | None = Cookie(default=None)):
    if not auth.verify_session(session):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    status = await runner.get_status()
    return JSONResponse(status)
