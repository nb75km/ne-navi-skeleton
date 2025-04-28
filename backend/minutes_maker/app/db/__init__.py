"""
minutes_maker.app.db package
———————————————
* エンジン / SessionLocal を提供
* `models` サブモジュールを属性としてエクスポート
  （`from app.db import models as M` が動くように）
"""
from __future__ import annotations

import os
from importlib import import_module

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------------------------
# ① まず接続情報と SessionLocal を定義（← stt_router がここを欲しがる）
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://app:app@postgres:5432/app",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)

# ---------------------------------------------------------------------------
# ② 次に ORM モデルを読み込み、モジュール属性にバインド
#    ※ 循環防止のため import_module を後ろに置く
# ---------------------------------------------------------------------------
models = import_module(__name__ + ".models")        # type: ignore[attr-defined]
Base = models.Base                                  # re-export for Alembic etc.

__all__: list[str] = ["engine", "SessionLocal", "models", "Base"]
