import asyncio
import json
from uuid import UUID


class StreamManager:
    def __init__(self):
        self._queues: dict[UUID, asyncio.Queue] = {}

    def get_queue(self, article_id: UUID) -> asyncio.Queue:
        if article_id not in self._queues:
            self._queues[article_id] = asyncio.Queue()
        return self._queues[article_id]

    async def send(self, article_id: UUID, event: str, data: dict) -> None:
        queue = self.get_queue(article_id)
        await queue.put({"event": event, "data": data})

    async def send_status(self, article_id: UUID, status: str) -> None:
        await self.send(article_id, "status", {"status": status})

    async def send_progress(self, article_id: UUID, progress: dict) -> None:
        await self.send(article_id, "progress", progress)

    async def send_error(self, article_id: UUID, message: str) -> None:
        await self.send(article_id, "error", {"message": message})

    async def send_done(self, article_id: UUID) -> None:
        await self.send(article_id, "done", {"status": "done"})
        await self.close_queue(article_id)

    async def event_generator(self, article_id: UUID):
        queue = self.get_queue(article_id)
        try:
            while True:
                event = await asyncio.wait_for(queue.get(), timeout=30)
                yield f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"
        except asyncio.TimeoutError:
            yield f"event: timeout\ndata: {json.dumps({'message': 'stream timeout'})}\n\n"

    def close_queue(self, article_id: UUID) -> None:
        if article_id in self._queues:
            del self._queues[article_id]


stream_manager = StreamManager()
