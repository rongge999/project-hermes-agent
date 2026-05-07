"""Feishu auth middleware (MVP: dev bypass)."""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse


async def verify_feishu_token(request: Request, call_next):
    """Dev mode: skip real feishu auth."""
    # Skip auth for webhooks, health, docs
    path = request.url.path
    if path.startswith("/api/webhooks/") or path in ["/", "/health", "/docs", "/openapi.json"]:
        return await call_next(request)
    # Dev mode: accept any request
    return await call_next(request)
