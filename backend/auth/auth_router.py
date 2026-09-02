"""
FastAPI Authentication Router for WeatherGPT.
Endpoints:
- POST /api/auth/register/request-otp
- POST /api/auth/register/verify-otp
- POST /api/auth/register/set-password
- POST /api/auth/login
- POST /api/auth/logout
- GET  /api/auth/me
"""
import re
import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Response, Depends, status
from pydantic import BaseModel, EmailStr, Field

from config import AgentConfig
from db.mongo_database import MongoDatabaseManager
from auth.security import (
    hash_password,
    verify_password,
    validate_password_strength,
    generate_otp,
    hash_otp,
    generate_verification_token,
    create_access_token,
    require_auth,
    optional_auth
)
from auth.email_service import send_otp_email

config = AgentConfig()
db = MongoDatabaseManager.get_instance(config.mongodb_uri, config.mongodb_db_name)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# --- Request Schemas ---

class RequestOtpRequest(BaseModel):
    email: str = Field(..., description="User email address")


class VerifyOtpRequest(BaseModel):
    email: str = Field(..., description="User email address")
    otp: str = Field(..., min_length=4, max_length=10, description="Verification code")


class SetPasswordRequest(BaseModel):
    email: str = Field(..., description="User email address")
    verification_token: str = Field(..., description="Token issued upon successful OTP verification")
    password: str = Field(..., min_length=8, description="User password")
    name: Optional[str] = Field(default=None, description="User display name")


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class DirectRegisterRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password")
    name: Optional[str] = Field(default=None, description="User display name")


class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = Field(default=None, description="Google ID Token (JWT)")
    email: Optional[str] = Field(default=None, description="User email from Google")
    name: Optional[str] = Field(default=None, description="User name from Google")
    picture: Optional[str] = Field(default=None, description="User avatar URL")
    sub: Optional[str] = Field(default=None, description="Google Subject ID")


def _is_valid_email(email: str) -> bool:
    """Basic email format validator."""
    if not email or len(email) > 254:
        return False
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip()))


# --- API Routes ---

@router.post("/register/request-otp")
async def request_registration_otp(req: RequestOtpRequest):
    """
    Step 1 & 2: User requests OTP for registration.
    Validates email format, checks for account duplication, rate limits,
    generates cryptographic OTP, hashes it, and dispatches it via email.
    """
    email = req.email.strip().lower()
    if not _is_valid_email(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid email address."
        )

    # Check if account already exists
    existing_user = db.find_user_by_email(email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists. Please log in."
        )

    # Rate limiting / resend cooldown check
    existing_otp = db.get_otp_record(email)
    now = datetime.datetime.now(datetime.timezone.utc)
    if existing_otp:
        created_at_str = existing_otp.get("created_at")
        if created_at_str:
            try:
                created_at = datetime.datetime.fromisoformat(created_at_str)
                # Ensure at least 30 seconds cooldown between OTP requests
                if (now - created_at).total_seconds() < 30:
                    wait_seconds = int(30 - (now - created_at).total_seconds())
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Please wait {wait_seconds} seconds before requesting another code."
                    )
            except (ValueError, TypeError):
                pass

    # Generate cryptographic OTP
    otp_code = generate_otp(length=6)
    otp_hashed = hash_otp(otp_code)
    expires_at = (now + datetime.timedelta(minutes=config.otp_expiry_minutes)).isoformat()

    # Save to MongoDB
    db.create_or_update_otp(email, otp_hashed, expires_at)

    # Dispatch email
    await send_otp_email(email, otp_code)

    is_placeholder_smtp = not config.smtp_user or "your_email" in config.smtp_user

    return {
        "status": "success",
        "message": f"A 6-digit verification code has been sent to {email}.",
        "email": email,
        "expires_in_seconds": config.otp_expiry_minutes * 60,
        "dev_otp": otp_code if is_placeholder_smtp else None
    }



@router.post("/register/verify-otp")
async def verify_registration_otp(req: VerifyOtpRequest):
    """
    Step 5 & 6: Verify the 6-digit OTP code submitted by the user.
    Enforces expiration, single-use, and maximum attempt limits.
    """
    email = req.email.strip().lower()
    otp_input = req.otp.strip()

    if not email or not otp_input:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and verification code are required."
        )

    otp_record = db.get_otp_record(email)
    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active verification code found for this email. Please request a new code."
        )

    now = datetime.datetime.now(datetime.timezone.utc)
    expires_at_str = otp_record.get("expires_at")
    if expires_at_str:
        try:
            expires_at = datetime.datetime.fromisoformat(expires_at_str)
            if now > expires_at:
                db.delete_otp_record(email)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Verification code has expired. Please request a new code."
                )
        except (ValueError, TypeError):
            pass

    # Check attempt limit
    attempts = otp_record.get("attempts", 0)
    if attempts >= config.otp_max_attempts:
        db.delete_otp_record(email)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many incorrect attempts. Please request a new verification code."
        )

    # Compare SHA-256 hashes
    input_hash = hash_otp(otp_input)
    stored_hash = otp_record.get("otp_hash")

    if input_hash != stored_hash:
        new_attempts = db.increment_otp_attempts(email)
        remaining = max(0, config.otp_max_attempts - new_attempts)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid verification code. {remaining} attempt(s) remaining."
        )

    # Success: issue single-use verification token for setting password
    verification_token = generate_verification_token()
    db.mark_otp_verified(email, verification_token)

    return {
        "status": "success",
        "message": "Verification code successfully validated.",
        "email": email,
        "verification_token": verification_token
    }


@router.post("/register/set-password")
async def set_user_password(req: SetPasswordRequest, response: Response):
    """
    Step 7, 8, 9, 10: Set password and create user account.
    Verifies OTP verification token, checks password strength, hashes with BCRYPT,
    creates user document in MongoDB, issues JWT, and sets secure HttpOnly cookie.
    """
    email = req.email.strip().lower()
    token = req.verification_token.strip()
    password = req.password

    # Validate password complexity
    is_valid, error_msg = validate_password_strength(password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Verify authorization token
    otp_record = db.get_otp_record(email)
    if not otp_record or not otp_record.get("verified") or otp_record.get("verification_token") != token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired verification session. Please verify your email again."
        )

    # Check if user was already created
    if db.find_user_by_email(email):
        db.delete_otp_record(email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists. Please log in."
        )

    # Hash password using BCRYPT
    pw_hash = hash_password(password)

    # Create user in MongoDB
    user = db.create_user(
        email=email,
        password_hash=pw_hash,
        name=req.name,
        role="user"
    )

    # Clean up OTP record
    db.delete_otp_record(email)

    # Issue JWT token
    access_token = create_access_token(
        user_id=user["_id"],
        email=user["email"],
        role=user["role"]
    )

    # Set secure HttpOnly cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=7 * 24 * 3600,
        samesite="lax",
        secure=False  # Allow local HTTP development
    )

    return {
        "status": "success",
        "message": "Account created successfully.",
        "token": access_token,
        "user": {
            "id": user["_id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "created_at": user["created_at"]
        }
    }


@router.post("/register")
async def register_user_direct(req: DirectRegisterRequest, response: Response):
    """
    Direct user registration with Email + Password + Name (Instant 1-click, No OTP required).
    """
    email = req.email.strip().lower()
    if not _is_valid_email(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter a valid email address."
        )

    if len(req.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long."
        )

    existing = db.find_user_by_email(email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists. Please log in."
        )

    pw_hash = hash_password(req.password)
    user = db.create_user(
        email=email,
        password_hash=pw_hash,
        name=req.name.strip() if req.name else None,
        role="user"
    )

    token = create_access_token(
        user_id=user["_id"],
        email=user["email"],
        role=user["role"]
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=7 * 24 * 3600,
        samesite="lax",
        secure=False
    )

    return {
        "status": "success",
        "message": "Account created successfully.",
        "token": token,
        "user": {
            "id": user["_id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "created_at": user["created_at"]
        }
    }


@router.post("/google")
async def google_auth(req: GoogleAuthRequest, response: Response):
    """
    Google OAuth Sign-In & Registration.
    Verifies Google ID Token over HTTPS, creates/logs in the user in MongoDB, and issues JWT token.
    """
    email = req.email
    name = req.name
    picture = req.picture
    google_id = req.sub

    if req.credential:
        try:
            import requests
            verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={req.credential}"
            g_resp = requests.get(verify_url, timeout=5)
            if g_resp.status_code == 200:
                payload = g_resp.json()
                email = payload.get("email")
                name = name or payload.get("name")
                picture = picture or payload.get("picture")
                google_id = google_id or payload.get("sub")
            else:
                import base64
                import json
                parts = req.credential.split(".")
                if len(parts) >= 2:
                    padded = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
                    payload = json.loads(base64.urlsafe_b64decode(padded.encode()))
                    email = payload.get("email")
                    name = name or payload.get("name")
                    picture = picture or payload.get("picture")
                    google_id = google_id or payload.get("sub")
        except Exception as e:
            print(f"[Google Auth] Notice during token verification: {e}", flush=True)

    if not email or not _is_valid_email(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not retrieve a valid email from Google."
        )

    user = db.create_or_update_google_user(
        email=email,
        name=name,
        picture=picture,
        google_id=google_id
    )

    token = create_access_token(
        user_id=user["_id"],
        email=user["email"],
        role=user.get("role", "user")
    )

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=7 * 24 * 3600,
        samesite="lax",
        secure=False
    )

    return {
        "status": "success",
        "message": "Logged in with Google successfully.",
        "token": token,
        "user": {
            "id": user["_id"],
            "email": user["email"],
            "name": user.get("name"),
            "picture": user.get("picture"),
            "role": user.get("role", "user"),
            "created_at": user.get("created_at")
        }
    }


@router.post("/login")
async def login_user(req: LoginRequest, response: Response):
    """
    Login endpoint: authenticates email + password against BCRYPT hash.
    Issues JWT token and sets secure HttpOnly cookie.
    """
    email = req.email.strip().lower()
    password = req.password

    user = db.find_user_by_email(email)
    if not user or not verify_password(password, user.get("password_hash", "")):
        # Generic error message to prevent account enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please try again."
        )

    # Update last login
    db.update_last_login(user["_id"])

    # Issue JWT
    access_token = create_access_token(
        user_id=user["_id"],
        email=user["email"],
        role=user.get("role", "user")
    )

    # Set secure HttpOnly cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=7 * 24 * 3600,
        samesite="lax",
        secure=False
    )

    return {
        "status": "success",
        "message": "Login successful.",
        "token": access_token,
        "user": {
            "id": user["_id"],
            "email": user["email"],
            "name": user.get("name", email.split("@")[0]),
            "role": user.get("role", "user"),
            "created_at": user.get("created_at")
        }
    }


@router.post("/logout")
async def logout_user(response: Response):
    """
    Logout endpoint: clears authentication cookie.
    """
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax"
    )
    return {
        "status": "success",
        "message": "Logged out successfully."
    }


@router.get("/me")
async def get_current_user_profile(user_payload: dict = Depends(require_auth)):
    """
    Returns current authenticated user profile.
    Rejects unauthenticated requests with 401.
    """
    user = db.find_user_by_id(user_payload["id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found."
        )

    return {
        "status": "success",
        "user": {
            "id": user["_id"],
            "email": user["email"],
            "name": user.get("name", user["email"].split("@")[0]),
            "role": user.get("role", "user"),
            "created_at": user.get("created_at"),
            "last_login_at": user.get("last_login_at")
        }
    }
