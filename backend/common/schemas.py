from uuid import UUID
from fastapi_users import schemas

class UserRead(schemas.BaseUser[UUID]):
    pass                       # 追加プロフィールが要るならフィールドを足す

class UserCreate(schemas.BaseUserCreate):
    pass                       # email & password は既定で必須

class UserUpdate(schemas.BaseUserUpdate):      # 空継承で OK
    """ユーザー更新用スキーマ（全フィールド optional）"""
    pass