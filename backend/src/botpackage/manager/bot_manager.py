import asyncio

from sqlalchemy.orm import Session

from shared.schemas import BotCreateSchema
from ..bots.bot import Bot
import logging
import json
from pathlib import Path
from shared.bot_model import BotModel
from ..handlers.handler import BaseHandler
from datetime import datetime

ws_url = "wss://stream.binance.com:9443/ws"
completeUrl = "wss://stream.binance.com:9443/ws/btcusdt@trade"


class BotManager:
    def __init__(self, db_session, notification_queue):
        self.db_session = db_session
        self.notification_queue = notification_queue
        self.active_bots: dict[str, Bot] = {}
        # self.load_bots()

    """"
    def create_bot(self, data: dict, db: Session):
        data_obj = BotCreate(**data)

        bot = Bot(data_obj)
        logging.info(f"Bot with id:[{data["id"]}] wurde erstellt")
        print(f"Bot mit Id: {data["id"]} wurde erstellt")
        db.add(bot)
        # self.bots[bot.id] = bot

        #data_dict = bot.to_dict()
        #self.save_bots(data_dict)

        return bot
    """

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
