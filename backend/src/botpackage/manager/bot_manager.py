import asyncio

from sqlalchemy.orm import Session
from starlette.websockets import WebSocket

from repositories.bot_repository import BotRepository, BotInfoResponse
from shared.allschemas import BotCreateSchema
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
        # self.load_bots()

    # async def connect_frontend(self, websocket: WebSocket):
    #     await websocket.accept()
    #     self.frontend_connections.append(websocket)
    #     logging.info(f"Client verbunden. Altive frontends: {len(self.frontend_connections)}")
    #
    # def disconnect_frontend(self, websocket: WebSocket):
    #     if websocket in self.frontend_connections:
    #         self.frontend_connections.remove(websocket)
    #         logging.info(f"🔴 Client getrennt. Aktive Frontends: {len(self.frontend_connections)}")
    #
    # async def broadcast_to_frontends(self, message:dict):
    #     for connection in list(self.frontend_connections):
    #         try:
    #             await connection.send_json(message)
    #         except Exception:
    #             self.disconnect_frontend(connection)
    # async def listen_to_queue(self):
    #     """
    #             🚀 DAS GEGENSTÜCK ZUM BOT:
    #             Liest permanent Events aus der notification_queue und leitet sie an das Frontend weiter.
    #             """
    #     logging.info("📡 Queue-Listener gestartet...")
    #     while True:
    #         try:
    #             # Wartet auf das Paket vom Bot
    #             event = await self.notification_queue.get()
    #
    #             # Leitet PRICE_UPDATE oder ALARM_TRIGGERED an die Browser weiter
    #             await self.broadcast_to_frontends(event)
    #
    #             self.notification_queue.task_done()
    #         except Exception as e:
    #             logging.error(f"Fehler im Queue-Listener: {e}")
    #
    #
    # def create_bot(self, data_schema, db):
    #     now = datetime.now()
    #     db_bot = BotModel(
    #         symbol=data_schema.symbol.upper(),
    #         is_running=False,
    #         createdAt=now
    #     )
    #     db.add(db_bot)
    #     db.commit()
    #     db.refresh(db_bot)
    #     return db_bot

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
            raise  ValueError("did not found bot")
        if symbol in self.active_bots:
            try:
                await self.stop_bot(symbol)
            except Exception as e:
                logging.warning(f"Konnte laufenden Bot-Task für {symbol} nicht sauber stoppen: {e}")

        db.delete(db_bot)
        db.commit()
        logging.info(f"Bot {symbol} erfolgreich aus Datenbank und RAM gelöscht.")

    def get_all_bots(self, db):
        bots = db.query(BotModel).all()
        return bots

    def get_all__active_bots(self, db):
        bots = db.query(BotModel).filter(BotModel.is_running).all()
        return bots

    def getBot(self, bot_id):

        return self.bots[bot_id]

    async def restore_active_bots(self, db):
        logging.info("Starte Wiederherstellung der aktiven Bots aus der Datenbank...")
        print("Lade aktive Bots aus der DB...")

        bots = db.query(BotModel).filter(BotModel.is_running).all()
        if not bots:
            logging.info("Keine aktiven Bots zum Wiederherstellen gefunden.")
            return
        print(f"Gefunden: {len(bots)} Bots werden nacheinander gestartet.")

        for db_bot in bots:
            try:
                await self.start_bot(db_bot.id, db=db)

                await asyncio.sleep(1)
            except Exception as e:
                logging.error(f"Fehler beim Wiederherstellen von Bot {db_bot.id}: {e}")

    async def reload_bot_alerts(self, symbol: str):
        raw_symbol = symbol.upper().replace("USDT", "").strip()
        full_symbol = f"{raw_symbol}USDT"

        # Key im Dictionary finden
        bot_key = full_symbol if full_symbol in self.active_bots else raw_symbol

        if bot_key in self.active_bots:
            bot = self.active_bots[bot_key]

            # Frische Session öffnen -> Daten laden -> Session schließen
            db = SessionLocal()
            try:
                db.expire_all()  # Zwingt SQLAlchemy, die Daten echt aus der Postgres/SQLite DB zu holen
                await bot.load_alerts(db)
                print(f"🔄 RAM-Cache für Bot '{bot_key}' erfolgreich aktualisiert!")
            finally:
                db.close()
        else:
            # Falls für den Coin noch gar kein Bot lief -> Jetzt starten!
            #await self.start_bot_for_symbol(full_symbol)
            print("bot night da")


if __name__ == "__main__":
    # Testcode nur beim direkten Aufruf
    data1 = {
        "id": 1,
        "symbol": "XRP",
        "threshold": 1.5
    }
