from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from shared.user_model import Base


class PriceAlarm(Base):
    __tablename__ = "price_alarm"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    coin_symbol = Column(String(20), nullable=False)

    activation_price = Column(Float, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    target_percentage = Column(Float, nullable=True)

    target_price = Column(Float, nullable=True)

    direction = Column(String(10), nullable=False)

    is_triggered = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="alarms")

