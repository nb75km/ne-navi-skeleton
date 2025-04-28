# ---------------------------------------------------------------------------
# backend/minutes_maker/app/api/minutes_versions_router.py
# ---------------------------------------------------------------------------
"""CRUD for minutes_versions (edit / list)."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..db import models as M
from .. import SessionLocal

router = APIRouter(prefix="/api", tags=["minutes-versions"])


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class MinutesVersionIn(BaseModel):
    markdown: str = Field(min_length=10)
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


@router.get("/minutes_versions", response_model=list[MinutesVersionOut])
def list_versions(
    transcript_id: int = Query(..., description="Filter by transcript"),
    db: Session = Depends(get_db),
):
    stmt = select(M.MinutesVersion).where(M.MinutesVersion.transcript_id == transcript_id).order_by(M.MinutesVersion.version_no.desc())
    return db.scalars(stmt).all()


@router.post("/minutes_versions", response_model=MinutesVersionOut, status_code=201)
def create_version(
    body: MinutesVersionIn,
    transcript_id: int = Query(..., description="Parent transcript id"),
    db: Session = Depends(get_db),
):
    # determine next version number
    next_no: int = (
        db.execute(
            select(func.coalesce(func.max(M.MinutesVersion.version_no), 0) + 1).where(M.MinutesVersion.transcript_id == transcript_id)
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
