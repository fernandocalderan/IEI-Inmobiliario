from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    database_url: str
    cors_origins: list[str]
    use_db_zones: bool
    zone_cache_ttl_seconds: int
    engine_version: str

    admin_password: str
    session_secret: str

    ip_hash_salt: str
    phone_hash_salt: str

    dedupe_window_days: int
    feature_reservations: bool
    export_pii: bool

    rate_limit_per_minute: int
    rate_limit_leads_per_minute: int


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    db_url = os.getenv("DATABASE_URL") or os.getenv("DB_URL") or "postgresql+psycopg://postgres:postgres@localhost:5432/iei_mvp"
    return Settings(
        app_name=os.getenv("APP_NAME", "IEI Inmobiliario API"),
        app_env=os.getenv("APP_ENV", "dev"),
        database_url=db_url,
        cors_origins=_split_csv(os.getenv("CORS_ORIGINS", "*")),
        use_db_zones=_as_bool(os.getenv("USE_DB_ZONES", "true"), default=True),
        zone_cache_ttl_seconds=int(os.getenv("ZONE_CACHE_TTL_SECONDS", "300")),
        engine_version=os.getenv("ENGINE_VERSION", "iei_engine_mvp_v1"),
        admin_password=os.getenv("ADMIN_PASSWORD", "change-me"),
        session_secret=os.getenv("SESSION_SECRET", "change-me-too"),
        ip_hash_salt=os.getenv("IP_HASH_SALT", "iei-ip-salt"),
        phone_hash_salt=os.getenv("PHONE_HASH_SALT", "iei-phone-salt"),
        dedupe_window_days=int(os.getenv("DEDUPE_WINDOW_DAYS", "30")),
        feature_reservations=_as_bool(os.getenv("FEATURE_RESERVATIONS", "true"), default=True),
        export_pii=_as_bool(os.getenv("EXPORT_PII", "false"), default=False),
        rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "120")),
        rate_limit_leads_per_minute=int(os.getenv("RATE_LIMIT_LEADS_PER_MINUTE", "20")),
    )
