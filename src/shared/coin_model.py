from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime

class CryptoCoin(Base):
    __tablename__ = "CryptoCoin"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    is_running = Column(Boolean, default=False, nullable=False)
    createdAt = Column(DateTime, default=datetime.timezone.utc, nullable=False)
    updatedAt = Column(DateTime, default=datetime.timezone.utc, nullable=False)