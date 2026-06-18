from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from database import Base
from sqlalchemy.orm import  relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    hashedPassword = Column(String(255), nullable=False)
    isAdmin = Column(Boolean, default=False, nullable=False)

    alarms = relationship("PriceAlarm", back_populates="user", cascade="all, delete-orphan")