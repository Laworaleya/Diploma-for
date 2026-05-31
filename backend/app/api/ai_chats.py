from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import get_current_user
from app.core.middleware import check_ai_rate_limit
from app.models.ai_chat import AIChatCreate, AIChatUpdate, AIMessageCreate
from app.services import ai_chat_service

router = APIRouter(prefix="/api/ai", tags=["AI Chat"])


async def _require_ai_quota(current_user: dict) -> None:
    """Raise 429 if the user has exceeded their hourly AI call quota."""
    if not await check_ai_rate_limit(current_user["id"]):
        raise HTTPException(
            status_code=429,
            detail="Превышен лимит AI-запросов (20 в час). Попробуйте позже.",
        )


@router.get("/chats")
async def list_ai_chats(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    return await ai_chat_service.get_user_chats(current_user["id"], skip, limit)


@router.post("/chats")
async def create_ai_chat(
    data: AIChatCreate,
    current_user: dict = Depends(get_current_user),
):
    return await ai_chat_service.create_chat(current_user["id"], data)


@router.get("/chats/{chat_id}")
async def get_ai_chat(
    chat_id: str,
    current_user: dict = Depends(get_current_user),
):
    return await ai_chat_service.get_chat_detail(chat_id, current_user["id"])


@router.patch("/chats/{chat_id}")
async def rename_ai_chat(
    chat_id: str,
    data: AIChatUpdate,
    current_user: dict = Depends(get_current_user),
):
    return await ai_chat_service.rename_chat(chat_id, current_user["id"], data.title)


@router.delete("/chats/{chat_id}")
async def delete_ai_chat(
    chat_id: str,
    current_user: dict = Depends(get_current_user),
):
    await ai_chat_service.delete_chat(chat_id, current_user["id"])
    return {"detail": "Chat deleted"}


@router.post("/chats/{chat_id}/messages")
async def send_ai_message(
    chat_id: str,
    data: AIMessageCreate,
    current_user: dict = Depends(get_current_user),
):
    await _require_ai_quota(current_user)
    return await ai_chat_service.send_message(chat_id, current_user["id"], data.content)


@router.post("/reports/{report_id}/analyze")
async def analyze_report_with_ai(
    report_id: str,
    current_user: dict = Depends(get_current_user),
):
    await _require_ai_quota(current_user)
    return await ai_chat_service.analyze_report(report_id, current_user)


@router.post("/goals/{goal_id}/plan")
async def plan_goal_with_ai(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
):
    await _require_ai_quota(current_user)
    return await ai_chat_service.plan_goal(goal_id, current_user)
