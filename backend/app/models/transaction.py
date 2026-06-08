from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class TransactionCreate(BaseModel):
    type: Literal["expense", "income"]
    amount: float = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class TransactionResponse(BaseModel):
    id: str
    user_id: str
    type: str
    amount: float
    category: str
    description: Optional[str]
    created_at: datetime
