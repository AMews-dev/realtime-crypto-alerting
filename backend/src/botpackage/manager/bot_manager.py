import asyncio

from sqlalchemy.orm import Session
from starlette.websockets import WebSocket

from repositories.bot_repository import BotRepository, BotInfoResponse
from shared.allschemas import BotCreateSchema
from utils.symbols import normalize_pair
from ..bots.bot import Bot
import logging
import json
from pathlib import Path
from shared.bot_model import BotModel
from ..handlers.handler import BaseHandler
from datetime import datetime
from database import SessionLocal
from exceptions.bot_exceptions import BotNotFoundError, BotRunningError

ws_url = "wss://stream.binance.com:9443/ws"
completeUrl = "wss://stream.binance.com:9443/ws/btcusdt@trade"


class BotManager:
    def __init__(self, notification_queue: asyncio.Queue):

        self.notification_queue = notification_queue
        self.active_bots: dict[str, Bot] = {}

    async def start_bot(self, bot_id: int) -> BotInfoResponse:
        with SessionLocal() as db:
            repo = BotRepository(db)
            bot_info = repo.get_by_id(bot_id)

            if bot_info is None:
                raise BotNotFoundError(str(bot_id))
            symbol = bot_info.symbol.upper()
            # test if bot already exist in ram
            existing_bot = self.active_bots.get(symbol)
            if (
                    existing_bot is not None
                    and existing_bot.task is not None
                    and not existing_bot.task.done()
            ):
                raise BotRunningError(symbol)

            #set db status running
            updated_bot = repo.set_running(bot_id, True)

            if updated_bot is None:
                raise BotNotFoundError(str(bot_id))
            db.commit()

        # create bot object and start asyncio task
        new_bot = Bot(
            db_bot=updated_bot,
            notification_queue=self.notification_queue,
        )
        self.active_bots[symbol] = new_bot
        new_bot.task = asyncio.create_task(new_bot.run())

        return updated_bot

    async def stop_bot(self, bot_id: int) -> BotInfoResponse:

        with SessionLocal() as db:
            repo = BotRepository(db)
            bot_info = repo.get_by_id(bot_id)

            if bot_info is None:
                raise BotNotFoundError(str(bot_id))

            symbol = bot_info.symbol.upper()
            active_bot = self.active_bots.pop(symbol, None)

        if active_bot is not None and active_bot.task is not None and not active_bot.task.done():
            active_bot.task.cancel()
            try:
                await active_bot.task
            except asyncio.CancelledError:
                pass

        with SessionLocal() as db:
            repo = BotRepository(db)
            updated_bot = repo.set_running(bot_id, False)

            if updated_bot is None:
                raise BotNotFoundError(str(bot_id))
            db.commit()
        return updated_bot

    def update_bot(self):
        pass

    async def delete_bot(self, symbol, db: Session):
        db_bot = db.query(BotModel).filter(BotModel.symbol == symbol).first()
        if not db_bot:
            raise ValueError("did not found bot")
        if symbol in self.active_bots:
            try:
                await self.stop_bot(symbol)
            except Exception as e:
                logging.warning(f"Konnte laufenden Bot-Task für {symbol} nicht sauber stoppen: {e}")

        db.delete(db_bot)
        db.commit()
        logging.info(f"Bot {symbol} erfolgreich aus Datenbank und RAM gelöscht.")

    async def restore_active_bots(self) -> None:
        logging.info("Starte Wiederherstellung der aktiven Bots aus der Datenbank...")
        print("Lade aktive Bots aus der DB...")

        with SessionLocal() as db:
            repo = BotRepository(db)
            running_bots = repo.get_active()  # z. B. gibt Liste von BotInfoResponse oder IDs zurück

        if not running_bots:
            logging.info("Keine aktiven Bots zum Wiederherstellen gefunden.")
            return

        logging.info("Gefunden: %s Bots werden nacheinander gestartet.", len(running_bots))

        for bot_item in running_bots:
            try:
                await self.start_bot(bot_item.id)
                await asyncio.sleep(1)
            except Exception as e:
                logging.error("Fehler beim Wiederherstellen von Bot %s: %s", bot_item.id, e)

    async def reload_bot_alerts(self, symbol: str) -> None:
        normalized_symbol = normalize_pair(symbol)

        bot = self.active_bots.get(normalized_symbol)

        if bot is None:
            logging.info("Kein aktiver Bot im RAM für %s gefunden.", normalized_symbol)
            return

        with SessionLocal() as db:
            db.expire_all()
            await bot.load_alerts(db)

        logging.info("RAM-Cache für Bot '%s' erfolgreich aktualisiert.", normalized_symbol)


if __name__ == "__main__":
    # Testcode nur beim direkten Aufruf
    data1 = {
        "id": 1,
        "symbol": "XRP",
        "threshold": 1.5
    }
