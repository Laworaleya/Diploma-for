from fastapi import HTTPException
from app.models.recurring_payment import RecurringPaymentCreate, RecurringPaymentUpdate
from app.repositories import recurring_payment_repo
from app.services.recurring_payment_logic import (
    build_recurring_payment_payload,
    createRecurringPaymentFromRequiredCategory,
)


async def create_recurring_payment(user_id: str, data: RecurringPaymentCreate) -> dict:
    payment_data = build_recurring_payment_payload(
        title=data.title,
        amount=data.amount,
        original_payment_date=data.originalPaymentDate,
        period=data.period,
        source="manual",
        user_id=user_id,
        icon_color=data.iconColor,
    )
    duplicate = await recurring_payment_repo.find_duplicate(user_id, payment_data)
    if duplicate:
        return duplicate
    return await recurring_payment_repo.create_payment(payment_data)


async def create_from_required_category(user_id: str, category: dict) -> dict | None:
    try:
        payment_data = createRecurringPaymentFromRequiredCategory(category)
    except ValueError:
        return None

    payment_data["user_id"] = user_id
    duplicate = await recurring_payment_repo.find_duplicate(user_id, payment_data)
    if duplicate:
        return duplicate
    return await recurring_payment_repo.create_payment(payment_data)


async def sync_required_categories(user_id: str, categories: list[dict]) -> list[dict]:
    created = []
    for category in categories:
        payment = await create_from_required_category(user_id, category)
        if payment:
            created.append(payment)
    return created


async def get_user_recurring_payments(user_id: str) -> list[dict]:
    payments = await recurring_payment_repo.find_payments_by_user(user_id)
    refreshed = []
    for payment in payments:
        refreshed_payload = build_recurring_payment_payload(
            title=payment["title"],
            amount=payment["amount"],
            original_payment_date=payment["originalPaymentDate"],
            period=payment["period"],
            source=payment.get("source", "manual"),
            user_id=user_id,
            icon_color=payment.get("manualIconColor"),
        )
        if (
            refreshed_payload["nextPaymentDate"] != payment.get("nextPaymentDate")
            or refreshed_payload["status"] != payment.get("status")
        ):
            payment = await recurring_payment_repo.update_payment(payment["id"], user_id, refreshed_payload)
        refreshed.append(payment)
    return sorted(refreshed, key=lambda item: item["nextPaymentDate"])


async def update_recurring_payment(
    payment_id: str,
    user_id: str,
    data: RecurringPaymentUpdate,
) -> dict:
    existing = await recurring_payment_repo.find_payment_by_id(payment_id, user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Recurring payment not found")

    payment_data = build_recurring_payment_payload(
        title=data.title if data.title is not None else existing["title"],
        amount=data.amount if data.amount is not None else existing["amount"],
        original_payment_date=(
            data.originalPaymentDate
            if data.originalPaymentDate is not None
            else existing["originalPaymentDate"]
        ),
        period=data.period if data.period is not None else existing["period"],
        source=existing.get("source", "manual"),
        user_id=user_id,
        icon_color=data.iconColor if data.iconColor is not None else existing.get("manualIconColor"),
    )
    duplicate = await recurring_payment_repo.find_duplicate(user_id, payment_data)
    if duplicate and duplicate["id"] != payment_id:
        raise HTTPException(status_code=409, detail="Такой регулярный платеж уже существует")
    return await recurring_payment_repo.update_payment(payment_id, user_id, payment_data)


async def delete_recurring_payment(payment_id: str, user_id: str) -> bool:
    deleted = await recurring_payment_repo.delete_payment(payment_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Recurring payment not found")
    return True
