from __future__ import annotations

import hashlib
import hmac

from fastapi import Request

from api.errors import ApiException
from api.settings import get_settings

COOKIE_NAME = "admin_session"


def _expected_token() -> str:
    settings = get_settings()
    payload = f"{settings.admin_password}:{settings.session_secret}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def issue_token() -> str:
    return _expected_token()


def verify_token(token: str | None) -> bool:
    if not token:
        return False
    return hmac.compare_digest(token, _expected_token())


def require_admin(request: Request) -> None:
    token = request.cookies.get(COOKIE_NAME)
    if not verify_token(token):
        raise ApiException(
            status_code=401,
            code="UNAUTHORIZED",
            message="Sesion admin no valida.",
            details={},
        )
