from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime
from sqlalchemy.sql import func
from database import Base  # Deine zentrale Base-Klasse für SQLAlchemy
from database import Base
from datetime import datetime

class BotModel(Base):
    __tablename__ = "bots"

    # 1. Eindeutige ID (wird von PostgreSQL automatisch hochgezählt)
    id = Column(Integer, primary_key=True, index=True, unique=True)

    symbol = Column(String(100), nullable=False, index=True, unique=True)




    is_running = Column(Boolean, default=False, nullable=False, index=True)

    createdAt = Column(DateTime, default=datetime.now(), nullable=False)
    updatedAt = Column(DateTime, default=datetime.now(), onupdate=datetime.now, nullable=False)