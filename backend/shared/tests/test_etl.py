# backend/tests/test_etl.py
import json
from datetime import datetime, timezone

import pytest
import responses

from shared.etl_dify import sync_dify
from chat_explorer.app.db import SessionLocal, models as M


@pytest.fixture(autouse=True)
def _freeze_time(monkeypatch):
    """
    OpenAI Embedding モデルで日時を使う場合に備え、固定の now() を返す。
    今回のテストでは不要かもしれませんが、将来の non-determinism を防ぎます。
    """
    monkeypatch.setattr(
        datetime, "utcnow", lambda: datetime(2025, 4, 27, 12, 0, tzinfo=timezone.utc)
    )


@responses.activate
def test_etl_inserts_messages_and_prints(capfd, db_engine):
    """
    • /v1/conversations → 1 件返し、その JSON を print で確認  
    • /v1/messages → 2 件返して DB に書けるか検証
    """
    base_url = "https://api.dify.ai/v1"

    # --- mock conversations -------------------------------------------------
    conv_json = {
        "id": "1",
        "name": "Demo Conversation",
        "created_at": "2025-04-25T00:00:00Z",
    }
    responses.get(
        f"{base_url}/conversations",
        json={"data": [conv_json], "has_more": False},
        status=200,
    )

    # --- mock messages (pagination無し) --------------------------------------
    msg_json = {
        "data": [
            {
                "id": "10",
                "query": "こんにちは",
                "created_at": "2025-04-25T00:01:00Z",
            },
            {
                "id": "11",
                "answer": "こんにちは！ご用件は？",
                "created_at": "2025-04-25T00:01:05Z",
            },
        ],
        "has_more": False,
    }
    responses.get(
        f"{base_url}/messages",
        json=msg_json,
        status=200,
    )

    # --- run ETL -------------------------------------------------------------
    sync_dify()  # Celery task だが単発実行

    # デバッグ: 会話 JSON を標準出力に出す
    print("DEBUG conversations:", json.dumps([conv_json], indent=2, ensure_ascii=False))

    # --- assert DB state -----------------------------------------------------
    sess = SessionLocal()
    assert sess.query(M.Conversation).count() == 1
    assert sess.query(M.Message).count() == 2
    sess.close()

    # --- capture stdout ------------------------------------------------------
    captured = capfd.readouterr()
    assert "DEBUG conversations" in captured.out
    assert '"Demo Conversation"' in captured.out