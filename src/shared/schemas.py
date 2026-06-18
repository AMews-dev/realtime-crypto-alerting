from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List
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
