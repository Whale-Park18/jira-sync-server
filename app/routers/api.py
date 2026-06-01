import asyncio

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.auth import is_authenticated
from app.runner import sync_runner

router = APIRouter(prefix="/api")


def _check_auth(request: Request) -> None:
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")


@router.post("/sync", status_code=202)
async def trigger_sync(request: Request):
    _check_auth(request)
    if sync_runner.is_running():
        raise HTTPException(status_code=409, detail="이미 동기화가 진행 중입니다.")
    asyncio.create_task(sync_runner.run_sync())
    return {"status": "started"}


@router.get("/status")
async def get_status(request: Request):
    _check_auth(request)
    return JSONResponse(sync_runner.get_status())
