
from typing import Optional
from pydantic import BaseModel


class BotCreateSchema(BaseModel):
    symbol: str


class BotCreateResponseSchema(BaseModel):
    symbol: str
    status: str
    id: int


class StopBotSchema(BaseModel):
    symbol: str


class BotUpdateSchema(BaseModel):
    name: Optional[str] = None
    threshold: Optional[float] = None
    enabled: Optional[bool] = None