from datetime import datetime, timezone
from typing import Callable, Optional
from collections import defaultdict
import time
from sqlalchemy import not_
from sqlalchemy.orm import Session

# Passe diesen Import an dein Projekt an:
from shared.models.price_alarm_model import PriceAlarm, AlarmType, AlarmDirection

# -------------------------------------------------------------------
# 1. Reine Logik zur Alarm-Evaluierung (OHNE DB-Zugriff)
# -------------------------------------------------------------------
def evaluate_alarm_condition(
    alarm: PriceAlarm,
    current_price: float,
    get_historical_price: Optional[Callable[[str, int], Optional[float]]] = None
) -> bool:
    """
    Prüft rein logisch, ob ein einzelner PriceAlarm beim aktuellen Kurs auslösen muss.
    """
    # --- ABSOLUTE_PRICE ---
    if alarm.alarm_type == AlarmType.ABSOLUTE_PRICE:
        if alarm.target_price is None:
            return False

        if alarm.direction == AlarmDirection.ABOVE:
            return current_price >= alarm.target_price
        elif alarm.direction == AlarmDirection.BELOW:
            return current_price <= alarm.target_price
        elif alarm.direction == AlarmDirection.BOTH:
            if alarm.reference_price is None:
                return False
            target_distance = abs(alarm.target_price - alarm.reference_price)
            current_distance = abs(current_price - alarm.reference_price)
            return current_distance >= target_distance

    # --- DYNAMIC_PERCENTAGE ---
    elif alarm.alarm_type == AlarmType.DYNAMIC_PERCENTAGE:
        if alarm.target_percentage is None or not alarm.reference_price:
            return False

        price_change_pct = ((current_price - alarm.reference_price) / alarm.reference_price) * 100.0

        if alarm.direction == AlarmDirection.ABOVE:
            return price_change_pct >= alarm.target_percentage
        elif alarm.direction == AlarmDirection.BELOW:
            return price_change_pct <= -alarm.target_percentage
        elif alarm.direction == AlarmDirection.BOTH:
            return abs(price_change_pct) >= alarm.target_percentage

    # --- TIMEFRAME_PERCENTAGE ---
    elif alarm.alarm_type == AlarmType.TIMEFRAME_PERCENTAGE:
        if alarm.target_percentage is None or alarm.timeframe_minutes is None:
            return False
        if not get_historical_price:
            return False

        old_price = get_historical_price(alarm.coin_symbol, alarm.timeframe_minutes)
        if not old_price:
            return False

        timeframe_change_pct = ((current_price - old_price) / old_price) * 100.0

        if alarm.direction == AlarmDirection.ABOVE:
            return timeframe_change_pct >= alarm.target_percentage
        elif alarm.direction == AlarmDirection.BELOW:
            return timeframe_change_pct <= -alarm.target_percentage
        elif alarm.direction == AlarmDirection.BOTH:
            return abs(timeframe_change_pct) >= alarm.target_percentage

    return False


# -------------------------------------------------------------------
# 2. Preis-Tick Verarbeitung mit DB-Update
# -------------------------------------------------------------------
async def process_price_tick(
    db: Session,
    coin_symbol: str,
    current_price: float,
    get_historical_price_func=None
):
    """
    Wird aufgerufen, wenn ein neuer Preis reinkommt.
    Wichtig: Recorde zuerst den Preis für Timeframe-Alarme!
    """
    # 1. Preis in Historie schreiben
    record_price(coin_symbol, current_price)

    # 2. Nur aktive & ungetriggerte Alarme laden
    active_alarms = db.query(PriceAlarm).filter(
        PriceAlarm.coin_symbol == coin_symbol.upper(),
        PriceAlarm.is_active,
        not_(PriceAlarm.is_triggered)
    ).all()

    if not active_alarms:
        return

    triggered_alarms = []

    # 3. Alarme prüfen
    for alarm in active_alarms:
        if evaluate_alarm_condition(alarm, current_price, get_historical_price_func or get_historical_price):
            alarm.is_triggered = True
            alarm.is_active = False
            alarm.last_triggered_at = datetime.now(timezone.utc)
            triggered_alarms.append(alarm)

    # 4. In DB speichern
    if triggered_alarms:
        db.commit()
        for triggered_alarm in triggered_alarms:
            print(f"🚨 ALARM AUSGELÖST! [ID: {triggered_alarm.id}] {triggered_alarm.coin_symbol} bei ${current_price}")


# -------------------------------------------------------------------
# 3. Timeframe Price-History Memory Buffer
# -------------------------------------------------------------------
price_history = defaultdict(list)

def record_price(symbol: str, price: float):
    """Speichert den aktuellen Preis mit Zeitstempel und säubert Daten älter als 60 Min."""
    now = time.time()
    symbol_upper = symbol.upper()
    price_history[symbol_upper].append((now, price))

    cutoff = now - 3600
    price_history[symbol_upper] = [item for item in price_history[symbol_upper] if item[0] >= cutoff]


def get_historical_price(symbol: str, minutes: int) -> Optional[float]:
    """Findet den Kurs, der am nächsten an 'vor N Minuten' liegt."""
    symbol_upper = symbol.upper()
    if symbol_upper not in price_history or not price_history[symbol_upper]:
        return None

    target_time = time.time() - (minutes * 60)
    closest_entry = min(price_history[symbol_upper], key=lambda item: abs(item[0] - target_time))

    # Nur zurückgeben, wenn der Eintrag zeitlich nah genug liegt (max. 2 Min Abweichung)
    if abs(closest_entry[0] - target_time) < 120:
        return closest_entry[1]

    return None