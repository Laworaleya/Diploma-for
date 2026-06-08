from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserBudgetResponse(BaseModel):
    id: str
    user_id: str
    period: str
    monthly_limit: float
    total_income: float
    total_expense: float
    current_balance: float
    created_at: datetime
    updated_at: datetime
