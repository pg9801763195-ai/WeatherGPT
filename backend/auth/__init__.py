"""Authentication and history package for WeatherGPT."""
from auth.security import (
    hash_password,
    verify_password,
    validate_password_strength,
    generate_otp,
    hash_otp,
    create_access_token,
    decode_access_token,
    require_auth,
    optional_auth
)
from auth.auth_router import router as auth_router
from auth.history_router import router as history_router

__all__ = [
    "hash_password",
    "verify_password",
    "validate_password_strength",
    "generate_otp",
    "hash_otp",
    "create_access_token",
    "decode_access_token",
    "require_auth",
    "optional_auth",
    "auth_router",
    "history_router"
]
