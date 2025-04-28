from typing import AsyncGenerator

from sqlalchemy.orm import Session

from chat_explorer.app.db import SessionLocal  # type: ignore


async def db_session() -> AsyncGenerator[Session, None]:
    sess = SessionLocal()
    try:
        yield sess
    finally:
        sess.close()