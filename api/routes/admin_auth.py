from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Response

from api.errors import ApiException
from api.schemas import AdminLoginRequestSchema, AdminLoginResponseSchema
from api.services.auth_service import COOKIE_NAME, issue_token
from api.settings import get_settings

router = APIRouter(prefix="/api/admin", tags=["admin-auth"])


@router.post("/login", response_model=AdminLoginResponseSchema)
def admin_login(payload: AdminLoginRequestSchema, response: Response):
    settings = get_settings()
    if payload.password != settings.admin_password:
        raise ApiException(
            status_code=401,
            code="UNAUTHORIZED",
            message="Credenciales invalidas.",
            details={},
        )

    expires = datetime.now(UTC) + timedelta(hours=12)
    response.set_cookie(
        key=COOKIE_NAME,
        value=issue_token(),
        httponly=True,
        samesite="lax",
        secure=False,
        expires=expires,
    )
    return {"ok": True}


@router.post("/logout", response_model=AdminLoginResponseSchema)
def admin_logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}
