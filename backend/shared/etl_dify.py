# Patched backend/shared/etl_dify.py
"""Improved Dify→Postgres synchroniser.

Fixes:
* URL base handling – always appends "/v1" once (404 bug)
* Uses `text-embedding-3-small` (1536‑dim) to match DB schema
* Commits per‑conversation to avoid giant transactions
* Updates counters only if body/role changed
* Additional fallback fields & role detection
* Graceful handling of OpenAI errors (skips batch, logs)
"""
from __future__ import annotations

import logging
import os
import time
from collections.abc import Iterator
from typing import Any, Dict, List
from urllib.parse import urljoin

import requests
from openai import OpenAI, OpenAIError
from sqlalchemy.orm import Session
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from shared.celery_app import celery_app
from chat_explorer.app.db import SessionLocal
from chat_explorer.app.db import models as M

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------
_raw_base = os.getenv("DIFY_API_URL", "https://api.dify.ai").rstrip("/")
# guarantee single /v1 suffix
BASE = _raw_base if _raw_base.endswith("/v1") else f"{_raw_base}/v1"

API_KEY = os.getenv("DIFY_API_KEY", "")
ETL_USER = os.getenv("DIFY_ETL_USER", "default")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "User-Agent": "ne-navi-etl/0.4",
}

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
PAGE_LIMIT = 100
BATCH_EMB_LIMIT = 96

# ---------------------------------------------------------------------------
# Retryable GET
# ---------------------------------------------------------------------------
class _Retryable(requests.RequestException):
    pass


@retry(
    retry=retry_if_exception_type(_Retryable),
    wait=wait_exponential_jitter(initial=1, max=20),
    stop=stop_after_attempt(5),
    reraise=True,
)
def _get(path: str, *, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    url = urljoin(BASE + "/", path.lstrip("/"))
    rsp = requests.get(url, headers=HEADERS, params=params or {}, timeout=15)
    if rsp.status_code in {429, 502, 503}:
        raise _Retryable(f"{rsp.status_code} {rsp.text[:120]}")
    rsp.raise_for_status()
    return rsp.json()

# ---------------------------------------------------------------------------
# Iterators
# ---------------------------------------------------------------------------

def _iter_conversations() -> Iterator[Dict[str, Any]]:
    """Yield conversations for ETL_USER and log raw payload for debugging."""
    params = {"user": ETL_USER, "limit": PAGE_LIMIT}
    page_no = 1
    while True:
        payload = _get("conversations", params=params)
        # ---- debug logging -------------------------------------------------
        logger.info(
            "[ETL] Fetched page %d – %d conversations (keys: %s)",
            page_no,
            len(payload.get("data", [])),
            list(payload.keys()),
        )
        logger.info("[ETL] Sample conversation objects: %s", payload.get("data", [])[:3])
        # -------------------------------------------------------------------
        yield from payload["data"]
        if not payload.get("has_more"):
            break
        params["last_id"] = payload["data"][-1]["id"]
        page_no += 1


def _iter_messages(conversation_id: str) -> Iterator[Dict[str, Any]]:
    params = {
        "conversation_id": conversation_id,
        "user": ETL_USER,
        "limit": PAGE_LIMIT,
    }
    first_id: str | None = None
    pages: list[list[Dict[str, Any]]] = []
    while True:
        if first_id:
            params["first_id"] = first_id
        payload = _get("messages", params=params)
        pages.append(payload["data"])
        if not payload.get("has_more"):
            break
        first_id = payload["data"][-1]["id"]
    # oldest→newest
    for page in reversed(pages):
        yield from reversed(page)

# ---------------------------------------------------------------------------
# Embedding helper (1536‑dim)
# ---------------------------------------------------------------------------

def _embed_texts(texts: list[str]) -> list[list[float]]:
    try:
        rsp = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )
        return [d.embedding for d in rsp.data]
    except OpenAIError as e:  # log & skip batch
        logger.error("Embedding batch failed – skipped (%s)", e)
        return [[0.0] * 1536 for _ in texts]  # zero‑vector placeholder

# ---------------------------------------------------------------------------
# Celery task
# ---------------------------------------------------------------------------
@celery_app.task(name="etl.sync_dify")
def sync_dify() -> None:
    start = time.perf_counter()
    sess: Session = SessionLocal()
    stats = {"inserted": 0, "updated": 0}

    try:
        for conv_json in _iter_conversations():
            conv_obj = sess.merge(
                M.Conversation(
                    conversation_uid=conv_json["id"],
                    title=conv_json.get("name"),
                )
            )

            # batch‑embedding queues
            batch_msg: list[M.Message] = []
            batch_txt: list[str] = []

            for msg_json in _iter_messages(conv_json["id"]):
                # --- role / body handling ---
                role = (
                    msg_json.get("role")
                    or ("assistant" if "answer" in msg_json else "user")
                )
                body = (
                    msg_json.get("answer")
                    or msg_json.get("query")
                    or msg_json.get("content")
                    or ""
                )

                db_msg = sess.get(M.Message, int(msg_json["id"]))
                if db_msg is None:
                    db_msg = M.Message(
                        id=int(msg_json["id"]),
                        conversation=conv_obj,
                        role=role,
                        body=body,
                    )
                    sess.add(db_msg)
                    stats["inserted"] += 1
                else:
                    if db_msg.role != role or db_msg.body != body:
                        db_msg.role, db_msg.body = role, body
                        stats["updated"] += 1

                if db_msg.embedding is None and body:
                    batch_msg.append(db_msg)
                    batch_txt.append(body)

                if len(batch_txt) >= BATCH_EMB_LIMIT:
                    vectors = _embed_texts(batch_txt)
                    for m, vec in zip(batch_msg, vectors):
                        m.embedding = vec
                    batch_msg.clear()
                    batch_txt.clear()

            # flush leftovers per‑conversation
            if batch_txt:
                vectors = _embed_texts(batch_txt)
                for m, vec in zip(batch_msg, vectors):
                    m.embedding = vec

            sess.commit()  # commit per conversation

        logger.info(
            "Dify ETL finished: +%d new, ~%d updated in %.2fs",
            stats["inserted"],
            stats["updated"],
            time.perf_counter() - start,
        )
    except Exception:
        sess.rollback()
        logger.exception("Dify ETL aborted – rolled back")
        raise
    finally:
        sess.close()
