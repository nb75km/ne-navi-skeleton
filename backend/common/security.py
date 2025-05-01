"""
認証・ユーザー依存性をまとめた共通モジュール。
FastAPI インスタンスを **生成しない** ので、
各サービス(app/main.py) で自由にルータをマウント出来る。
"""

import os, uuid
from typing import AsyncGenerator

from fastapi import Depends
from fastapi_users import FastAPIUsers, UUIDIDMixin, BaseUserManager
from fastapi_users.authentication import (
    CookieTransport,
    JWTStrategy,
    AuthenticationBackend,
)
from fastapi_users.db import SQLAlchemyUserDatabase

from .deps import db_session  # :contentReference[oaicite:4]{index=4}
from .models.user import User  # :contentReference[oaicite:5]{index=5}

# ------------------------------------------------------------------ #
# JWT / Cookie backend
# ------------------------------------------------------------------ #

SECRET = os.getenv("SECRET_KEY")
if not SECRET:
    raise RuntimeError("SECRET_KEY env var is required for JWT auth")

cookie_transport = CookieTransport(cookie_name="access", cookie_max_age=60 * 60)

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=60 * 60)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

# ------------------------------------------------------------------ #
# DB bridge
# ------------------------------------------------------------------ #

async def get_user_db(
    session=Depends(db_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    """FastAPI-Users が要求する DB アダプタを返す。"""
    yield SQLAlchemyUserDatabase(session, User)

# ------------------------------------------------------------------ #
# User manager & public dependencies
# ------------------------------------------------------------------ #

class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)

fastapi_users: FastAPIUsers[User, uuid.UUID] = FastAPIUsers(
    get_user_manager,
    [auth_backend],
)

# ★ 他モジュールが import しやすい依存性
current_user = fastapi_users.current_user()
current_active_user = fastapi_users.current_user(active=True)

__all__ = (
    "auth_backend",
    "fastapi_users",
    "current_user",
    "current_active_user",
)