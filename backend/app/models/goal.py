from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date


class GoalCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    goal_type: str = Field(..., pattern="^(savings|investment|custom)$")
    target_amount: float = Field(..., gt=0)
    current_amount: float = Field(default=0, ge=0)
    deadline: Optional[str] = None  # ISO date string "2026-12-31"
    description: Optional[str] = Field(None, max_length=500)


class GoalUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    current_amount: Optional[float] = Field(None, ge=0)
    target_amount: Optional[float] = Field(None, gt=0)
    deadline: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|completed|cancelled)$")
    description: Optional[str] = Field(None, max_length=500)


class GoalResponse(BaseModel):
    id: str
    user_id: str
    title: str
    goal_type: str
    target_amount: float
    current_amount: float
    deadline: Optional[str]
    status: str
    description: Optional[str]
    progress_percent: float
    created_at: datetime
