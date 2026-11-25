import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.ws.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])

def get_connection_manager(websocket: WebSocket) -> ConnectionManager:
    return websocket.app.state.connection_manager


@router.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket) -> None:
    manager = get_connection_manager(websocket)
    await manager.connect(websocket)
    try:
        while True:
            # Hält die Verbindung offen (z. B. Ping/Pong oder Client-Nachrichten)
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("Client hat WebSocket sauber geschlossen.")
    except Exception as exc:
        logger.warning("Unerwarteter Fehler auf WebSocket-Verbindung: %s", exc)
    finally:
        manager.disconnect(websocket)
