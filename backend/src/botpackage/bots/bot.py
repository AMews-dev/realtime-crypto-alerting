import asyncio
import logging
import json
import websockets
from sqlalchemy import Null, not_
from typing_inspection.typing_objects import is_self

from ..alarm_evaluator import evaluate_alarm_condition
from database import SessionLocal
from shared.models.price_alarm_model import PriceAlarm

from datetime import datetime, timezone
class Bot:
    def __init__(self, db_bot, db_session, notification_queue):

        self.id = db_bot.id
        self.symbol = db_bot.symbol
        self.db_session = db_session
        self.notification_queue = notification_queue
        self.running = False
        self.stream_url = f"wss://stream.binance.com:9443/ws/{self.symbol.lower()}usdt@ticker"
        # self.ws_url = ws_url
        self.cached_alerts = []
        self.task: asyncio.Task | None = None

    @classmethod
    def create_new_bot(cls, db_bot, db_session, notification_queue):
        return cls(db_bot, db_session, notification_queue)

    async def load_alerts(self):
        """Lädt alle aktiven Alarme für diesen Coin inkl. aller neuen Felder."""
        raw_symbol = self.symbol.upper().replace("USDT", "").strip()

        db = SessionLocal()
        try:
            alarms = db.query(PriceAlarm).filter(
                PriceAlarm.coin_symbol.in_([raw_symbol, f"{raw_symbol}USDT"]),
                PriceAlarm.is_active == True,  # bzw. PriceAlarm.is_active
                PriceAlarm.is_triggered == False  # bzw. not_(PriceAlarm.is_triggered)
            ).all()

            db.expunge_all()
            self.cached_alerts = alarms

            print(f"🧠 [RAM-CACHE OK] {self.symbol}: {len(self.cached_alerts)} Alarme geladen.")
            logging.info(f"[{self.id}] {len(self.cached_alerts)} Alarme geladen für {self.symbol}.")
        finally:
            db.close()
    @classmethod
    def from_state(cls, state: dict):
        return cls(
            id=state["id"],
            symbol=state["symbol"],
            threshold=state["threshold"],
            running=state["running"]
        )



    def to_dict(self):
        return {
            "id": self.id,
            "symbol": self.symbol,
            "threshold": self.threshold,
            "running": self.running,
            "handlers": self.handlers
        }

    def __repr__(self):
        return f"Bot(id={self.id}, symbol='{self.symbol}', running={self.running}, stream={self.stream_url})"

    async def run(self):
        self.running = True

        print(f"[{self.id}] Bot läuft...")
        print(self.running)

        logging.info(f"[{self.id}] Starting Bot")
        await self.load_alerts()

        while self.running:
            try:
                async with websockets.connect(self.stream_url) as ws:
                    logging.info(f"[{self.id}] Connected to {self.stream_url}")
                    print(f"[{self.id}] Verbunden mit {self.stream_url}")

                    async for msg in ws:
                        if not self.running:
                            break

                        data = json.loads(msg)
                        if 'c' not in data:
                            continue
                        current_price = float(data['c'])  # Aktueller Preis von Binance

                        # Preissignal an Frontend weiterleiten
                        if self.notification_queue:
                            await self.notification_queue.put({
                                "type": "PRICE_UPDATE",
                                "symbol": self.symbol,
                                "price": current_price
                            })

                        # ram-cache auf getriggerte alarme prüfen
                        triggered = []

                        # 3. Durch den RAM-Cache iterieren (Verwendung deiner neuen evaluate_alarm_condition Funktion)
                        for alarm in list(self.cached_alerts):
                            # Wenn cached_alerts Objekte sind:
                            if evaluate_alarm_condition(alarm, current_price):
                                triggered.append(alarm)

                        # 4. Wenn Alarme ausgelöst wurden
                        if triggered:
                            await self._handle_triggered_alerts(triggered, current_price)

            except asyncio.CancelledError:
                print(f"👋 Task für {self.symbol} gecancelt. Schließe Verbindung.")
                break
            except Exception as e:
                logging.error(f"[{self.id}] Fehler im WebSocket {self.symbol}: {e}")
                print(f"Fehler im WebSocket {self.symbol}: {e}")
                await asyncio.sleep(5)



    async def stop(self):
        logging.info(f"[{self.id}] Stopping bot")
        self.running = False
        if self.task:
            self.task.cancel()

    async def _handle_triggered_alerts(self, triggered, current_price:float):
        db = SessionLocal()
        try :
            # 1. DB-Status für alle getriggerten Alarme aktualisieren
            triggered_ids = [alarm.id for alarm in triggered]
            db.query(PriceAlarm).filter(PriceAlarm.id.in_(triggered_ids)).update(
                {
                    PriceAlarm.is_triggered: True,
                    PriceAlarm.is_active: False,
                    PriceAlarm.last_triggered_at: datetime.now(timezone.utc)
                },
                synchronize_session=False
            )
            db.commit()

            self.cached_alerts = [a for a in self.cached_alerts if a.id not in triggered_ids]
            for alarm in triggered:
                payload = {
                    "alarm_id": alarm.id,
                    "user_id": alarm.user_id,
                    "symbol": self.symbol,
                    "triggered_price": current_price
                }
                if self.notification_queue:
                    await self.notification_queue.put(payload)

                print(f"🚨 ALARM AUSGELÖST! [ID: {alarm.id}] {self.symbol} bei ${current_price}")

        except Exception as e:
            db.rollback()
            logging.error(f"Fehler beim Speichern ausgelöster Alarme: {e}")
        finally:
            db.close()


if __name__ == "__main__":
    # Testcode nur beim direkten Aufruf
    # from ..models.bot_model import Bot, BotCreate
    data1 = {
        "id": 1,
        "symbol": "XRP",
        "threshold": 1.5
    }
