import asyncio
import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)
        logger.info("Client verbunden. Aktive Frontends: %d", len(self._connections))

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)
        logger.info("Client getrennt. Aktive Frontends: %d", len(self._connections))

    async def broadcast(self, message: dict) -> None:
        if not self._connections:
            return

        async def _send(ws: WebSocket) -> None:
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(ws)

        await asyncio.gather(*(_send(ws) for ws in list(self._connections)))