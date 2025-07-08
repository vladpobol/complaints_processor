from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


class StatusEnum(str, Enum):
    open = "open"
    closed = "closed"


class CategoryEnum(str, Enum):
    technical = "technical"
    payment = "payment"
    other = "other"


class ComplaintCreate(BaseModel):
    text: str = Field(..., example="Не приходит SMS-код")


class ComplaintUpdate(BaseModel):
    status: StatusEnum


class ComplaintResponse(BaseModel):
    id: int
    text: str
    status: StatusEnum
    timestamp: datetime
    sentiment: str
    category: CategoryEnum

    class Config:
        orm_mode = True 