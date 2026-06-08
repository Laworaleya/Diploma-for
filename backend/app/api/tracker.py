from calendar import monthrange
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.core.dependencies import get_current_user
from app.core.database import get_database


class AddExpenseBody(BaseModel):
    amount: float = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class AddIncomeBody(BaseModel):
    amount: float = Field(..., gt=0)


class SetBudgetBody(BaseModel):
    amount: float = Field(..., gt=0)

router = APIRouter(prefix="/api/tracker", tags=["Tracker"])


def _current_period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _month_bounds(period: str) -> tuple[datetime, datetime]:
    year, month = map(int, period.split("-"))
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    last_day = monthrange(year, month)[1]
    end = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)
    return start, end


def _subtract_months(year: int, month: int, n: int) -> tuple[int, int]:
    month -= n
    while month <= 0:
        month += 12
        year -= 1
    return year, month


@router.get("/summary")
async def get_summary(
    period: str = Query(default=None),
    current_user: dict = Depends(get_current_user),
):
    if not period:
        period = _current_period()

    db = get_database()
    user_id = current_user["id"]
    month_start, month_end = _month_bounds(period)

    budget = await db.user_budgets.find_one({"user_id": user_id, "period": period})
    monthly_limit = budget.get("monthly_limit", 0) if budget else 0
    total_income = budget.get("total_income", 0) if budget else 0
    total_expense = budget.get("total_expense", 0) if budget else 0
    current_balance = total_income - total_expense
    usage_pct = round(total_expense / monthly_limit * 100, 1) if monthly_limit > 0 else 0

    # Daily expense aggregation
    daily_pipeline = [
        {"$match": {"user_id": user_id, "type": "expense", "created_at": {"$gte": month_start, "$lte": month_end}}},
        {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}}, "amount": {"$sum": "$amount"}}},
        {"$sort": {"_id": 1}},
    ]
    daily_map = {}
    async for doc in db.transactions.aggregate(daily_pipeline):
        daily_map[doc["_id"]] = doc["amount"]

    year, month = map(int, period.split("-"))
    last_day = monthrange(year, month)[1]
    daily_expenses = [
        {"date": f"{year}-{month:02d}-{d:02d}", "amount": daily_map.get(f"{year}-{month:02d}-{d:02d}", 0)}
        for d in range(1, last_day + 1)
    ]

    # Category breakdown
    cat_pipeline = [
        {"$match": {"user_id": user_id, "type": "expense", "created_at": {"$gte": month_start, "$lte": month_end}}},
        {"$group": {"_id": "$category", "amount": {"$sum": "$amount"}}},
        {"$sort": {"amount": -1}},
    ]
    categories = []
    async for doc in db.transactions.aggregate(cat_pipeline):
        pct = round(doc["amount"] / total_expense * 100, 1) if total_expense > 0 else 0
        categories.append({"name": doc["_id"], "amount": doc["amount"], "pct": pct})

    # Velocity & forecast
    now = datetime.now(timezone.utc)
    days_passed = max((now - month_start).days, 1) if period == _current_period() else last_day
    daily_rate = round(total_expense / days_passed, 0) if days_passed > 0 else 0
    days_left_forecast = int(current_balance / daily_rate) if daily_rate > 0 and current_balance > 0 else None

    return {
        "period": period,
        "budget": {
            "monthly_limit": monthly_limit,
            "total_income": total_income,
            "total_expense": total_expense,
            "current_balance": current_balance,
            "usage_pct": usage_pct,
        },
        "daily_expenses": daily_expenses,
        "categories": categories,
        "daily_rate": daily_rate,
        "days_left_forecast": days_left_forecast,
    }


@router.get("/transactions")
async def get_transactions(
    period: str = Query(default=None),
    limit: int = Query(default=50, le=200),
    skip: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    if not period:
        period = _current_period()

    db = get_database()
    user_id = current_user["id"]
    month_start, month_end = _month_bounds(period)

    match = {"user_id": user_id, "created_at": {"$gte": month_start, "$lte": month_end}}
    total = await db.transactions.count_documents(match)
    cursor = db.transactions.find(match).sort("created_at", -1).skip(skip).limit(limit)

    items = []
    async for doc in cursor:
        created = doc.get("created_at")
        items.append({
            "id": str(doc["_id"]),
            "type": doc.get("type"),
            "amount": doc.get("amount", 0),
            "category": doc.get("category", ""),
            "description": doc.get("description"),
            "created_at": created.isoformat() if isinstance(created, datetime) else created,
        })

    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/monthly-history")
async def get_monthly_history(
    months: int = Query(default=6, le=12, ge=1),
    current_user: dict = Depends(get_current_user),
):
    db = get_database()
    user_id = current_user["id"]
    now = datetime.now(timezone.utc)
    cur_year, cur_month = now.year, now.month

    results = []
    for i in range(months - 1, -1, -1):
        y, m = _subtract_months(cur_year, cur_month, i)
        period = f"{y}-{m:02d}"
        budget = await db.user_budgets.find_one({"user_id": user_id, "period": period})
        results.append({
            "period": period,
            "total_expense": budget.get("total_expense", 0) if budget else 0,
            "total_income": budget.get("total_income", 0) if budget else 0,
            "monthly_limit": budget.get("monthly_limit", 0) if budget else 0,
        })

    return results


@router.post("/expense")
async def add_expense(
    body: AddExpenseBody,
    current_user: dict = Depends(get_current_user),
):
    db = get_database()
    user_id = current_user["id"]
    period = _current_period()
    now = datetime.now(timezone.utc)

    await db.transactions.insert_one({
        "user_id": user_id,
        "type": "expense",
        "amount": body.amount,
        "category": body.category,
        "description": body.description,
        "created_at": now,
    })

    budget = await db.user_budgets.find_one_and_update(
        {"user_id": user_id, "period": period},
        {
            "$inc": {"total_expense": body.amount},
            "$set": {"updated_at": now},
            "$setOnInsert": {"monthly_limit": 0.0, "total_income": 0.0, "created_at": now},
        },
        upsert=True,
        return_document=True,
    )

    monthly_limit = budget.get("monthly_limit", 0) if budget else 0
    total_income  = budget.get("total_income", 0) if budget else 0
    total_expense = budget.get("total_expense", 0) if budget else body.amount
    balance = total_income - total_expense
    usage_pct = round(total_expense / monthly_limit * 100, 1) if monthly_limit > 0 else 0

    return {
        "amount": body.amount,
        "category": body.category,
        "balance": balance,
        "total_expense": total_expense,
        "monthly_limit": monthly_limit,
        "usage_pct": usage_pct,
    }


@router.post("/income")
async def add_income(
    body: AddIncomeBody,
    current_user: dict = Depends(get_current_user),
):
    db = get_database()
    user_id = current_user["id"]
    period = _current_period()
    now = datetime.now(timezone.utc)

    budget = await db.user_budgets.find_one_and_update(
        {"user_id": user_id, "period": period},
        {
            "$inc": {"total_income": body.amount, "monthly_limit": body.amount},
            "$set": {"updated_at": now},
            "$setOnInsert": {"total_expense": 0.0, "created_at": now},
        },
        upsert=True,
        return_document=True,
    )

    total_income  = budget.get("total_income", 0) if budget else body.amount
    total_expense = budget.get("total_expense", 0) if budget else 0
    balance = total_income - total_expense

    return {"amount": body.amount, "balance": balance, "total_income": total_income}


@router.put("/budget")
async def set_budget(
    body: SetBudgetBody,
    current_user: dict = Depends(get_current_user),
):
    db = get_database()
    user_id = current_user["id"]
    period = _current_period()
    now = datetime.now(timezone.utc)

    budget = await db.user_budgets.find_one_and_update(
        {"user_id": user_id, "period": period},
        {
            "$set": {"monthly_limit": body.amount, "updated_at": now},
            "$setOnInsert": {"total_income": body.amount, "total_expense": 0.0, "created_at": now},
        },
        upsert=True,
        return_document=True,
    )

    return {
        "monthly_limit": body.amount,
        "total_income": budget.get("total_income", 0) if budget else body.amount,
        "total_expense": budget.get("total_expense", 0) if budget else 0,
    }


@router.delete("/transaction/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    current_user: dict = Depends(get_current_user),
):
    from bson import ObjectId
    db = get_database()
    user_id = current_user["id"]
    period = _current_period()
    now = datetime.now(timezone.utc)

    try:
        txn = await db.transactions.find_one({"_id": ObjectId(transaction_id), "user_id": user_id})
    except Exception:
        txn = None

    if not txn:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Transaction not found")

    await db.transactions.delete_one({"_id": ObjectId(transaction_id)})

    # Revert the budget counter
    if txn["type"] == "expense":
        await db.user_budgets.update_one(
            {"user_id": user_id, "period": period},
            {"$inc": {"total_expense": -txn["amount"]}, "$set": {"updated_at": now}},
        )
    else:
        await db.user_budgets.update_one(
            {"user_id": user_id, "period": period},
            {"$inc": {"total_income": -txn["amount"], "monthly_limit": -txn["amount"]}, "$set": {"updated_at": now}},
        )

    return {"ok": True}


@router.post("/ai-report")
async def create_ai_report(
    body: dict,
    current_user: dict = Depends(get_current_user),
):
    """Build a monthly report and send it to AI for financial advice."""
    from app.services.ai_chat_service import analyze_tracker_report
    period = body.get("period", _current_period())
    return await analyze_tracker_report(period=period, current_user=current_user)
