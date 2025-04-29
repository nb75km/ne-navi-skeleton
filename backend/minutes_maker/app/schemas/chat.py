from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"] = Field(..., description="会話の話者")
    content: str = Field(..., description="メッセージ本文")


class ChatRequest(BaseModel):
    """
    ChatPanel から送信されるペイロード。

    - messages は直近の user/assistant ログを任意件数
    - user_input は今回ユーザーが送信した指示文
    """
    messages: List[ChatMessage] = Field(default_factory=list)
    user_input: str
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    assistant_message: str
    version_id: int
    markdown: str
