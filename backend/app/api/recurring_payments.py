from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.models.recurring_payment import RecurringPaymentCreate, RecurringPaymentUpdate
from app.services import recurring_payment_service

router = APIRouter(prefix="/api/recurring-payments", tags=["Recurring Payments"])


@router.get("")
async def list_recurring_payments(current_user: dict = Depends(get_current_user)):
    return await recurring_payment_service.get_user_recurring_payments(current_user["id"])


@router.post("")
async def create_recurring_payment(
    data: RecurringPaymentCreate,
    current_user: dict = Depends(get_current_user),
):
    return await recurring_payment_service.create_recurring_payment(current_user["id"], data)


@router.put("/{payment_id}")
async def update_recurring_payment(
    payment_id: str,
    data: RecurringPaymentUpdate,
    current_user: dict = Depends(get_current_user),
):
    return await recurring_payment_service.update_recurring_payment(
        payment_id,
        current_user["id"],
        data,
    )


@router.delete("/{payment_id}")
async def delete_recurring_payment(
    payment_id: str,
    current_user: dict = Depends(get_current_user),
):
    await recurring_payment_service.delete_recurring_payment(payment_id, current_user["id"])
    return {"detail": "Recurring payment deleted"}
