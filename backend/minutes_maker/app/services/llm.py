"""
OpenAI へのラッパー – AI に議事録を修正させる。
返値は assistant 返信と更新後 Markdown (変更なければ現状を返す)。
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Sequence, Union

from openai import OpenAI
from ..schemas.chat import ChatMessage  # Pydantic 型

client = OpenAI()


def _to_openai_msg(m: Union[ChatMessage, Dict[str, Any]]) -> Dict[str, str]:
    """ChatMessage / dict どちらでも OpenAI 形式へ揃える。"""
    if isinstance(m, dict):
        return {"role": m.get("role", "user"), "content": m.get("content", "")}
    return {"role": m.role, "content": m.content}


def complete_with_minutes(
    user_messages: Sequence[Union[ChatMessage, Dict[str, Any]]],
    user_input: str,
    current_minutes: str,
) -> tuple[str, str]:
    system_prompt = (
        "あなたは優秀なビジネスアシスタントです。ユーザーと対話しながら議事録(Markdown)"
        "を改善します。回答は必ず JSON で返してください：\n"
        '{ "assistant_message": "...", "markdown": "..." }'
    )

    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"現在の議事録:\n```\n{current_minutes}\n```"},
    ] + [_to_openai_msg(m) for m in user_messages] + [
        {"role": "user", "content": user_input}
    ]

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        response_format={"type": "json_object"},  # JSON mode
        temperature=0.3,
    )

    # 返値は JSON 文字列なのでパースする
    raw: str = resp.choices[0].message.content  # type: ignore[attr-defined]
    # ```json ... ``` を除去するケースもある&#8203;:contentReference[oaicite:3]{index=3}
    raw = re.sub(r"```json\n?|```", "", raw).strip()
    data = json.loads(raw)

    markdown = data.get("markdown") or current_minutes
    return data["assistant_message"], markdown
