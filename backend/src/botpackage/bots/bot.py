import asyncio
import logging
import json
import websockets

from ..alarm_evaluator import evaluate_alarm_condition
from database import SessionLocal
from shared.models.price_alarm_model import PriceAlarm

from datetime import datetime, timezone


class Bot:
    def __init__(self, db_bot, notification_queue) -> None:

        self.id = db_bot.id
        self.symbol = db_bot.symbol.upper()
        self.notification_queue = notification_queue
        self.running = False

        base, _, quote = self.symbol.partition("/")
        quote_asset = (quote or "USDT").lower()
        self.stream_url = f"wss://stream.binance.com:9443/ws/{base.lower()}{quote_asset}@ticker"

        self.cached_alerts = []
        self.task: asyncio.Task | None = None

    async def load_alerts(self) -> None:
        """Lädt alle aktiven, noch nicht ausgelösten Alarme für das Symbol in den RAM."""
        base, _, quote = self.symbol.partition("/")
        quote_asset = quote or "USDT"
        compact_pair = f"{base}{quote_asset}"

        with SessionLocal() as db:
            alarms = (
                db.query(PriceAlarm)
                .filter(
                    PriceAlarm.coin_symbol.in_([base, compact_pair, self.symbol]),
                    PriceAlarm.is_active.is_(True),
                    PriceAlarm.is_triggered.is_(False),
                )
                .all()
            )
            db.expunge_all()
            self.cached_alerts = alarms

        logging.info("[%s] %s Alarme geladen für %s", self.id, len(self.cached_alerts), self.symbol)

    def __repr__(self):
        return f"Bot(id={self.id}, symbol='{self.symbol}', running={self.running}, stream={self.stream_url})"

    async def run(self):
        self.running = True

        print(f"[{self.id}] Bot läuft...")
        print(self.running)

        logging.info(f"[{self.id}] Starting Bot")
        await self.load_alerts()
        try:
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
                            change_24h = float(data.get("P", 0.0))
                            #change_24h = float(data['P'])
                            pair = data['s']
                            # Preissignal an Frontend weiterleiten
                            if self.notification_queue:
                                await self.notification_queue.put({
                                    "type": "PRICE_UPDATE",
                                    "symbol": self.symbol,
                                    "pair": pair,
                                    "price": current_price,
                                    "change24h": change_24h
                                })

                            triggered = [
                                alarm
                                for alarm in list(self.cached_alerts)
                                if evaluate_alarm_condition(alarm, current_price)
                            ]

                            if triggered:
                                await self._handle_triggered_alerts(triggered, current_price)

                except asyncio.CancelledError:
                    logging.info("[%s] Task für %s gecancelt.", self.id, self.symbol)
                    raise
                except Exception as e:
                    logging.error("[%s] Fehler im WebSocket %s: %s", self.id, self.symbol, e)
                    print(f"Fehler im WebSocket {self.symbol}: {e}")
                    await asyncio.sleep(5)

        finally:
            self.running = False
            logging.info("[%s] Bot für %s gestoppt.", self.id, self.symbol)

    #
    # async def stop(self) -> None:
    #     logging.info(f"[{self.id}] Stopping bot")
    #     self.running = False
    #     if self.task is not None and not self.task.done():
    #         self.task.cancel()

    async def _handle_triggered_alerts(self, triggered, current_price: float):
        if not triggered:
            return

        triggered_ids = [alarm.id for alarm in triggered]
        triggered_set = set(triggered_ids)

        with SessionLocal() as db:
            try:
                db.query(PriceAlarm).filter(PriceAlarm.id.in_(triggered_ids)).update(
                    {
                        PriceAlarm.is_triggered: True,
                        PriceAlarm.is_active: False,
                        PriceAlarm.last_triggered_at: datetime.now(timezone.utc),
                    },
                    synchronize_session=False,
                )
                db.commit()
            except Exception as e:
                db.rollback()
                logging.error("[%s] Fehler beim Speichern ausgelöster Alarme: %s", self.id, e)
                return

        # Aus dem RAM-Cache entfernen, damit derselbe Alarm nicht erneut feuert
        self.cached_alerts = [a for a in self.cached_alerts if a.id not in triggered_set]

        for alarm in triggered:
            payload = {
                "type": "ALARM_TRIGGERED",
                "alarm_id": alarm.id,
                "user_id": alarm.user_id,
                "symbol": self.symbol,
                "triggered_price": current_price,
            }
            if self.notification_queue is not None:
                await self.notification_queue.put(payload)

            logging.info("🚨 ALARM AUSGELÖST [ID: %s] %s bei %s", alarm.id, self.symbol, current_price)


if __name__ == "__main__":
    # Testcode nur beim direkten Aufruf
    # from ..models.bot_model import Bot, BotCreate
    data1 = {
        "id": 1,
        "symbol": "XRP",
        "threshold": 1.5
    }
