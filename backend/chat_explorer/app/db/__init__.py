# backend/chat_explorer/app/db/__init__.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base  # ← 2. で定義

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://app:app@postgres:5432/app",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)

__all__ = ["engine", "SessionLocal", "Base"]