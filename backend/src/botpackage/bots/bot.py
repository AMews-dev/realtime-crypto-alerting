import asyncio
import logging
import json
import websockets
from sqlalchemy import Null

from shared.price_alarm_model import PriceAlarm


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

    @classmethod
    def from_state(cls, state: dict):
        return cls(
            id=state["id"],
            symbol=state["symbol"],
            threshold=state["threshold"],
            running=state["running"]
        )

    async def load_alerts(self, db):
        alarms = db.query(PriceAlarm).filter(PriceAlarm.symbol == self.symbol, PriceAlarm.is_triggered == False).all()
        self.cached_alerts = [
            {
                "id": a.id,
                "activation_price": a.activation_price,
                "target_price": a.target_price,
                "target_percentage": a.target_percentage,
                "direction": a.direction.upper(),  # "UP" oder "DOWN"
                "user_id": a.user_id
            } for a in alarms
        ]

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
        print(f"[{self.id}] Bot läuft...")
        print(self.running)
        logging.info(f"[{self.id}] Starting Bot")

        while self.running:
            try:
                async with websockets.connect(self.stream_url) as ws:
                    logging.info(f"[{self.id}] Connected to {self.stream_url}")
                    print(f"[{self.id}] Verbunden mit {self.stream_url}")

                    while self.running:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        current_price = float(data['c'])  # Aktueller Preis von Binance

                        triggered = []

                        for alarm in self.cached_alerts:
                            # -----------------------------------------------------------
                            # FALL 1: Absoluter Preis-Alarm (target_price ist gesetzt)
                            # -----------------------------------------------------------
                            if alarm["target_price"] is not None:
                                if alarm["direction"] == "UP" and current_price >= alarm["target_price"]:
                                    triggered.append(alarm)
                                elif alarm["direction"] == "DOWN" and current_price <= alarm["target_price"]:
                                    triggered.append(alarm)

                            # -----------------------------------------------------------
                            # FALL 2: Prozentualer Alarm (Prozent + Aktivierungspreis)
                            # -----------------------------------------------------------
                            elif alarm["target_percentage"] is not None and alarm["activation_price"] is not None:
                                # Berechne, wie viel Prozent sich der Preis seit der Aktivierung verändert hat
                                # Formel: ((Aktueller Preis - Startpreis) / Startpreis) * 100
                                price_change_pct = ((current_price - alarm["activation_price"]) / alarm[
                                    "activation_price"]) * 100

                                if alarm["direction"] == "UP" and price_change_pct >= alarm["target_percentage"]:
                                    triggered.append(alarm)
                                elif alarm["direction"] == "DOWN" and price_change_pct <= -alarm["target_percentage"]:
                                    # Hinweis: Bei "DOWN" fällt der Preis, die Änderung wird negativ (z.B. -5%)
                                    triggered.append(alarm)

                            # Wenn Alarme ausgelöst wurden, verarbeiten (DB Update + Notification Queue)
                        if triggered:
                            await self._handle_triggered_alerts(triggered)


            except asyncio.CancelledError:

                print(f"👋 Task für {self.symbol} gecancelt. Schließe Verbindung sofort.")

                break  #
            except Exception as e:
                print(f"Fehler: {e}")
                await asyncio.sleep(5)

    async def stop(self):
        logging.info(f"[{self.id}] Stopping bot")
        self.running = False
        if self.task:
            self.task.cancel()

    async def _handle_triggered_alerts(self, triggered):
        return Null


if __name__ == "__main__":
    # Testcode nur beim direkten Aufruf
    # from ..models.bot_model import Bot, BotCreate
    data1 = {
        "id": 1,
        "symbol": "XRP",
        "threshold": 1.5
    }
