from fastapi import APIRouter, Depends
from app.models.goal import GoalCreate, GoalUpdate
from app.services import goal_service
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/api/goals", tags=["Financial Goals"])


@router.post("")
async def create_goal(
    data: GoalCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new financial goal (savings, investment, or custom)."""
    return await goal_service.create_goal(current_user["id"], data)


@router.get("")
async def list_goals(
    current_user: dict = Depends(get_current_user),
):
    """List all financial goals for the current user."""
    return await goal_service.get_user_goals(current_user["id"])


@router.get("/{goal_id}")
async def get_goal(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a specific financial goal."""
    return await goal_service.get_goal(goal_id, current_user["id"])


@router.put("/{goal_id}")
async def update_goal(
    goal_id: str,
    data: GoalUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update a financial goal. Auto-completes if target is reached."""
    return await goal_service.update_goal(goal_id, current_user["id"], data)


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a financial goal."""
    await goal_service.delete_goal(goal_id, current_user["id"])
    return {"detail": "Goal deleted"}
