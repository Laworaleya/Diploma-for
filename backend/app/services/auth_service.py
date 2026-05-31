from fastapi import HTTPException, status
from datetime import datetime
from app.core.security import hash_password, verify_password, create_access_token
from app.repositories import user_repo


async def register_user(data) -> dict:
    """Register a new user with hashed password."""
    existing = await user_repo.find_user_by_email(data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user_data = {
        "email": data.email,
        "hashed_password": hash_password(data.password),
        "name": data.name,
        "preferred_language": data.preferred_language,
        "currency": data.currency,
    }

    user = await user_repo.create_user(user_data)
    token = create_access_token({"sub": user["id"]})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _build_user_response(user),
    }


async def login_user(email: str, password: str) -> dict:
    """Authenticate user and return JWT token."""
    user = await user_repo.find_user_by_email(email)
    if not user or not verify_password(password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if user.get("is_blocked"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт заблокирован администратором",
        )

    token = create_access_token({"sub": user["id"]})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _build_user_response(user),
    }


async def update_profile(user_id: str, update_data: dict) -> dict:
    """Update user profile."""
    filtered = {k: v for k, v in update_data.items() if v is not None}
    if not filtered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    user = await user_repo.update_user(user_id, filtered)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _build_user_response(user)


def _build_user_response(user: dict) -> dict:
    """Build safe user response — converts all types to JSON-serializable."""
    created = user.get("created_at")
    if isinstance(created, datetime):
        created = created.isoformat()

    return {
        "id": str(user.get("id", "")),
        "email": user.get("email", ""),
        "name": user.get("name", ""),
        "preferred_language": user.get("preferred_language", "ru"),
        "currency": user.get("currency", "KZT"),
        "role": user.get("role", "user"),
        "created_at": created,
    }
