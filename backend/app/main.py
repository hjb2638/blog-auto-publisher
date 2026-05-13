from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AppException
from app.routers import articles, health, stream, wordpress

app = FastAPI(title="Blog Publisher", version="0.1.0")

origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.exception_handler(AppException)
async def app_exception_handler(_request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.error,
            "detail": exc.detail,
            "field_errors": getattr(exc, "field_errors", None),
            "retryable": exc.retryable,
        },
    )


@app.get("/")
async def root():
    return {"message": "Blog Publisher API", "version": "0.1.0"}


app.include_router(health.router, prefix="/api/v1")
app.include_router(articles.router, prefix="/api/v1")
app.include_router(stream.router, prefix="/api/v1")
app.include_router(wordpress.router, prefix="/api/v1")
