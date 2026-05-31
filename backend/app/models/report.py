from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ExpenseCategory(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., ge=0)
    custom: bool = Field(default=False)


class RequiredCategory(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., ge=0)
    period: str = Field(..., min_length=1, max_length=100)
    duration: Optional[str] = Field(None, max_length=100)
    paymentDate: Optional[str] = Field(None, max_length=30)


class ReportCreate(BaseModel):
    period: str = Field(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$")  # e.g. "2026-03"
    total_income: float = Field(..., ge=0)
    total_expense: float = Field(..., ge=0)
    categories: List[ExpenseCategory] = Field(default_factory=list)
    required_categories: List[RequiredCategory] = Field(default_factory=list)


class ReportUpdate(BaseModel):
    period: Optional[str] = Field(None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    total_income: Optional[float] = Field(None, ge=0)
    total_expense: Optional[float] = Field(None, ge=0)
    categories: Optional[List[ExpenseCategory]] = None
    required_categories: Optional[List[RequiredCategory]] = None


class ReportResponse(BaseModel):
    id: str
    user_id: str
    period: str
    total_income: float
    total_expense: float
    categories: List[ExpenseCategory]
    required_categories: List[RequiredCategory] = Field(default_factory=list)
    unaccounted_expense: float
    surplus: float
    created_at: datetime
    updated_at: datetime


class BalanceSummary(BaseModel):
    total_income: float
    total_expense: float
    categorized_total: float
    unaccounted_expense: float
    surplus: float
    expense_ratio: float  # total_expense / total_income as percentage
    category_breakdown: List[dict]  # [{name, amount, percentage}]
