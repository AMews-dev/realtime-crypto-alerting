from datetime import datetime, timezone
from sqlalchemy import update

from sqlalchemy.engine import CursorResult
from models.bot_model import BotModel
from sqlalchemy.orm import Session
from pydantic import BaseModel

from utils.symbols import normalize_pair
from exceptions.bot_exceptions import BotNotFoundError, BotRunningError


class BotInfoResponse(BaseModel):
    id: int
    symbol: str
    is_running: bool
    created_at: datetime | None = None


class BotRepository:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_response(row: object) -> BotInfoResponse:
        return BotInfoResponse(
            id=getattr(row, "id"),
            symbol=getattr(row, "symbol"),
            is_running=getattr(row, "is_running"),
            created_at=getattr(row, "created_at", None),
        )

    def get_by_id(self, bot_id: int) -> BotInfoResponse | None:
        row = (
            self.db.query(
                BotModel.id,
                BotModel.symbol,
                BotModel.is_running,
                BotModel.created_at,
            )
            .filter(BotModel.id == bot_id)
            .first()
        )
        return self._to_response(row) if row is not None else None

    def get_by_symbol(self, symbol: str) -> BotInfoResponse | None:
        normalized_symbol = normalize_pair(symbol)
        row = (
            self.db.query(
                BotModel.id,
                BotModel.symbol,
                BotModel.is_running,
                BotModel.createdAt,
            )
            .filter(BotModel.symbol == normalized_symbol)
            .first()
        )
        return self._to_response(row) if row is not None else None

    def get_all(self) -> list[BotInfoResponse]:
        rows = (
            self.db.query(
                BotModel.id,
                BotModel.symbol,
                BotModel.is_running,
                BotModel.createdAt,
            )
            .all()
        )
        return [self._to_response(row) for row in rows]

    def get_active(self) -> list[BotInfoResponse]:
        rows = (
            self.db.query(
                BotModel.id,
                BotModel.symbol,
                BotModel.is_running,
                BotModel.createdAt,
            )
            .filter(BotModel.is_running.is_(True)).all()
        )
        return [self._to_response(row) for row in rows]

    def create_bot(self, symbol: str) -> BotInfoResponse | None:
        normalized_symbol = normalize_pair(symbol)

        #first search if bot with this symbol already exist in db
        if self.get_by_symbol(normalized_symbol) is not None:
            raise ValueError(f"Bot with symbol '{normalized_symbol}' already exists")

        newbot = BotModel(symbol=normalized_symbol)
        self.db.add(newbot)
        self.db.commit()
        self.db.refresh(newbot)
        return BotInfoResponse.model_validate(newbot)

    def delete_bot(self, symbol: str) -> BotInfoResponse | None:
        normalized_symbol = normalize_pair(symbol)

        bot = self.get_by_symbol(normalized_symbol)
        if bot is None:
            raise BotNotFoundError(normalized_symbol)

        # if bot is running error
        if bot.is_running:
            raise BotRunningError(normalized_symbol)

        # bot doenst run in ram so it can be deletet

        self.db.query(BotModel).filter(BotModel.symbol == normalized_symbol).delete()
        self.db.commit()

        return bot

    def set_running(self, bot_id: int, is_running: bool)  -> bool:
        stmt = (
            update(BotModel)
            .where(BotModel.id == bot_id)
            .values(
                is_running=is_running,
                updatedAt=datetime.now(timezone.utc),
            )
        )
        result = self.db.execute(stmt)
        self.db.commit()#
        if isinstance(result, CursorResult):
            return (result.rowcount or 0) > 0
        return False
