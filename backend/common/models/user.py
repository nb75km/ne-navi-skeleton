# backend/common/models/user.py
import uuid
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):      # “public” スキーマ
    pass

Base.metadata.schema = "public"

class User(SQLAlchemyBaseUserTableUUID, Base):
    # 追加したいプロフィール項目はここへ
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}  # ★追加すると分かりやすい
