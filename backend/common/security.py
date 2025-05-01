from fastapi_users import FastAPIUsers, UUIDIDMixin, BaseUserManager
from fastapi_users.authentication import CookieTransport, JWTStrategy, AuthenticationBackend
from fastapi import FastAPI
import uuid, os

SECRET = os.getenv("SECRET_KEY")

cookie_transport = CookieTransport(cookie_name="access", cookie_max_age=3600)
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="cookie",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret   = SECRET
    # on_after_register などをオーバーライドしてログ取りも可

async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,                  # 既に実装済みの UserManager
    [auth_backend],
)

app = FastAPI()

# ★ サインアップルータを追加
from common.schemas import UserRead, UserCreate
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),  # POST /auth/register
    prefix="/auth",
    tags=["auth"],
)
# ★ ログイン／ログアウトも標準ルータを付ける
app.include_router(
    fastapi_users.get_auth_router(auth_backend),              # /auth/login, /auth/logout
    prefix="/auth",
    tags=["auth"],
)
# 認証必須で現在のユーザーを返す
app.include_router(
    fastapi_users.get_users_router(UserRead, UserCreate),
    prefix="/users",
    tags=["users"],
)
