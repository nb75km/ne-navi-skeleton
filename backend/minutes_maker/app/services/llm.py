# 既存 import 群...
from openai import OpenAI

client = OpenAI()


def complete_with_minutes(
    user_messages: list[dict],
    user_input: str,
    current_minutes: str,
) -> tuple[str, str]:
    """
    GPT-4o に
        1) assistant 返信（自然文）
        2) 更新後 Markdown
    を JSON 文字列で返してもらう。
    """
    system_prompt = (
        "あなたは優秀なビジネスアシスタントです。ユーザーと対話しながら議事録(Markdown)を改善します。"
        "回答は以下 JSON フォーマットで返してください。\n"
        "{\n"
        '  "assistant_message": "<ユーザーへの返信>",\n'
        '  "markdown": "<更新後Markdown。変更不要なら空文字>"\n'
        "}"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"現在の議事録:\n```\n{current_minutes}\n```"},
    ]
    # これまでの会話履歴
    for m in user_messages:
        messages.append({"role": m["role"], "content": m["content"]})
    # 今回の指示
    messages.append({"role": "user", "content": user_input})

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    data = resp.choices[0].message.json()
    return data["assistant_message"], data["markdown"] or current_minutes
