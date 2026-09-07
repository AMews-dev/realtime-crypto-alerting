from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, model_validator

class AlarmType(str, Enum):
    ABSOLUTE_PRICE = "ABSOLUTE_PRICE"  # Fester Zielpreis (z.B. 65.000$)
    DYNAMIC_PERCENTAGE = "DYNAMIC_PERCENTAGE"  # +/- X% vom Ausgangspreis ab jetzt
    TIMEFRAME_PERCENTAGE = "TIMEFRAME_PERCENTAGE"  # +/- X% in Y Minuten
    ATH_ATL = "ATH_ATL"  # Allzeithoch / Allzeittief


class AlarmDirection(str, Enum):
    ABOVE = "ABOVE"  # Preis überschreitet Ziel
    BELOW = "BELOW"  # Preis unterschreitet Ziel
    BOTH = "BOTH"  # Bei relativen Alerts (+/- 5%)


# 2. Schema für die ANFRAGE vom Client (CREATE)
class CreateAlertSchema(BaseModel):
    coin_symbol: str = Field(..., json_schema_extra={"example": "BTC"})
    alarm_type: AlarmType = Field(default=AlarmType.ABSOLUTE_PRICE)
    direction: AlarmDirection

    # Werte-Felder je nach Typ optional
    target_price: Optional[float] = Field(None, examples=[95000.0])
    target_percentage: Optional[float] = Field(None, examples=[5.0])
    timeframe_minutes: Optional[int] = Field(None, examples=[15])

    # Validiert, ob die richtigen Felder für den jeweiligen Typ da sind
    @model_validator(mode="after")
    def validate_alarm_fields(self):
        if self.alarm_type == AlarmType.ABSOLUTE_PRICE and self.target_price is None:
            raise ValueError("Für ABSOLUTE_PRICE muss ein 'target_price' angegeben werden.")

        if self.alarm_type == AlarmType.TIMEFRAME_PERCENTAGE:
            if self.target_percentage is None or self.timeframe_minutes is None:
                raise ValueError(
                    "Für TIMEFRAME_PERCENTAGE werden 'target_percentage' und 'timeframe_minutes' benötigt.")

        return self

# 3. Schema für die ANTWORT vom Backend (RESPONSE)
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