import os
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import Cookie, HTTPException
from fastapi.responses import RedirectResponse

_SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")
_PASSWORD = os.environ.get("SERVER_PASSWORD", "")
_COOKIE_NAME = "session"
_SESSION_MAX_AGE = 60 * 60 * 24  # 24 hours

_serializer = URLSafeTimedSerializer(_SECRET_KEY)


def check_password(password: str) -> bool:
    return _PASSWORD and password == _PASSWORD


def create_session_token() -> str:
    return _serializer.dumps("authenticated")


def verify_session(session: str | None = Cookie(default=None, alias=_COOKIE_NAME)) -> bool:
    if not session:
        return False
    try:
        _serializer.loads(session, max_age=_SESSION_MAX_AGE)
        return True
    except (BadSignature, SignatureExpired):
        return False


def require_auth(session: str | None = Cookie(default=None, alias=_COOKIE_NAME)) -> str:
    if not verify_session(session):
        raise HTTPException(status_code=302, headers={"Location": "/login"})
    return session
