from fastapi import APIRouter, Depends
from app.models.user import UserCreate, UserLogin, UserUpdate, TelegramAuthData
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


@router.post("/telegram")
async def telegram_login(data: TelegramAuthData):
    """Login or register via Telegram Login Widget. Verifies HMAC hash."""
    return await auth_service.telegram_login(data)


@router.get("/link-code")
async def generate_link_code(current_user: dict = Depends(get_current_user)):
    """Generate a 6-digit one-time code for linking Telegram account to this web account."""
    return await auth_service.generate_link_code(current_user["id"])
