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
    """Fill the dashboard with realistic example sessions for the demo video.

    Idempotent: removes any previous demo rows first, so double-clicks don't duplicate.
    """
    # (student, language, concept, misconception, hints, solved, evidence, tutor tip, practice)
    examples = [
        ("Ava", "JavaScript", "Loops", "Thinks a for loop runs once more than its condition allows", 3, 1,
         "for (let i = 0; i <= scores.length; i++)",
         "Use the staircase analogy: count the steps out loud and see who steps off the end.",
         "Print the numbers 1 to 5 with a loop, then change ONE character so it prints 1 to 4."),
        ("Leo", "JavaScript", "Loops", "Believes i <= length is safe for the last array item", 2, 1,
         "console.log(names[i]) prints undefined at the end",
         "Write the array indexes 0,1,2 under the items on the whiteboard - length is 3 but there's no box 3.",
         "Make a list of 3 pets and print each one. What does pets[3] give you? Why?"),
        ("Zara", "Small Basic", "Coordinates & graphics", "Thinks Y gets bigger going UP the screen", 1, 1,
         "y = y - 5 to make the ball fall",
         "Screen Y is like reading a page: line numbers grow as you go DOWN.",
         "Draw a dot at Y = 50 and another at Y = 300. Which one is higher? Predict first!"),
        ("Sam", "JavaScript", "Boolean logic", "Uses = when comparing values in an if statement", 4, 0,
         "if (lives = 0) { gameOver() }",
         "One equals is 'put into the box', three equals is 'are these the same?'. Act it out with a real box.",
         "Write three if statements that check a score. Read each one out loud as a question."),
        ("Maya", "Small Basic", "Loops", "Expects the loop variable to keep its value after EndFor", 2, 1,
         "TextWindow.WriteLine(i) after the loop",
         "Trace the loop on paper with a 'variable whiteboard' column and update it every step.",
         "Loop from 1 to 3 and print i inside AND after the loop. Explain the difference."),
        ("Ollie", "JavaScript", "Scope", "Declares score inside the function so it resets every click", 4, 1,
         "function onClick() { let score = 0; score++; }",
         "A variable inside a function is like a whiteboard wiped clean every time the function starts.",
         "Make a click counter. First put the variable inside the function, then move it out. What changes?"),
        ("Ava", "JavaScript", "Conditionals (if/else)", "Puts else-if conditions in the wrong order", 2, 1,
         "if (score > 10) ... else if (score > 50) ...",
         "Conditions are like a bouncer checking IDs in order - the first match wins, so put the strictest first.",
         "Give grades for scores: 90+ = A, 70+ = B, else C. Test with 95 - does it get an A?"),
        ("Leo", "JavaScript", "Loops", "Changes the loop counter inside the loop body", 3, 0,
         "for (let i = 0; i < 10; i++) { i = i + 2; }",
         "Let the loop own the counter. Use a separate variable if you need to count something else.",
         "Print every even number from 0 to 10 two ways: changing the step, and using an if."),
        ("Zara", "Small Basic", "Program flow / order of steps", "Draws the shape before setting the pen colour", 1, 1,
         "GraphicsWindow.DrawRectangle(...) then GraphicsWindow.PenColor = \"Red\"",
         "Programs are recipes: you pick up the red pen BEFORE you draw.",
         "Draw a red square then a blue circle. Swap the lines around and predict what happens."),
    ]
    now = datetime.now()
    with _conn() as con:
        con.execute("DELETE FROM sessions WHERE goal = '(demo)'")
        for i, (student, lang, concept, misc, hints, solved, evidence, tip, practice) in enumerate(examples):
            diag = {
                "concept": concept,
                "misconception": misc,
                "evidence": evidence,
                "confidence": "high",
                "next_exercise": practice,
                "sensei_note": tip,
            }
            con.execute(
                "INSERT INTO sessions (created_at, student, language, goal, code, hints_used, solved, "
                "concept, misconception, diagnosis) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    (now - timedelta(hours=3 * i)).isoformat(timespec="seconds"),
                    student, lang, "(demo)", "(demo)", hints, solved, concept, misc, json.dumps(diag),
                ),
            )
