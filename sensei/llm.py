"""Thin wrapper around Nebius Token Factory (OpenAI-compatible API).

Model routing:
  - FAST model  (Nemotron 3 Nano)  -> every hint the student sees. Needs to be quick.
  - SMART model (Nemotron 3 Ultra) -> concept diagnosis once a session ends.
  - MID model   (Nemotron 3 Super) -> class-wide insights on the sensei dashboard.

Set SENSEI_MOCK=1 to run without an API key (canned responses, for UI work / demos).
"""
from __future__ import annotations

import json
import os
import re

BASE_URL = os.getenv("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/")

# Check exact IDs in your Token Factory model catalog (or run check_models.py)
FAST_MODEL = os.getenv("SENSEI_FAST_MODEL", "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B")
MID_MODEL = os.getenv("SENSEI_MID_MODEL", "nvidia/nemotron-3-super-120b-a12b")
SMART_MODEL = os.getenv("SENSEI_SMART_MODEL", "nvidia/Nemotron-3-Ultra-550b-a55b")


def _secret(name: str) -> str | None:
    """Read from env first, then Streamlit secrets (for Streamlit Cloud)."""
    val = os.getenv(name)
    if val:
        return val
    try:
        import streamlit as st

        return st.secrets.get(name)  # type: ignore[attr-defined]
    except Exception:
        return None


def is_mock() -> bool:
    return os.getenv("SENSEI_MOCK", "0") == "1" or not _secret("NEBIUS_API_KEY")


_client = None


def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI

        _client = OpenAI(base_url=BASE_URL, api_key=_secret("NEBIUS_API_KEY"))
    return _client


_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def clean(text: str) -> str:
    """Nemotron reasoning models may emit <think> blocks - strip them."""
    text = _THINK_RE.sub("", text or "")
    # Unclosed think block (truncated) - drop everything before the close tag
    if "</think>" in text:
        text = text.split("</think>", 1)[1]
    return text.strip()


def chat(model: str, messages: list[dict], temperature: float = 0.4, max_tokens: int = 2000) -> str:
    if is_mock():
        from . import mock

        return mock.respond(model, messages)
    resp = _get_client().chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    choice = resp.choices[0]
    text = clean(choice.message.content or "")
    if choice.finish_reason == "length" and max_tokens < 8000:
        # Ran out of room (usually while reasoning) - retry once with double the budget
        return chat(model, messages, temperature, max_tokens * 2)
    return text


def chat_json(model: str, messages: list[dict], max_tokens: int = 4000) -> dict:
    """Ask for JSON and parse it robustly (models sometimes wrap it in prose/fences)."""
    raw = chat(model, messages, temperature=0.2, max_tokens=max_tokens)
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}
