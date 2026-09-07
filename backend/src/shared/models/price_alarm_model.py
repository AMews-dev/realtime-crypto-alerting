from sqlalchemy import Enum, Column, Integer, String, Boolean, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from shared.schemas.price_alarm import AlarmType, AlarmDirection
from shared.user_model import Base
from datetime import datetime, timezone


# __table_args__ = (
#         # Erstellt einen kombinierten Index für die exakte Abfrage deines Workers
#         Index("idx_active_coin", "coin_symbol", "is_active"),
#     )

class PriceAlarm(Base):
    __tablename__ = "price_alarm"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    coin_symbol = Column(String(20), nullable=False, index=True)

    # typ richtung
    alarm_type = Column(Enum(AlarmType), nullable=False, default=AlarmType.ABSOLUTE_PRICE)
    direction = Column(Enum(AlarmDirection), nullable=False)

    # werte felder für die verschiedenen phase-1 alerts
    target_price = Column(Float, nullable=True)
    target_percentage = Column(Float, nullable=True)
    reference_price = Column(Float, nullable=True)
    timeframe_minutes = Column(Integer, nullable=True)

    #status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_triggered = Column(Boolean, default=False, nullable=False)

    #timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)

    # relationsship
    user = relationship("User", back_populates="alarms")

# class PriceAlarm(Base):
#     __tablename__ = "price_alarm"
#
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
#     coin_symbol = Column(String(20), nullable=False)
#
#     activation_price = Column(Float, nullable=True)
#
#     is_active = Column(Boolean, default=True, nullable=False)
#
#     target_percentage = Column(Float, nullable=True)
#
#     target_price = Column(Float, nullable=True)
#
#     direction = Column(String(10), nullable=False)
#
#     is_triggered = Column(Boolean, default=False, nullable=False)
#
#     created_at = Column(
#         DateTime(timezone=True),
#         default=lambda: datetime.now(timezone.utc),
#         nullable=False
#     )
#
#     updated_at = Column(
#         DateTime(timezone=True),
#         default=lambda: datetime.now(timezone.utc),
#         onupdate=lambda: datetime.now(timezone.utc),
#         nullable=False
#     )
#     user = relationship("User", back_populates="alarms")
