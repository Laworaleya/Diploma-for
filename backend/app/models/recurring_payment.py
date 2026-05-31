from typing import Literal, Optional
from pydantic import BaseModel, Field


PaymentPeriod = Literal["monthly"]
PaymentStatus = Literal["safe", "soon", "urgent", "overdue"]
PaymentSource = Literal["manual", "requiredCategory"]


class RecurringPaymentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., ge=0)
    originalPaymentDate: str = Field(..., min_length=8, max_length=20)
    period: PaymentPeriod = "monthly"


class RecurringPaymentCreate(RecurringPaymentBase):
    iconColor: Optional[str] = None


class RecurringPaymentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    amount: Optional[float] = Field(None, ge=0)
    originalPaymentDate: Optional[str] = Field(None, min_length=8, max_length=20)
    period: Optional[PaymentPeriod] = None
    iconColor: Optional[str] = None


class RecurringPaymentResponse(RecurringPaymentBase):
    id: str
    user_id: str
    paymentDay: int
    paymentMonth: int
    paymentYear: int
    nextPaymentDate: str
    status: PaymentStatus
    iconColor: str
    source: PaymentSource
