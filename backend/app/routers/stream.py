from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.core.dependencies import get_session
from app.services.article_service import get_article
from app.services.stream_service import stream_manager

router = APIRouter(tags=["stream"])


@router.get("/articles/{article_id}/stream")
async def article_stream(article_id: UUID, db: AsyncSession = Depends(get_session)):
    article = await get_article(db, article_id)
    if not article:
        return EventSourceResponse(stream_manager.event_generator(article_id))

    async def event_generator_wrapper():
        queue = stream_manager.get_queue(article_id)
        import asyncio, json
        try:
            while True:
                event = await asyncio.wait_for(queue.get(), timeout=600)
                yield {"event": event["event"], "data": json.dumps(event["data"])}
        except asyncio.TimeoutError:
            yield {"event": "timeout", "data": json.dumps({"message": "stream timeout"})}

    return EventSourceResponse(event_generator_wrapper())
