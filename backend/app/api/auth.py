from fastapi import APIRouter, Depends
from app.models.user import UserCreate, UserLogin, UserUpdate
from app.services import auth_service
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register")
async def register(data: UserCreate):
    """Register a new user account. Returns JWT token + user object."""
    return await auth_service.register_user(data)


@router.post("/login")
async def login(data: UserLogin):
    """Login and receive JWT token."""
    return await auth_service.login_user(data.email, data.password)


@router.get("/me")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile."""
    return auth_service._build_user_response(current_user)


@router.put("/me")
async def update_profile(
    data: UserUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update current user profile (name, language, currency)."""
    return await auth_service.update_profile(
        current_user["id"],
        data.model_dump(exclude_unset=True),
    )
