import secrets

from fastapi import Request, Response
from itsdangerous import BadSignature, SignatureExpired, TimestampSigner

from app.config import settings


def _signer() -> TimestampSigner:
    return TimestampSigner(settings.secret_key)


def check_password(plain: str) -> bool:
    return secrets.compare_digest(plain, settings.server_password)


def sign_session_cookie(response: Response) -> None:
    token = _signer().sign("authenticated").decode()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.session_max_age,
    )


def delete_session_cookie(response: Response) -> None:
    response.delete_cookie(key=settings.session_cookie_name)


def is_authenticated(request: Request) -> bool:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return False
    try:
        _signer().unsign(token, max_age=settings.session_max_age)
        return True
    except (SignatureExpired, BadSignature):
        return False
