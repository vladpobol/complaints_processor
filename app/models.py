from sqlalchemy import Column, Integer, String, DateTime, Enum
from datetime import datetime
from enum import Enum as PyEnum

from app.database import Base


class StatusEnum(str, PyEnum):
    open = "open"
    closed = "closed"


class CategoryEnum(str, PyEnum):
    technical = "technical"
    payment = "payment"
    other = "other"


class Complaint(Base):
    __tablename__ = "complaints"

    id: int = Column(Integer, primary_key=True, index=True)
    text: str = Column(String, nullable=False)
    status: str = Column(Enum(StatusEnum), default=StatusEnum.open, nullable=False)
    timestamp: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    sentiment: str | None = Column(String, default="unknown")
    category: str = Column(Enum(CategoryEnum), default=CategoryEnum.other, nullable=False) 