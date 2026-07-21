"""Custom ASGI middleware for security headers and OPTIONS preflight handling."""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response


def _is_mobile_webview_origin(origin: str) -> bool:
    """Allow common mobile/Tauri/Capacitor local origins and file/null origins."""
    if not origin or origin == "null":
        return True
    low = origin.lower()
    return (
        low.startswith("http://localhost")
        or low.startswith("https://localhost")
        or low.startswith("http://127.0.0.1")
        or low.startswith("https://127.0.0.1")
        or "tauri" in low
        or low.startswith("capacitor://")
        or low.startswith("ionic://")
        or low.startswith("file://")
    )


class OptionsCorsMiddleware(BaseHTTPMiddleware):
    """Handle CORS for web browsers and mobile/Tauri webviews."""

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin", "")
        allowed_origin = origin if (
            origin in settings.cors_origins_list or _is_mobile_webview_origin(origin)
        ) else (
            settings.cors_origins_list[0] if settings.cors_origins_list else "*"
        )

        if request.method == "OPTIONS":
            response = Response(status_code=200)
            response.headers["Access-Control-Allow-Origin"] = allowed_origin
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Max-Age"] = "86400"
            response.headers["Vary"] = "Origin"
            return response

        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = allowed_origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Vary"] = "Origin"
        return response
