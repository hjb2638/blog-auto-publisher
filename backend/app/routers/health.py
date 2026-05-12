import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_session
from app.schemas.article import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=dict)
async def health_check(session: AsyncSession = Depends(get_session)):
    db_status = "connected"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    llm_status = "unreachable"
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{settings.llm_base_url}/models")
            llm_status = "reachable" if r.status_code == 200 else "unreachable"
    except Exception:
        pass

    wp_status = "unreachable"
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{settings.wp_api_url}/wp/v2/posts?per_page=1")
            wp_status = "reachable" if r.status_code == 200 else "unreachable"
    except Exception:
        pass

    overall = "healthy" if all(s == "connected" or s == "reachable" for s in [db_status, llm_status, wp_status]) else "degraded"

    return {
        "success": True,
        "data": {
            "status": overall,
            "database": db_status,
            "llm_service": llm_status,
            "wordpress": wp_status,
        },
    }
