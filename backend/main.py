"""Hermes Agent — 项目智能管家 API."""
import os
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException, RequestValidationError
from database import init_db
from routers import projects, tasks, capabilities, webhooks, audit_logs


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Hermes Agent API",
    description="项目智能管家 — AI Agent 驱动的项目管理与能力沉淀平台",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Register routers
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(capabilities.router)
app.include_router(webhooks.router)
app.include_router(audit_logs.router)


# ─── Unified Response Middleware ─────────────

@app.middleware("http")
async def wrap_response(request: Request, call_next):
    response = await call_next(request)
    content_type = response.headers.get("content-type", "")
    if 200 <= response.status_code < 300 and "application/json" in content_type:
        try:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
        except Exception:
            return response
        try:
            data = json.loads(body)
            if not ("code" in data and "msg" in data):
                data = {"code": 200, "msg": "成功", "data": data}
            return Response(content=json.dumps(data, ensure_ascii=False, default=str), status_code=200, media_type="application/json")
        except (json.JSONDecodeError, Exception):
            return response
    return response


# ─── Exception Handlers ─────────────────────

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=200, content={"code": exc.status_code, "msg": exc.detail, "data": None})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=200, content={"code": 422, "msg": str(exc.errors()), "data": None})


# ─── Root Endpoints ─────────────────────────

@app.get("/")
async def root():
    return {"message": "Hermes Agent API", "version": "0.1.0", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}
