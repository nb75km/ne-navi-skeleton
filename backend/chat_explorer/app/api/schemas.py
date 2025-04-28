from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    id: int
    role: str
    body: str
    created_at: datetime


class Message(MessageBase):
    conversation_id: int

    class Config:
        from_attributes = True


class Conversation(BaseModel):
    id: int
    conversation_uid: str
    title: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
        populate_by_name = True
        from_attributes = True


class Paginated(BaseModel):
    total: int
    items: List[BaseModel]