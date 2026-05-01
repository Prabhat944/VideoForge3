from fastapi import APIRouter, Depends, HTTPException

from core.db import db
from core.deps import (
    create_jwt, hash_password, verify_password,
    get_current_user, to_user_public, now_iso,
)
from core.schemas import UserRegister, UserLogin, UserPublic, AuthResponse
import uuid

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=AuthResponse)
async def register(payload: UserRegister):
    existing = await db.users.find_one({"email": payload.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_doc = {
        "id": str(uuid.uuid4()),
        "email": payload.email.lower(),
        "full_name": payload.full_name,
        "password_hash": hash_password(payload.password),
        "plan": "free",
        "credits": 100,
        "created_at": now_iso(),
    }
    await db.users.insert_one(user_doc)
    token = create_jwt(user_doc["id"])
    return AuthResponse(token=token, user=to_user_public(user_doc))


@router.post("/auth/login", response_model=AuthResponse)
async def login(payload: UserLogin):
    user = await db.users.find_one({"email": payload.email.lower()})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_jwt(user["id"])
    return AuthResponse(token=token, user=to_user_public(user))


@router.get("/auth/me", response_model=UserPublic)
async def me(current=Depends(get_current_user)):
    return to_user_public(current)
