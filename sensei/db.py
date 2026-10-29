"""Tiny SQLite store for finished sessions (first name / nickname only - no personal data)."""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timedelta

DB_PATH = os.getenv("SENSEI_DB", "sensei.db")


def _conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute(
        """CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            student TEXT,
            language TEXT,
            goal TEXT,
            code TEXT,
            hints_used INTEGER,
            solved INTEGER,
            concept TEXT,
            misconception TEXT,
            diagnosis TEXT
        )"""
    )
    return con


def save_session(session: dict, diagnosis: dict) -> None:
    with _conn() as con:
        con.execute(
            "INSERT INTO sessions (created_at, student, language, goal, code, hints_used, solved, "
            "concept, misconception, diagnosis) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                datetime.now().isoformat(timespec="seconds"),
                session["student"],
                session["language"],
                session["goal"],
                session["code"],
                session["level"],
                int(bool(session.get("solved"))),
                diagnosis.get("concept", ""),
                diagnosis.get("misconception", ""),
                json.dumps(diagnosis),
            ),
        )


def all_sessions() -> list[dict]:
    with _conn() as con:
        rows = con.execute("SELECT * FROM sessions ORDER BY created_at DESC").fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["diagnosis"] = json.loads(d["diagnosis"] or "{}")
        out.append(d)
    return out


def clear() -> None:
    with _conn() as con:
        con.execute("DELETE FROM sessions")


def seed_demo_data() -> None:
    """Fill the dashboard with realistic example sessions for the demo video."""
    examples = [
        ("Ava", "JavaScript", "Loops", "Thinks a for loop runs once more than its condition allows", 3, 1),
        ("Leo", "JavaScript", "Loops", "Believes i <= length is safe for the last array item", 2, 1),
        ("Zara", "Small Basic", "Coordinates & graphics", "Thinks Y gets bigger going UP the screen", 1, 1),
        ("Sam", "JavaScript", "Variables", "Uses = when comparing values in an if statement", 4, 0),
        ("Maya", "Small Basic", "Loops", "Expects the loop variable to keep its value after EndFor", 2, 1),
        ("Ollie", "JavaScript", "Scope", "Declares score inside the function so it resets every click", 4, 1),
        ("Ava", "JavaScript", "Conditionals (if/else)", "Puts else-if conditions in the wrong order", 2, 1),
        ("Leo", "JavaScript", "Loops", "Changes the loop counter inside the loop body", 3, 0),
        ("Zara", "Small Basic", "Program flow / order of steps", "Draws the shape before setting the pen colour", 1, 1),
    ]
    now = datetime.now()
    with _conn() as con:
        for i, (student, lang, concept, misc, hints, solved) in enumerate(examples):
            diag = {
                "concept": concept,
                "misconception": misc,
                "confidence": "high",
                "next_exercise": "Demo data - run a real session to see a generated exercise.",
                "sensei_note": "Demo data.",
            }
            con.execute(
                "INSERT INTO sessions (created_at, student, language, goal, code, hints_used, solved, "
                "concept, misconception, diagnosis) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    (now - timedelta(hours=3 * i)).isoformat(timespec="seconds"),
                    student, lang, "(demo)", "(demo)", hints, solved, concept, misc, json.dumps(diag),
                ),
            )
