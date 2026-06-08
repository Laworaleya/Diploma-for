import hashlib
import hmac
import time
from fastapi import HTTPException, status
from datetime import datetime, timezone
from app.config import settings
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


async def generate_link_code(user_id: str) -> dict:
    """Generate a 6-digit code for linking Telegram to this web account."""
    import secrets, string
    from app.core.database import get_database

    db = get_database()
    # Remove any existing codes for this user
    await db.link_codes.delete_many({"user_id": user_id})
    code = "".join(secrets.choice(string.digits) for _ in range(6))
    await db.link_codes.insert_one({
        "code": code,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc),
    })
    return {"code": code}


async def telegram_login(data) -> dict:
    """Verify Telegram Login Widget data and return JWT token."""
    # Verify HMAC-SHA256 signature
    bot_token = settings.TELEGRAM_BOT_TOKEN
    if not bot_token:
        raise HTTPException(status_code=503, detail="Telegram login not configured")

    data_dict = {
        k: v for k, v in data.model_dump().items()
        if k != "hash" and v is not None
    }
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(data_dict.items()))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    expected_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_hash, data.hash):
        raise HTTPException(status_code=401, detail="Invalid Telegram auth data")

    # Check auth_date not older than 24 hours
    if time.time() - data.auth_date > 86400:
        raise HTTPException(status_code=401, detail="Telegram auth data expired")

    # Find or create user
    user = await user_repo.find_user_by_telegram_id(data.id)
    if not user:
        full_name = data.first_name
        if data.last_name:
            full_name = f"{data.first_name} {data.last_name}"
        user = await user_repo.create_user_from_telegram(
            telegram_id=data.id,
            name=full_name,
            username=data.username,
        )

    if user.get("is_blocked"):
        raise HTTPException(status_code=403, detail="Аккаунт заблокирован")

    token = create_access_token({"sub": user["id"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _build_user_response(user),
    }


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
        "telegram_id": user.get("telegram_id"),
        "telegram_username": user.get("telegram_username"),
    }
