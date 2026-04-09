"""
Centralised HTTP exception and validation error handlers.
Registered in main.py so all routes benefit automatically.
"""
 
from __future__ import annotations
 
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
 
from app.core.logging import get_logger
 
log = get_logger(__name__)
 
 
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    log.warning("HTTP %d – %s %s – %s", exc.status_code, request.method, request.url.path, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code},
    )
 
 
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    log.warning("Validation error on %s %s: %s", request.method, request.url.path, exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Validation failed", "details": exc.errors()},
    )
 
 
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"},
    )