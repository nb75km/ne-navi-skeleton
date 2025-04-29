# ---------------------------------------------------------------------------
# backend/minutes_maker/app/api/minutes_versions_router.py
# ---------------------------------------------------------------------------
"""CRUD + diff/rollback + AI‑edit for *minutes_versions*.

This router now supports:
* **GET   /api/minutes_versions?transcript_id=** – list all versions (latest‑first)
* **POST  /api/minutes_versions?transcript_id=** – create a new version by hand (Markdown body)
* **GET   /api/minutes_versions/{vid}** – fetch single version
* **GET   /api/minutes_versions/{from_id}/diff/{to_id}?html=1** – diff two versions (HTML or unified)
* **POST  /api/minutes_versions/{vid}/rollback** – copy an old version as the newest one
* **POST  /api/minutes_versions/{vid}/ai_edit** – generate a new edited version via OpenAI­‑Chat

The endpoints unblock **version switching** and **AI based editing** in the React
front‑end.  They return compact JSON that the existing SWR hooks can consume.
"""
from __future__ import annotations

from datetime import datetime
from difflib import HtmlDiff, unified_diff

from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from openai import OpenAI

from ..db import models as M
from .. import SessionLocal

router = APIRouter(prefix="/api", tags=["minutes-versions"])

oai = OpenAI()  # requires OPENAI_API_KEY in env

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

def get_db() -> Session:  # pragma: no cover – tiny helper
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class MinutesVersionIn(BaseModel):
    markdown: str = Field(..., min_length=10)
    created_by: str = "ui_user"


class MinutesVersionOut(BaseModel):
    id: int
    transcript_id: int
    version_no: int
    markdown: str
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class DiffOut(BaseModel):
    from_id: int
    to_id: int
    diff: str  # HTML table or unified‑diff string depending on query


class AIEditIn(BaseModel):
    instruction: str = Field(..., min_length=5, description="e.g. 『ToDoを抽出し箇条書きに』")
    model: str = "gpt-4o-mini"
    created_by: str = "ai_editor"

# ---------------------------------------------------------------------------
# Routes – list & create
# ---------------------------------------------------------------------------

@router.get("/minutes_versions", response_model=list[MinutesVersionOut])
def list_versions(
    transcript_id: int = Query(..., description="Filter by transcript"),
    db: Session = Depends(get_db),
):
    """Return *all* versions of the given transcript, latest first."""
    stmt = (
        select(M.MinutesVersion)
        .where(M.MinutesVersion.transcript_id == transcript_id)
        .order_by(M.MinutesVersion.version_no.desc())
    )
    return db.scalars(stmt).all()


@router.post(
    "/minutes_versions",
    response_model=MinutesVersionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_version(
    body: MinutesVersionIn,
    transcript_id: int = Query(..., description="Parent transcript id"),
    db: Session = Depends(get_db),
):
    """Manually create a new minutes version (e.g. from the editor *Save* button)."""
    next_no: int = (
        db.execute(
            select(func.coalesce(func.max(M.MinutesVersion.version_no), 0) + 1).where(
                M.MinutesVersion.transcript_id == transcript_id
            )
        ).scalar_one()
    )

    mv = M.MinutesVersion(
        transcript_id=transcript_id,
        version_no=next_no,
        markdown=body.markdown,
        created_by=body.created_by,
        created_at=datetime.utcnow(),
    )
    db.add(mv)
    db.commit()
    db.refresh(mv)
    return mv

# ---------------------------------------------------------------------------
# Routes – read single / diff / rollback
# ---------------------------------------------------------------------------


@router.get("/minutes_versions/{vid}", response_model=MinutesVersionOut)
def get_version(vid: int, db: Session = Depends(get_db)):
    mv = db.get(M.MinutesVersion, vid)
    if not mv:
        raise HTTPException(status_code=404, detail="Version not found")
    return mv


@router.get("/minutes_versions/{from_id}/diff/{to_id}", response_model=DiffOut)
def diff_versions(
    from_id: int,
    to_id: int,
    html: bool = Query(True, description="Return HTML table if true, unified diff if false"),
    n: int = Query(3, ge=0, le=10, description="Context lines for unified diff"),
    db: Session = Depends(get_db),
):
    """Compute diff between two versions.

    *When* `html=true` the response is an HTML `<table>` suitable for direct
    insertion; otherwise it is a plain unified‑diff string.
    """
    v1 = db.get(M.MinutesVersion, from_id)
    v2 = db.get(M.MinutesVersion, to_id)
    if v1 is None or v2 is None:
        raise HTTPException(status_code=404, detail="One of the versions not found")

    if html:
        diff_str = HtmlDiff(wrapcolumn=80).make_table(
            v1.markdown.splitlines(),
            v2.markdown.splitlines(),
            fromdesc=f"v{v1.version_no}",
            todesc=f"v{v2.version_no}",
            context=True,
            numlines=n,
        )
    else:
        diff_str = "\n".join(
            unified_diff(
                v1.markdown.splitlines(),
                v2.markdown.splitlines(),
                fromfile=f"v{v1.version_no}",
                tofile=f"v{v2.version_no}",
                n=n,
            )
        )
    return {"from_id": from_id, "to_id": to_id, "diff": diff_str}


@router.post(
    "/minutes_versions/{vid}/rollback",
    response_model=MinutesVersionOut,
    status_code=status.HTTP_201_CREATED,
)
def rollback_version(
    vid: int,
    created_by: str = Query("rollback", description="username recorded in new version"),
    db: Session = Depends(get_db),
):
    """Clone an old version as *NEW* latest one (non‑destructive rollback)."""
    src = db.get(M.MinutesVersion, vid)
    if src is None:
        raise HTTPException(status_code=404, detail="Version not found")

    next_no: int = (
        db.execute(
            select(func.coalesce(func.max(M.MinutesVersion.version_no), 0) + 1).where(
                M.MinutesVersion.transcript_id == src.transcript_id
            )
        ).scalar_one()
    )

    mv = M.MinutesVersion(
        transcript_id=src.transcript_id,
        version_no=next_no,
        markdown=src.markdown,
        created_by=created_by,
        created_at=datetime.utcnow(),
    )
    db.add(mv)
    db.commit()
    db.refresh(mv)
    return mv

# ---------------------------------------------------------------------------
# Routes – AI edit
# ---------------------------------------------------------------------------

@router.post(
    "/minutes_versions/{vid}/ai_edit",
    response_model=MinutesVersionOut,
    status_code=status.HTTP_201_CREATED,
)
def ai_edit_version(
    vid: int,
    body: AIEditIn,
    db: Session = Depends(get_db),
):
    """Let GPT polish or transform the minutes and store as a new version."""
    mv = db.get(M.MinutesVersion, vid)
    if mv is None:
        raise HTTPException(status_code=404, detail="Version not found")

    # Call OpenAI with a concise system prompt so we stay in the free tier token limit
    prompt = (
        "以下は議事録の Markdown です。指示に従い編集し、Markdown でのみ回答してください。\n\n"
        "---\n" + mv.markdown + "\n---\n\n指示: " + body.instruction
    )

    rsp = oai.chat.completions.create(
        model=body.model,
        messages=[
            {"role": "system", "content": "あなたは優秀な議事録編集者です。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    new_markdown: str = rsp.choices[0].message.content.strip()

    next_no: int = (
        db.execute(
            select(func.coalesce(func.max(M.MinutesVersion.version_no), 0) + 1).where(
                M.MinutesVersion.transcript_id == mv.transcript_id
            )
        ).scalar_one()
    )

    new_mv = M.MinutesVersion(
        transcript_id=mv.transcript_id,
        version_no=next_no,
        markdown=new_markdown,
        created_by=body.created_by,
        created_at=datetime.utcnow(),
    )
    db.add(new_mv)
    db.commit()
    db.refresh(new_mv)
    return new_mv

# ---------------------------------------------------------------------------
# End of file
# ---------------------------------------------------------------------------
