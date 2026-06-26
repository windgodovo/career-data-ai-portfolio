from __future__ import annotations

import json
import re

from openai import APIStatusError
from openai import OpenAI

from .config import Settings


def _fallback_summary(summary_payload: dict) -> str:
    summary = summary_payload["summary"]
    hints = summary_payload["hints"]
    return (
        "Daily report summary (fallback mode):\n"
        f"- Total sales: {summary['total_sales']}\n"
        f"- Total profit: {summary['total_profit']}\n"
        f"- Profit margin: {summary['profit_margin']}\n"
        f"- Key observations: {'; '.join(hints)}\n"
        "- Next step: investigate low-profit region and optimize cost drivers."
    )


def _clean_summary_text(text: str) -> str:
    """Normalize model output to plain business text.

    Some providers return markdown bullets and bold markers. This function removes
    markdown symbols and keeps readable lines for email/PDF output.
    """
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        # Remove markdown bullet prefixes: *, -, +, numbered bullets.
        line = re.sub(r"^(?:[-*+]\s+|\d+[.)]\s+)", "", line)
        # Remove markdown emphasis markers.
        line = line.replace("**", "")
        line = line.replace("__", "")
        # Normalize extra spaces.
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def generate_ai_summary(settings: Settings, summary_payload: dict) -> str:
    if not settings.openai_api_key:
        return _fallback_summary(summary_payload)

    client_kwargs = {"api_key": settings.openai_api_key}
    if settings.openai_base_url:
        client_kwargs["base_url"] = settings.openai_base_url
    client = OpenAI(**client_kwargs)

    prompt = (
        "You are a business analyst. Return a concise daily business summary with exactly 5 lines: "
        "Overall KPI:, Region Insight:, Trend Risk:, Forecast Hint:, Next Action:. "
        "Use plain text only. Do not use markdown symbols such as *, **, -, #, or numbered lists.\n"
        f"Data:\n{json.dumps(summary_payload, ensure_ascii=True)}"
    )

    # Prefer Responses API. If provider endpoint does not support it (e.g. 404 on /responses),
    # automatically fallback to Chat Completions for compatibility.
    try:
        response = client.responses.create(
            model=settings.openai_model,
            input=prompt,
            temperature=0.2,
        )
        return _clean_summary_text(response.output_text)
    except APIStatusError as exc:
        if exc.status_code != 404:
            raise

    completion = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": "You are a business analyst.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
    )
    content = completion.choices[0].message.content
    final_text = content or _fallback_summary(summary_payload)
    return _clean_summary_text(final_text)
