from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    success: bool
    data: Any | None = None
    meta: dict | None = None
    error: str | None = None
    detail: str | None = None
    field_errors: dict | None = None
    retryable: bool = False


class PaginationMeta(BaseModel):
    total: int
    page: int
    limit: int
    pages: int
