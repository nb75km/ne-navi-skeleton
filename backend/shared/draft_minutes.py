"""Generate meeting-minutes draft from a transcript via OpenAI (model selectable)."""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import openai
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from shared.celery_app import celery_app
from minutes_maker.app import SessionLocal
from minutes_maker.app.db import models as M

openai.api_key = os.getenv("OPENAI_API_KEY")

_SYSTEM_PROMPT = (
    "You are an expert secretary. Summarise the following meeting transcript "
    "into Japanese markdown with sections: 概要 / 決定事項 / ToDo."
)


def _fetch_transcript(sess: Session, transcript_id: int) -> str:
    (txt,) = sess.execute(
        select(M.Transcript.content).where(M.Transcript.id == transcript_id)
    ).one()
    return txt


def _store_new_version(sess: Session, transcript_id: int, markdown: str):
    next_no: int = (
        sess.execute(
            select(
                func.coalesce(func.max(M.MinutesVersion.version_no), 0) + 1
            ).where(M.MinutesVersion.transcript_id == transcript_id)
        ).scalar_one()
    )
    mv = M.MinutesVersion(
        transcript_id=transcript_id,
        version_no=next_no,
        markdown=markdown,
        created_by="draft_bot",
        created_at=datetime.utcnow(),
    )
    sess.add(mv)
    sess.commit()


@celery_app.task(name="minutes.draft.generate")
def generate_minutes_draft(
    transcript_id: int,
    model: str = "gpt-4o-mini",
) -> dict[str, Any]:
    """Celery entry point. Returns {'status': 'ok'} on success."""
    sess = SessionLocal()
    try:
        content = _fetch_transcript(sess, transcript_id)
        if not content:
            raise ValueError("transcript not found")

        completion = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": content[:32_768]},
            ],
            temperature=0.4,
        )
        markdown = completion.choices[0].message.content  # type: ignore[index]
        _store_new_version(sess, transcript_id, markdown)
        return {"status": "ok", "model": model}
    finally:
        sess.close()
