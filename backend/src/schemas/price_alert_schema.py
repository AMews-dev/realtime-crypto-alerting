from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, model_validator, ConfigDict


class AlarmType(str, Enum):
    ABSOLUTE_PRICE = "ABSOLUTE_PRICE"  # Fester Zielpreis (z.B. 65.000$)
    DYNAMIC_PERCENTAGE = "DYNAMIC_PERCENTAGE"  # +/- X% vom Ausgangspreis ab jetzt
    TIMEFRAME_PERCENTAGE = "TIMEFRAME_PERCENTAGE"  # +/- X% in Y Minuten
    ATH_ATL = "ATH_ATL"  # Allzeithoch / Allzeittief


class AlarmDirection(str, Enum):
    ABOVE = "ABOVE"  # Preis überschreitet Ziel
    BELOW = "BELOW"  # Preis unterschreitet Ziel
    BOTH = "BOTH"  # Bei relativen Alerts (+/- 5%)


class CreateAlertSchema(BaseModel):
    coin_symbol: str
    direction: str
    activation_price: Optional[float] = None
    is_active: bool = True
    target_percentage: Optional[float] = None
    target_price: Optional[float] = None

    @model_validator(mode="after")
    def check_price_or_percentage(self):
        if self.target_price is None and self.target_percentage is None:
            raise ValueError(
                "Du musst entweder einen 'target_price' oder ein 'target_percentage' angeben."
            )
        return self

class AlertResponseSchema(BaseModel):
    id: int
    user_id: int
    coin_symbol: str
    alarm_type: AlarmType
    direction: AlarmDirection

    # Preis- & Prozent-Werte
    reference_price: Optional[float] = None  # Preis zum Erstellungszeitpunkt
    target_price: Optional[float] = None
    target_percentage: Optional[float] = None
    timeframe_minutes: Optional[int] = None

    # Status & Flags
    is_active: bool
    is_triggered: bool

    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_triggered_at: Optional[datetime] = None

    # SQLAlchemy -> Pydantic Konvertierung
    model_config = ConfigDict(from_attributes=True)