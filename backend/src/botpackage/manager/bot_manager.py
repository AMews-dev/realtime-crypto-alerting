import asyncio

from sqlalchemy.orm import Session

from shared.allschemas import BotCreateSchema
from ..bots.bot import Bot
import logging
import json
from pathlib import Path
from shared.bot_model import BotModel
from ..handlers.handler import BaseHandler
from datetime import datetime
from database import SessionLocal

ws_url = "wss://stream.binance.com:9443/ws"
completeUrl = "wss://stream.binance.com:9443/ws/btcusdt@trade"


class BotManager:
    def __init__(self, db_session, notification_queue):
        self.db_session = db_session
        self.notification_queue = notification_queue
        self.active_bots: dict[str, Bot] = {}
        # self.load_bots()

    def create_bot(self, data_schema, db):
        now = datetime.now()
        db_bot = BotModel(
            symbol=data_schema.symbol.upper(),
            is_running=False,
            createdAt=now
        )
        db.add(db_bot)
        db.commit()
        db.refresh(db_bot)
        return db_bot

    async def start_bot(self, bot_id: int, db: Session):
        db_bot = db.query(BotModel).filter(BotModel.id == bot_id).first()
        if not db_bot:
            return {"status": "bot not found"}

        symbol = db_bot.symbol.upper()
        if symbol in self.active_bots:
            return {"status": "ok", "msg": f"Bot für {symbol} läuft bereits."}
        newBot = Bot.create_new_bot(db_bot, db_session=self.db_session, notification_queue=self.notification_queue)

        self.active_bots[symbol] = newBot
        newBot.running = True
        newBot.task = asyncio.create_task(newBot.run())

        db_bot.is_running = True
        db.commit()

        return {"status": "ok", "msg": f"Bot {bot_id} erfolgreich gestartet"}

    async def stop_bot(self, symbol: str):

        symbol = symbol.upper()

        # 1. ERST prüfen, ob der Bot existiert!
        if symbol not in self.active_bots:
            raise ValueError(f"Bot für '{symbol}' existiert nicht in den aktiven Bots.")

        # 2. ERST DANACH sicher aus dem Dictionary ziehen
        current_bot = self.active_bots[symbol]

        if not current_bot.running:
            print(f"Bot {symbol} läuft bereits nicht.")
            return

        # 3. Bot sauber beenden
        current_bot.running = False

        if current_bot.task:
            current_bot.task.cancel()  # Task im Hintergrund abschießen

        del self.active_bots[symbol]  # Aus dem RAM löschen
        print(f"[RAM] Bot für '{symbol}' erfolgreich entfernt.")

    def update_bot(self):
        pass

    def delete_bot(self):
        pass

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
    data_obj = BotCreate(**data1)
    print(data_obj)
    bot = Bot(data_obj)
    print(bot)
    print("Test erfolgreich:", Bot)
