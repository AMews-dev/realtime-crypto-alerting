from sqlalchemy import Column, Integer, String, Boolean,DateTime
from database import Base
from datetime import datetime, timezone


class BotModel(Base):
    __tablename__ = "bots"

    # 1. Eindeutige ID (wird von PostgreSQL automatisch hochgezählt)
    id = Column(Integer, primary_key=True, index=True, unique=True)

    symbol = Column(String(100), nullable=False, index=True, unique=True)

    is_running = Column(Boolean, default=False, nullable=False, index=True)

    createdAt = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updatedAt = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
