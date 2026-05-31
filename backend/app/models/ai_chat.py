from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


AIMessageRole = Literal["user", "assistant"]
AIContextSource = Literal["manual", "financial_report", "goal"]


class ExpenseCategoryAIContext(BaseModel):
    name: str
    amount: float
    custom: bool = False


class RequiredCategoryAIContext(BaseModel):
    name: str
    amount: float
    period: str
    duration: Optional[str] = None
    paymentDate: Optional[str] = None


class RecurringPaymentAIContext(BaseModel):
    title: str
    amount: float
    period: str
    nextPaymentDate: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None


class FinancialReportSummaryAIContext(BaseModel):
    period: str
    total_income: float
    total_expense: float
    unaccounted_expense: float
    surplus: float
    categories: list[ExpenseCategoryAIContext] = Field(default_factory=list)


class FinancialReportAIContext(FinancialReportSummaryAIContext):
    required_categories: list[RequiredCategoryAIContext] = Field(default_factory=list)
    recurring_payments: list[RecurringPaymentAIContext] = Field(default_factory=list)


class GoalAIContext(BaseModel):
    title: str
    goal_type: str
    target_amount: float
    current_amount: float
    progress_percent: float
    deadline: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    recent_reports: list[FinancialReportSummaryAIContext] = Field(default_factory=list)
    recurring_payments: list[RecurringPaymentAIContext] = Field(default_factory=list)


class AIChat(BaseModel):
    id: str
    title: str
    source: AIContextSource = "manual"
    source_label: Optional[str] = None
    created_at: datetime | str
    updated_at: datetime | str


class AIMessage(BaseModel):
    id: str
    chat_id: str
    role: AIMessageRole
    content: str
    is_error: bool = False
    context_type: Optional[AIContextSource] = None
    created_at: datetime | str


class AIChatDetail(AIChat):
    messages: list[AIMessage] = Field(default_factory=list)


class AIChatCreate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=120)


class AIChatUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)


class AIMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=12000)


class AISendMessageResponse(BaseModel):
    chat: AIChat
    user_message: AIMessage
    assistant_message: AIMessage
    error: Optional[str] = None


class AIContextEnvelope(BaseModel):
    kind: AIContextSource
    payload: dict[str, Any]
