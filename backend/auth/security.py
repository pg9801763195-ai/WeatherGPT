"""
Security and Cryptography Utilities for WeatherGPT.
Implements:
- BCRYPT password hashing & verification
- Password complexity validation
- Cryptographically secure single-use OTP generation & SHA-256 hashing
- PyJWT access token generation and extraction
- FastAPI authentication dependencies (optionalAuth & requireAuth)
"""
import os
import re
import secrets
import hashlib
import datetime
from typing import Optional, Dict, Any, Tuple
import bcrypt
import jwt
from fastapi import Request, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import AgentConfig

config = AgentConfig()
security_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hashes plaintext password using BCRYPT with configured salt rounds."""
    salt = bcrypt.gensalt(rounds=config.bcrypt_salt_rounds)
    pw_bytes = password.encode("utf-8")
    hashed_bytes = bcrypt.hashpw(pw_bytes, salt)
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plaintext password against BCRYPT hash safely."""
    try:
        pw_bytes = plain_password.encode("utf-8")
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pw_bytes, hash_bytes)
    except Exception:
        return False


def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validates password strength according to production security policies:
    - Minimum 8 characters
    - At least 1 lowercase letter
    - At least 1 uppercase letter
    - At least 1 digit or special symbol
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[a-z]", password):
        return False, "Password must include at least one lowercase letter."
    if not re.search(r"[A-Z]", password):
        return False, "Password must include at least one uppercase letter."
    if not re.search(r"[\d\W_]", password):
        return False, "Password must include at least one number or special character."
    return True, None


def generate_otp(length: int = 6) -> str:
    """Generates a cryptographically random numeric OTP."""
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(length))


def hash_otp(otp: str) -> str:
    """Hashes single-use OTP using SHA-256 for secure database storage."""
    return hashlib.sha256(otp.strip().encode("utf-8")).hexdigest()


def generate_verification_token() -> str:
    """Generates a cryptographically random single-use token upon successful OTP verification."""
    return secrets.token_urlsafe(32)


def create_access_token(
    user_id: str,
    email: str,
    role: str = "user",
    expires_delta: Optional[datetime.timedelta] = None
) -> str:
    """
    Generates a secure signed JWT access token.
    Only contains minimum required non-sensitive claims (sub, email, role, iat, exp).
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        # Default 7 days
        expire = now + datetime.timedelta(days=7)

    payload = {
        "sub": str(user_id),
        "email": email.strip().lower(),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    }
    encoded_jwt = jwt.encode(payload, config.jwt_secret, algorithm=config.jwt_algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates JWT token signature and expiration."""
    try:
        payload = jwt.decode(
            token,
            config.jwt_secret,
            algorithms=[config.jwt_algorithm]
        )
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def extract_token_from_request(request: Request) -> Optional[str]:
    """
    Extracts authentication token from either:
    1. 'Authorization: Bearer <token>' header
    2. 'access_token' HttpOnly cookie
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token:
            return token

    cookie_token = request.cookies.get("access_token")
    if cookie_token and cookie_token.strip():
        return cookie_token.strip()

    return None


async def optional_auth(request: Request) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency for endpoints that accept both guests and authenticated users.
    If valid token is present, returns user dict {'id', 'email', 'role'}.
    If token is absent or invalid, returns None without raising an error (Guest mode).
    """
    token = extract_token_from_request(request)
    if not token:
        return None

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None

    return {
        "id": payload["sub"],
        "email": payload.get("email"),
        "role": payload.get("role", "user")
    }


async def require_auth(request: Request) -> Dict[str, Any]:
    """
    FastAPI dependency enforcing strict authentication on protected endpoints.
    Raises HTTP 401 if unauthenticated or token is expired/invalid.
    """
    user = await optional_auth(request)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please log in or register to access this resource."
        )
    return user
