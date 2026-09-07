from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
import re


@dataclass
class BotCreateSchema:
    symbol: str


@dataclass
class BotCreateResponseSchema:
    symbol: str
    status: str
    id: int


# 1. Ein Schema für den Body definieren
class StopBotSchema(BaseModel):
    symbol: str


class BotUpdate(BaseModel):
    name: Optional[str]
    threshold: Optional[float]
    enabled: Optional[float]


class BotDelete(BaseModel):
    pass


class CreateAlertSchema(BaseModel):
    coin_symbol: str
    direction: str
    # Optionale Felder mit Standardwerten belegen
    activation_price: Optional[float] = None
    is_active: bool = True
    target_percentage: Optional[float] = None
    target_price: Optional[float] = None

    @model_validator(mode="after")
    def check_price_or_percentage(self):
        # Wenn BEIDE Felder leer sind, werfen wir einen Fehler
        if self.target_price is None and self.target_percentage is None:
            raise ValueError("Du musst entweder einen 'target_price' oder ein 'target_percentage' angeben.")
        return self




class CreateUser(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator("password")
    @classmethod
    def password_complexity(cls, value: str) -> str:
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain alteast one smal number")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain alteast one big number")
        if not re.search(r"[0-9]", value):
            raise ValueError("Das Passwort muss mindestens eine Zahl enthalten.")
        if not re.search(r"[^a-zA-Z0-9]", value):
            raise ValueError("Das Passwort muss mindestens ein Sonderzeichen enthalten (z. B. !, $, %, @).")

        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str

