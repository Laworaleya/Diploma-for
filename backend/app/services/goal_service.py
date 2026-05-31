from fastapi import HTTPException
from app.repositories import goal_repo
from app.models.goal import GoalCreate, GoalUpdate


async def create_goal(user_id: str, data: GoalCreate) -> dict:
    """Create a new financial goal."""
    goal_data = {
        "user_id": user_id,
        "title": data.title,
        "goal_type": data.goal_type,
        "target_amount": data.target_amount,
        "current_amount": data.current_amount,
        "deadline": data.deadline,
        "description": data.description,
    }
    goal = await goal_repo.create_goal(goal_data)
    return _enrich_goal(goal)


async def get_user_goals(user_id: str) -> list:
    """Get all goals for a user with progress calculation."""
    goals = await goal_repo.find_goals_by_user(user_id)
    return [_enrich_goal(g) for g in goals]


async def get_goal(goal_id: str, user_id: str) -> dict:
    """Get a specific goal."""
    goal = await goal_repo.find_goal_by_id(goal_id, user_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return _enrich_goal(goal)


async def update_goal(goal_id: str, user_id: str, data: GoalUpdate) -> dict:
    """Update a financial goal."""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    goal = await goal_repo.update_goal(goal_id, user_id, update_data)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    # Auto-complete goal if current >= target
    if goal.get("current_amount", 0) >= goal.get("target_amount", 0):
        if goal.get("status") == "active":
            goal = await goal_repo.update_goal(goal_id, user_id, {"status": "completed"})

    return _enrich_goal(goal)


async def delete_goal(goal_id: str, user_id: str) -> bool:
    """Delete a financial goal."""
    deleted = await goal_repo.delete_goal(goal_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Goal not found")
    return True


def _enrich_goal(goal: dict) -> dict:
    """Add progress_percent to goal."""
    target = goal.get("target_amount", 1)
    current = goal.get("current_amount", 0)
    goal["progress_percent"] = round(min(100, (current / target * 100)) if target > 0 else 0, 1)
    return goal
