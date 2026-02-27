from __future__ import annotations

import hashlib
import re

from fastapi import Request

from api.settings import get_settings


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def hash_ip(ip: str) -> str:
    settings = get_settings()
    payload = f"{settings.ip_hash_salt}:{ip}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _normalize_phone(value: str) -> str:
    digits = re.sub(r"\D+", "", value or "")
    if digits:
        return digits
    return (value or "").strip()


def hash_phone(phone: str) -> str:
    settings = get_settings()
    normalized = _normalize_phone(phone)
    payload = f"{settings.phone_hash_salt}:{normalized}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def request_ip_hash(request: Request) -> str:
    return hash_ip(get_client_ip(request))
