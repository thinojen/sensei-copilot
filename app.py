"""Sensei Copilot - a coding coach that never gives the answer.

Run:  streamlit run app.py
"""
from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from sensei import coach, db, llm, prompts

st.set_page_config(page_title="Sensei Copilot", page_icon="🥷", layout="wide")

EXAMPLES = {
    "JavaScript - add up scores": {
        "language": "JavaScript",
        "goal": "Add up all the scores in my list and show the total",
        "problem": "It says the total is NaN instead of a number",
        "code": """let scores = [10, 25, 7, 40];
let total = 0;

for (let i = 0; i <= scores.length; i++) {
  total = total + scores[i];
}

console.log("Total score: " + total);""",
    },
    "Small Basic - falling ball": {
        "language": "Small Basic",
        "goal": "Make the ball fall down to the bottom of the window",
        "problem": "The ball goes UP and disappears off the top",
        "code": """GraphicsWindow.Height = 400
ball = Shapes.AddEllipse(30, 30)
y = 300

For step = 1 To 50
  y = y - 5
  Shapes.Move(ball, 200, y)
  Program.Delay(30)
EndFor""",
    },
}

# ---------------------------------------------------------------- styling
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@500;700;800&family=Nunito:wght@400;600;800&display=swap');

html, body, [class*="css"], .stMarkdown, p, label, input, textarea, button {
  font-family: 'Nunito', sans-serif !important;
}
h1, h2, h3, .hero h1 { font-family: 'Baloo 2', cursive !important; letter-spacing: -0.01em; }

/* playful background dots */
.stApp {
  background-color: #FFF9EE;
  background-image: radial-gradient(#FFD9A8 1.2px, transparent 1.2px);
  background-size: 26px 26px;
}
[data-testid="stSidebar"] { background: #FFE6BF; border-right: 3px solid #FFD08A; }

/* chunky buttons */
.stButton > button, .stFormSubmitButton > button {
  border-radius: 999px !important; font-weight: 800 !important; padding: 0.55rem 1.2rem !important;
  border: 2.5px solid #2B2147 !important; box-shadow: 0 4px 0 #2B2147 !important;
  transition: transform .08s ease, box-shadow .08s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 0 #2B2147 !important; }
.stButton > button:active, .stFormSubmitButton > button:active { transform: translateY(3px); box-shadow: 0 1px 0 #2B2147 !important; }

/* cards: form, chat bubbles, code */
[data-testid="stForm"], [data-testid="stChatMessage"] {
  background: #FFFFFF; border: 2.5px solid #2B2147; border-radius: 22px; box-shadow: 5px 5px 0 #FFC46B;
}
[data-testid="stChatMessage"] { padding: 0.9rem 1.1rem; margin-bottom: 0.8rem; }
[data-testid="stCode"] { border: 2.5px solid #2B2147; border-radius: 18px; overflow: hidden; }
[data-testid="stMetric"] {
  background: #FFFFFF; border: 2.5px solid #2B2147; border-radius: 20px; padding: 0.8rem 1rem;
  box-shadow: 4px 4px 0 #8FD3FF;
}

/* hero */
.hero { background: linear-gradient(120deg, #FF6B2C 0%, #FF9F1C 55%, #FFD23F 100%);
  border: 3px solid #2B2147; border-radius: 28px; padding: 1.6rem 1.8rem; margin-bottom: 1.2rem;
  box-shadow: 6px 6px 0 #2B2147; color: #2B2147; }
.hero h1 { font-size: 2.3rem; margin: 0 0 .3rem 0; line-height: 1.1; color: #2B2147; }
.hero p { font-size: 1.1rem; margin: 0; font-weight: 600; }
.steps { display:flex; gap:10px; margin-top: 1rem; flex-wrap: wrap; }
.step { background:#FFFFFFdd; border:2px solid #2B2147; border-radius:999px; padding:4px 14px; font-weight:800; font-size:.9rem; }

/* belt ladder */
.belts { display:flex; gap:10px; margin: 0.4rem 0 1.2rem 0; flex-wrap: wrap; }
.belt { flex:1; min-width: 110px; text-align:center; opacity:.4; transition: all .2s ease; }
.belt .strap { height: 18px; border:2.5px solid #2B2147; border-radius: 6px; position: relative; }
.belt .strap::after { content:""; position:absolute; left:50%; top:50%; width:16px; height:26px;
  transform: translate(-50%,-50%) rotate(8deg); background: inherit; border:2.5px solid #2B2147; border-radius:5px; }
.belt .lbl { font-weight:800; font-size:.82rem; margin-top:8px; }
.belt .sub { font-size:.72rem; opacity:.75; }
.belt.done { opacity:.75; }
.belt.now { opacity:1; transform: translateY(-3px) scale(1.04); }
.belt.now .lbl { color:#FF6B2C; }
.small-muted { font-size:0.8rem; opacity:0.65; }
.belt-badge { display:inline-block; padding:3px 12px; border:2px solid #2B2147; border-radius:999px; font-weight:800; font-size:.85rem; }
</style>
""",
    unsafe_allow_html=True,
)

BELTS = {
    1: ("White belt", "#FFFFFF"),
    2: ("Yellow belt", "#FFD23F"),
    3: ("Orange belt", "#FF9F1C"),
    4: ("Black belt", "#2B2147"),
}


def ladder_html(level: int) -> str:
    parts = []
    for n, (name, _) in prompts.HINT_LEVELS.items():
        belt, colour = BELTS[n]
        cls = "now" if n == level else ("done" if n < level else "")
        parts.append(
            f'<div class="belt {cls}"><div class="strap" style="background:{colour}"></div>'
            f'<div class="lbl">{belt}</div><div class="sub">{name}</div></div>'
        )
    return '<div class="belts">' + "".join(parts) + "</div>"


def belt_badge(level: int) -> str:
    belt, colour = BELTS[level]
    fg = "#FFFFFF" if level == 4 else "#2B2147"
    return f'<span class="belt-badge" style="background:{colour};color:{fg}">{belt} hint</span>'


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.title("🥷 Sensei Copilot")
    st.caption("A coding coach that never gives you the answer.")
    page = st.radio("Mode", ["Ninja mode", "Sensei dashboard"], label_visibility="collapsed")
    st.divider()
    if llm.is_mock():
        st.warning("Mock mode - no NEBIUS_API_KEY set, responses are canned.")
    else:
        st.success("Live on Nebius Token Factory")
    with st.expander("Models in use"):
        st.markdown(
            f"- **Hints (fast):** `{llm.FAST_MODEL}`\n"
            f"- **Diagnosis (deep reasoning):** `{llm.SMART_MODEL}`\n"
            f"- **Class insights:** `{llm.MID_MODEL}`"
        )


# ---------------------------------------------------------------- ninja mode
def new_session(student, language, goal, problem, code):
    return {
        "student": student.strip() or "Ninja",
        "language": language,
        "goal": goal.strip(),
        "problem": problem.strip(),
        "code": code,
        "level": 1,
        "turns": [],
        "solved": None,
        "diagnosis": None,
    }


def add_hint(sess):
    with st.spinner("Sensei is thinking..."):
        try:
            hint, guarded = coach.get_hint(sess)
        except Exception as e:  # keep the UI alive if the API hiccups
            st.error(f"Couldn't reach the model: {e}")
            return
    sess["turns"].append(
        {"role": "assistant", "text": hint, "level": sess["level"], "model": llm.FAST_MODEL, "guarded": guarded}
    )


def finish(sess, solved: bool):
    sess["solved"] = solved
    with st.spinner("Working out what to practise next..."):
        try:
            sess["diagnosis"] = coach.diagnose(sess)
        except Exception as e:
            st.error(f"Diagnosis failed: {e}")
            sess["diagnosis"] = {}
    db.save_session(sess, sess["diagnosis"])


def ninja_page():
    sess = st.session_state.get("session")

    if sess is None:
        st.markdown(
            """<div class="hero"><h1>Stuck on your code? 🥷</h1>
<p>Paste it in and Sensei gives you hints, but YOU do the fixing. That's how ninjas level up!</p>
<div class="steps"><span class="step">1 · Paste your code</span><span class="step">2 · Get a hint</span>
<span class="step">3 · Fix it yourself 🏆</span></div></div>""",
            unsafe_allow_html=True,
        )

        ex = st.selectbox("Try an example (or write your own below)", ["-"] + list(EXAMPLES))
        pre = EXAMPLES.get(ex, {})

        with st.form("start"):
            c1, c2 = st.columns([1, 1])
            student = c1.text_input("Your ninja name (first name or nickname only)", max_chars=20)
            langs = ["JavaScript", "Small Basic", "Python"]
            language = c2.selectbox("Language", langs, index=langs.index(pre.get("language", "JavaScript")))
            goal = st.text_input("What do you WANT your program to do?", value=pre.get("goal", ""))
            problem = st.text_input("What's ACTUALLY happening?", value=pre.get("problem", ""))
            code = st.text_area("Your code", value=pre.get("code", ""), height=260)
            go = st.form_submit_button("Help me, Sensei! 🥷", type="primary")

        if go:
            if not code.strip():
                st.error("Paste some code first!")
                return
            sess = new_session(student, language, goal, problem, code)
            st.session_state.session = sess
            add_hint(sess)
            st.rerun()
        return

    # ---- active / finished session
    left, right = st.columns([3, 2])
    with right:
        st.subheader("Your code")
        st.code(sess["code"], language="javascript" if sess["language"] == "JavaScript" else None)
        st.caption(f"🎯 {sess['goal'] or '-'}  \n🐞 {sess['problem'] or '-'}")

    with left:
        st.subheader(f"Hey {sess['student']}! 👋")
        st.markdown(ladder_html(sess["level"]), unsafe_allow_html=True)

        for t in sess["turns"]:
            with st.chat_message(t["role"], avatar="🥷" if t["role"] == "assistant" else "🧒"):
                st.markdown(t["text"])
                if t["role"] == "assistant":
                    st.markdown(belt_badge(t.get("level", 1)), unsafe_allow_html=True)
                    source = "mock response" if llm.is_mock() else f"{t['model']} · Nebius Token Factory"
                    note = f"⚡ {source}"
                    if t.get("guarded"):
                        note += " · 🛡️ no-spoiler guard rewrote this hint"
                    st.markdown(f'<span class="small-muted">{note}</span>', unsafe_allow_html=True)

        if sess["solved"] is None:
            reply = st.chat_input("Answer Sensei's question or tell it what you tried...")
            if reply:
                sess["turns"].append({"role": "user", "text": reply})
                add_hint(sess)
                st.rerun()

            b1, b2, b3 = st.columns(3)
            if b1.button("😕 Still stuck", disabled=sess["level"] >= prompts.MAX_LEVEL, width="stretch"):
                sess["level"] += 1
                sess["turns"].append({"role": "user", "text": "I'm still stuck - can I have a bigger hint?"})
                add_hint(sess)
                st.rerun()
            if b2.button("🎉 I fixed it!", type="primary", width="stretch"):
                finish(sess, True)
                st.rerun()
            if b3.button("Ask a real sensei", width="stretch"):
                finish(sess, False)
                st.rerun()
        else:
            d = sess["diagnosis"] or {}
            if sess["solved"]:
                if not st.session_state.get("ballooned"):
                    st.balloons()
                    st.session_state.ballooned = True
                belt = BELTS[sess["level"]][0]
                st.success(f"You fixed it yourself at **{belt}** level! That's real debugging. 🏆")
            else:
                st.info("No worries - put your hand up and a sensei will come over. They'll know what to look at. 🙌")
            if d.get("next_exercise"):
                st.markdown(f"**🎯 Practice challenge:** {d['next_exercise']}")
            if st.button("Start a new problem"):
                st.session_state.session = None
                st.session_state.ballooned = False
                st.rerun()


# ---------------------------------------------------------------- sensei dashboard
def dashboard_page():
    pin = os.getenv("SENSEI_PIN")
    if pin and st.session_state.get("pin_ok") is not True:
        entered = st.text_input("Sensei PIN", type="password")
        if entered == pin:
            st.session_state.pin_ok = True
            st.rerun()
        return

    st.header("🎓 Sensei dashboard")
    rows = db.all_sessions()

    c1, c2 = st.columns([1, 1])
    if c1.button("Load demo data"):
        db.seed_demo_data()
        st.rerun()
    if c2.button("Clear all sessions"):
        db.clear()
        st.session_state.pop("insights", None)
        st.rerun()

    if not rows:
        st.info("No sessions yet. Run one in Ninja mode, or load demo data.")
        return

    df = pd.DataFrame(rows)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Sessions", len(df))
    m2.metric("Solved independently", f"{df['solved'].mean():.0%}")
    m3.metric("Avg hint level", f"{df['hints_used'].mean():.1f} / {prompts.MAX_LEVEL}")
    m4.metric("Ninjas helped", df["student"].nunique())

    left, right = st.columns([1, 1])
    with left:
        st.subheader("Where the class gets stuck")
        st.bar_chart(df["concept"].value_counts(), horizontal=True, color="#FF6B2C")
    with right:
        st.subheader("Needs a check-in")
        flag = df[(df["solved"] == 0) | (df["hints_used"] >= prompts.MAX_LEVEL)]
        if flag.empty:
            st.write("Everyone's flying solo. 🎉")
        for _, r in flag.iterrows():
            st.markdown(f"- **{r['student']}** - {r['concept']}: _{r['misconception']}_")

    st.subheader("Class insights")
    st.caption(f"Generated by `{llm.MID_MODEL}` from all sessions above")
    if st.button("✨ Generate insights & mini-lesson", type="primary"):
        with st.spinner("Analysing the class..."):
            try:
                st.session_state.insights = coach.class_insights(rows)
            except Exception as e:
                st.error(f"Couldn't generate insights: {e}")
    if st.session_state.get("insights"):
        st.markdown(st.session_state.insights)

    st.subheader("All sessions")
    view = df[["created_at", "student", "language", "concept", "misconception", "hints_used", "solved"]].copy()
    view["solved"] = view["solved"].map({1: "✅", 0: "❌"})
    st.dataframe(view, width="stretch", hide_index=True)

    with st.expander("Per-session detail"):
        for r in rows[:20]:
            d = r["diagnosis"]
            st.markdown(
                f"**{r['student']}** · {r['concept']} · {r['created_at']}  \n"
                f"Misconception: {d.get('misconception', '-')}  \n"
                f"Evidence: `{d.get('evidence', '-')}`  \n"
                f"Tutor tip: {d.get('sensei_note', '-')}  \n"
                f"Practice: {d.get('next_exercise', '-')}"
            )
            st.divider()


if page == "Ninja mode":
    ninja_page()
else:
    dashboard_page()
