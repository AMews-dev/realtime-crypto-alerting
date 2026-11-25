
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import alerts
from api.routes import auth
from api.routes import bots
from api.ws.router import router as ws_router
from botpackage.manager import BotManager
from repositories.bot_repository import BotRepository
from contextlib import asynccontextmanager
import sys
from database import check_db_connection, SessionLocal, engine, Base
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from utils.limiter import Limiter
import logging

import asyncio
from api.ws.connection_manager import ConnectionManager
from api.ws.queue_broadcaster import QueueBroadcaster

logger = logging.getLogger(__name__)


def seed_initial_bot() -> None:
    """Legt bei leerer DB einen Standard-Bot an (ohne ihn doppelt zu starten)."""
    with SessionLocal() as db:
        repo = BotRepository(db)
        if not repo.get_all():
            created = repo.create_bot("BTC")
            logger.info("Standard-Bot %s (ID=%s) angelegt.", created.symbol, created.id)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Datenbank-Verbindung prüfen
    if not check_db_connection():
        logger.error("Server-Start abgebrochen: Datenbank nicht erreichbar.")
        sys.exit(1)

    notification_queue: asyncio.Queue = asyncio.Queue()
    connection_manager = ConnectionManager()
    broadcaster = QueueBroadcaster(notification_queue, connection_manager)
    manager = BotManager(notification_queue=notification_queue)

    app.state.notification_queue = notification_queue
    app.state.connection_manager = connection_manager
    app.state.bot_manager = manager

    Base.metadata.create_all(bind=engine)
    seed_initial_bot()

    broadcaster_task = asyncio.create_task(broadcaster.run(), name="queue-broadcaster")
    await manager.restore_active_bots()

    try:
        yield
    finally:
        logger.info("Server wird heruntergefahren...")
        # await manager.stop_all_bots()
        broadcaster_task.cancel()
        try:
            await broadcaster_task
        except asyncio.CancelledError:
            pass


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
origins = [
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(alerts.router)
app.include_router(auth.router)
app.include_router(bots.router)
app.include_router(ws_router)

if __name__ == "__main__":
    uvicorn.run("server:app", host="localhost", port=8000, reload=True)
