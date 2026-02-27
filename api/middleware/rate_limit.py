from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from api.settings import get_settings
from api.utils.ip_hash import request_ip_hash


class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    _lock = threading.Lock()
    _hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request, call_next):
        path = request.url.path

        # Endpoints administrativos y health fuera del rate limit MVP.
        if path.startswith("/api/admin") or path == "/health":
            return await call_next(request)

        settings = get_settings()
        ip_hash = request_ip_hash(request)

        limit = settings.rate_limit_per_minute
        session_id = request.headers.get("x-session-id", "").strip()
        if path == "/api/leads":
            limit = settings.rate_limit_leads_per_minute
            key = f"{ip_hash}:{session_id or 'no-session'}:{path}"
        else:
            key = f"{ip_hash}:{path}"

        window_start = time.time() - 60.0

        with self._lock:
            queue = self._hits[key]
            while queue and queue[0] < window_start:
                queue.popleft()

            if len(queue) >= limit:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "RATE_LIMITED",
                            "message": "Demasiadas solicitudes para este endpoint.",
                            "details": {"path": path},
                        }
                    },
                )

            queue.append(time.time())

        return await call_next(request)
