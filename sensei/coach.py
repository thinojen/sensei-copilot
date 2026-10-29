"""Core coaching logic: hint ladder, no-spoiler guard, diagnosis, class insights."""
from __future__ import annotations

import re

from . import llm, prompts

_FENCE_RE = re.compile(r"```")
_INLINE_CODE_RE = re.compile(r"`([^`]+)`")


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", s)


def leaks_answer(hint: str, student_code: str) -> bool:
    """Heuristic spoiler check.

    A hint leaks if it contains a fenced code block, or an inline code snippet that
    looks like a *changed* version of one of the student's own lines.
    """
    if _FENCE_RE.search(hint):
        return True
    student_lines = {_norm(l) for l in student_code.splitlines() if len(l.strip()) > 3}
    for snippet in _INLINE_CODE_RE.findall(hint):
        n = _norm(snippet)
        if len(n) < 12 or n in student_lines:
            continue  # short fragments or quoting their own code is fine
        # long snippet that isn't their code - probably a rewritten line
        if any(_similar(n, line) for line in student_lines):
            return True
    return False


def _similar(a: str, b: str) -> bool:
    """Cheap similarity: shares a long common prefix or suffix but isn't identical."""
    if a == b or not b:
        return False
    k = min(len(a), len(b)) // 2
    return k >= 5 and (a[:k] == b[:k] or a[-k:] == b[-k:])


def _strip_code(hint: str) -> str:
    return re.sub(r"```.*?```", "(I'll let you type this part yourself!)", hint, flags=re.DOTALL)


def get_hint(session: dict) -> tuple[str, bool]:
    """Return (hint_text, guard_triggered) for the session's current level."""
    level = session["level"]
    name, instruction = prompts.HINT_LEVELS[level]
    history = ""
    if session["turns"]:
        history = "\nOur chat so far:\n" + "\n".join(
            f"{'Me' if t['role'] == 'user' else 'Sensei'}: {t['text']}" for t in session["turns"][-6:]
        )
    messages = [
        {
            "role": "system",
            "content": prompts.HINT_SYSTEM.format(
                language=session["language"], level=level, level_name=name, level_instruction=instruction
            ),
        },
        {
            "role": "user",
            "content": prompts.HINT_USER.format(
                language=session["language"],
                goal=session["goal"] or "(not given)",
                problem=session["problem"] or "(not given)",
                code=session["code"],
                history=history,
            ),
        },
    ]
    hint = llm.chat(llm.FAST_MODEL, messages)

    guard = False
    if leaks_answer(hint, session["code"]):
        guard = True
        messages += [{"role": "assistant", "content": hint}, {"role": "user", "content": prompts.STRICT_RETRY}]
        hint = llm.chat(llm.FAST_MODEL, messages)
        if leaks_answer(hint, session["code"]):
            hint = _strip_code(hint)
    return hint, guard


def diagnose(session: dict) -> dict:
    transcript = "\n".join(
        f"{'Student' if t['role'] == 'user' else 'Coach'}: {t['text']}" for t in session["turns"]
    )
    messages = [
        {"role": "system", "content": prompts.DIAGNOSIS_SYSTEM.format(concepts=", ".join(prompts.CONCEPTS))},
        {
            "role": "user",
            "content": prompts.DIAGNOSIS_USER.format(
                language=session["language"],
                goal=session["goal"],
                problem=session["problem"],
                hints_used=session["level"],
                max_level=prompts.MAX_LEVEL,
                solved="yes" if session.get("solved") else "no",
                code=session["code"],
                transcript=transcript or "(none)",
            ),
        },
    ]
    result = llm.chat_json(llm.SMART_MODEL, messages)
    if result.get("concept") not in prompts.CONCEPTS:
        result["concept"] = result.get("concept") or "Program flow / order of steps"
    return result


def class_insights(rows: list[dict]) -> str:
    table = "\n".join(
        f"- {r['student']} | {r['language']} | {r['concept']} | {r['misconception']} | "
        f"hints {r['hints_used']} | {'solved' if r['solved'] else 'NOT solved'}"
        for r in rows
    )
    messages = [
        {"role": "system", "content": prompts.INSIGHTS_SYSTEM},
        {"role": "user", "content": f"Recent sessions:\n{table}"},
    ]
    return llm.chat(llm.MID_MODEL, messages, max_tokens=900)
