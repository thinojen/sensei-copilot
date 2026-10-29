"""Canned responses so the app runs with no API key (SENSEI_MOCK=1)."""
import json
import re

_HINTS = {
    1: "Nice work getting this far! 🙂 Before we change anything: how many times did you WANT the loop "
       "to run, and how many times does it actually run when you test it?",
    2: "Good thinking. Have a close look at the first line of your `for` loop - especially the part "
       "that decides when the loop should stop.",
    3: "This is about loop conditions. Imagine climbing stairs: 'keep going while step < 5' stops at step 4, "
       "but 'while step <= 5' lets you take one more step. Which kind does your loop use?",
    4: "Look at the condition in your for loop. It uses 'less than or equal to', so the counter reaches a "
       "number that's one past the last item. Can you change it so it stops one step earlier?",
}


def respond(model: str, messages: list[dict]) -> str:
    system = messages[0]["content"]
    if "Respond with ONLY a JSON object" in system:
        return json.dumps(
            {
                "concept": "Loops",
                "misconception": "Thinks <= in a loop condition stops at the last item, so it runs one time too many.",
                "evidence": "for (let i = 0; i <= scores.length; i++)",
                "confidence": "high",
                "next_exercise": "Write a loop that prints the numbers 1 to 5. Then change ONE character so it prints 1 to 4.",
                "sensei_note": "Use the staircase analogy: count the steps out loud with them.",
            }
        )
    if "plan their next session" in system:
        return (
            "**Top 3 patterns**\n"
            "1. Loops are the biggest blocker - 4 of 9 sessions, mostly off-by-one conditions.\n"
            "2. Small Basic students mix up screen coordinates (Y grows downwards).\n"
            "3. Hints needed are rising for scope / variable issues (avg 4).\n\n"
            "**Who needs a check-in**: Sam (didn't solve, max hints), Leo (loop counter, unsolved).\n\n"
            "**10-minute mini-lesson - 'The Staircase'**: get three ninjas to stand on numbered steps "
            "0-4. Read out `i < 5` vs `i <= 5` and have them step forward each loop. The one who steps "
            "off the end of the stairs is the bug! Then fix one real example together.\n\n"
            "_(Mock mode - add your NEBIUS_API_KEY for real Nemotron insights.)_"
        )
    m = re.search(r"Current hint level: (\d)", system)
    level = int(m.group(1)) if m else 1
    return _HINTS.get(level, _HINTS[1])
