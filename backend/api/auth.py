"""
Authentication API — /auth/*
Implements: register, login, logout, password reset, get current user
"""
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from backend.config import settings
from backend.database.mongo import get_db
from backend.models.schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
)

router = APIRouter()
bearer_scheme = HTTPBearer()

ALGORITHM = "HS256"


# ── Token helpers ─────────────────────────────────────────────────────────────

def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRY_HOURS)
    payload = {"sub": user_id, "role": role, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


# ── Auth dependency ───────────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    payload = decode_token(credentials.credentials)
    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
    if not user or not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest):
    db = get_db()
    if await db.users.find_one({"email": body.email}):
        raise HTTPException(status_code=409, detail="Email already registered")

    hashed = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()
    result = await db.users.insert_one({
        "name": body.name,
        "email": body.email,
        "password_hash": hashed,
        "role": "user",
        "created_at": datetime.utcnow(),
        "last_login": None,
        "is_active": True,
        "reset_token": None,
        "reset_token_expiry": None,
    })

    user_id = str(result.inserted_id)
    token = create_access_token(user_id, "user")
    return TokenResponse(token=token, user_id=user_id, name=body.name, role="user")


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    db = get_db()
    user = await db.users.find_one({"email": body.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not bcrypt.checkpw(body.password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account deactivated")

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.utcnow()}},
    )

    user_id = str(user["_id"])
    token = create_access_token(user_id, user.get("role", "user"))
    return TokenResponse(
        token=token,
        user_id=user_id,
        name=user["name"],
        role=user.get("role", "user"),
    )


@router.post("/logout")
async def logout(user: dict = Depends(get_current_user)):
    # JWT is stateless — client drops the token. Server-side blacklist optional.
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {
        "user_id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "role": user.get("role", "user"),
        "created_at": user.get("created_at"),
    }


@router.post("/reset-password")
async def request_password_reset(body: PasswordResetRequest):
    db = get_db()
    user = await db.users.find_one({"email": body.email})
    # Always return 200 to prevent email enumeration
    if not user:
        return {"message": "If that email is registered, a reset link has been sent"}

    import secrets
    token = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(hours=1)

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"reset_token": token, "reset_token_expiry": expiry}},
    )

    # In production: send email via SMTP with reset link
    # For dev: return token directly (remove in production)
    if settings.ENVIRONMENT == "development":
        return {"message": "Reset token generated", "dev_token": token}
    return {"message": "If that email is registered, a reset link has been sent"}


@router.put("/reset-password/confirm")
async def confirm_password_reset(body: PasswordResetConfirm):
    db = get_db()
    user = await db.users.find_one({"reset_token": body.token})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    if user.get("reset_token_expiry") and datetime.utcnow() > user["reset_token_expiry"]:
        raise HTTPException(status_code=400, detail="Reset token has expired")

    hashed = bcrypt.hashpw(body.new_password.encode(), bcrypt.gensalt()).decode()
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "password_hash": hashed,
            "reset_token": None,
            "reset_token_expiry": None,
        }},
    )
    return {"message": "Password reset successfully"}
