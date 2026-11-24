import asyncio
import logging
from api.ws.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


class QueueBroadcaster:
    def __init__(self, queue: asyncio.Queue, connection_manager: ConnectionManager) -> None:
        self._queue = queue
        self._connection_manager = connection_manager

    async def run(self) -> None:
        logger.info("Queue-Listener gestartet...")
        while True:
            event = await self._queue.get()
            try:
                await self._connection_manager.broadcast(event)
            except Exception as exc:
                logger.error("Fehler im Queue-Listener: %s", exc)
            finally:
                self._queue.task_done()