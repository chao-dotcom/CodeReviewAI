from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Awaitable, Callable
from uuid import UUID


@dataclass(frozen=True)
class ReviewJob:
    review_id: UUID
    diff_text: str


class ReviewQueue:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[ReviewJob] = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None

    async def start(self, handler: Callable[[ReviewJob], Awaitable[None]]) -> None:
        if self._worker_task is not None:
            return

        async def _run() -> None:
            while True:
                job = await self._queue.get()
                try:
                    await handler(job)
                finally:
                    self._queue.task_done()

        self._worker_task = asyncio.create_task(_run())

    async def enqueue(self, job: ReviewJob) -> None:
        await self._queue.put(job)
