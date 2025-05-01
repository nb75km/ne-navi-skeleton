from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import os
from sqlalchemy.engine.url import make_url



from chat_explorer.app.db import SessionLocal  # type: ignore

DATABASE_URL = os.getenv("DATABASE_URL")
sync_url = make_url(DATABASE_URL)               # → URL オブジェクト
async_url = sync_url.set(drivername="postgresql+asyncpg")
ASYNC_DATABASE_URL = DATABASE_URL.replace(
    "postgresql+psycopg2", "postgresql+asyncpg"
)

print("DEBUG ASYNC_DATABASE_URL =", ASYNC_DATABASE_URL)

# --- 既存 sync エンジン (Minutes, Chat で使用) -------------------
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

  # --- NEW: async エンジン (Auth 専用) ------------------------------

async_engine = create_async_engine(ASYNC_DATABASE_URL, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
                                                             )

async def db_session() -> AsyncGenerator[Session, None]:
    sess = SessionLocal()
    try:
        yield sess
    finally:
        sess.close()
        
# FastAPI-Users 用
async def async_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session