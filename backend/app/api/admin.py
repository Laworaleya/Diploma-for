from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import get_current_admin
from app.repositories import admin_repo

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/users")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _admin: dict = Depends(get_current_admin),
):
    users = await admin_repo.get_all_users_with_stats(skip, limit)
    return {"users": users, "count": len(users)}


@router.post("/users/{user_id}/block")
async def block_user(
    user_id: str,
    admin: dict = Depends(get_current_admin),
):
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Нельзя заблокировать себя")
    success = await admin_repo.block_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return {"detail": "Пользователь заблокирован"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: dict = Depends(get_current_admin),
):
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Нельзя удалить себя")
    success = await admin_repo.delete_user_and_data(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return {"detail": "Пользователь и все его данные удалены"}


@router.get("/stats")
async def get_stats(_admin: dict = Depends(get_current_admin)):
    return await admin_repo.get_global_stats()


@router.get("/ai-stats")
async def get_ai_stats(_admin: dict = Depends(get_current_admin)):
    return await admin_repo.get_ai_stats()


@router.get("/import-errors")
async def get_import_errors(_admin: dict = Depends(get_current_admin)):
    errors = await admin_repo.get_import_errors(limit=50)
    return {"errors": errors, "count": len(errors)}
