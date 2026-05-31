"""
SECURITY TESTS

Covers bcrypt password hash/verify and JWT create/decode,
including expired and tampered tokens.
"""

from datetime import timedelta

from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


# ─────────────────────────────────────────────────────────────────────────────
# 12. Password hash and verify
# ─────────────────────────────────────────────────────────────────────────────
def test_security_password_hash_and_verify_work_correctly():
    hashed = hash_password("SecurePass2025!")

    assert hashed != "SecurePass2025!"          # stored in bcrypt format
    assert hashed.startswith("$2b$")            # bcrypt signature

    assert verify_password("SecurePass2025!", hashed) is True
    assert verify_password("WrongPassword",   hashed) is False
    assert verify_password("",                hashed) is False


# ─────────────────────────────────────────────────────────────────────────────
# 13. JWT: valid token decodes correctly; expired and tampered tokens return None
# ─────────────────────────────────────────────────────────────────────────────
def test_security_jwt_valid_token_decodes_and_expired_tampered_tokens_return_none():
    # Valid token
    token = create_access_token({"sub": "507f1f77bcf86cd799439011"})
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "507f1f77bcf86cd799439011"

    # Expired token (negative delta → already past)
    expired = create_access_token({"sub": "abc"}, expires_delta=timedelta(seconds=-1))
    assert decode_token(expired) is None

    # Tampered / garbage token
    assert decode_token("eyJhbGciOiJIUzI1NiJ9.fake.badsig") is None
    assert decode_token("not.a.jwt") is None
