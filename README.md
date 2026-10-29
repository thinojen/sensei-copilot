# 🥷 Sensei Copilot

**A coding coach for kids that never gives the answer.**

Built for the Nebius x NVIDIA Global AI Hackathon, **Best Apps and Agents** track.

## The problem

At kids' coding clubs, one tutor ("sensei") looks after a room full of 7–15 year olds. When a child gets stuck, they either:

- wait with their hand up, losing momentum, or
- ask a general-purpose AI that hands them the fixed code, so they learn nothing.

The sensei also never sees the *pattern*: which concept the whole class keeps tripping over this week.

## The solution

Sensei Copilot has two sides.

**🧒 Ninja mode (for students)**
1. Paste your code and say what you wanted vs what's happening.
2. Get a hint from the **hint ladder**. Each "still stuck" press climbs one rung:
   1. *Nudge* – a question comparing expected vs actual behaviour
   2. *Look here* – which area of the code to look at
   3. *Big idea* – the concept, explained with an analogy that isn't their code
   4. *Spot it* – the exact line and what's wrong, in words only
3. A **no-spoiler guard** checks every hint. If the model leaks corrected code, it's sent back to rewrite the hint, and stripped if it still leaks.
4. When they fix it, they get a targeted 5-minute practice challenge.

**🎓 Sensei dashboard (for tutors)**
- Every session is diagnosed into a concept + specific misconception.
- See where the class gets stuck, who needs a check-in, and solve rates.
- One click generates class insights and a 10-minute group mini-lesson.

## How it uses NVIDIA Nemotron on Nebius Token Factory

All inference runs on **Nebius Token Factory** through its OpenAI-compatible API. Each job is routed to the Nemotron model that fits it:

| Job | Model | Why |
|---|---|---|
| Every hint a child sees | **Nemotron 3 Nano** | Kids won't wait. Fast and cheap enough to call on every turn. |
| Session diagnosis (concept, misconception, practice task) | **Nemotron 3 Ultra** | Inferring *why* a child made a mistake from code + conversation needs deep reasoning. Runs once per session, so cost stays low. |
| Class insights and mini-lesson plan | **Nemotron 3 Super** | Summarising across many sessions: a middle ground of quality and speed. |

### Where Token Factory accelerated the workflow

- **Minutes to first call:** Token Factory is OpenAI-compatible, so the standard `openai` Python SDK works by changing only the `base_url`. No custom client or new SDK to learn.
- **One endpoint, three models:** swapping between Nano, Super and Ultra is a single string change, which made it easy to test which model suits each job and route each call to the cheapest model that does it well.
- **No GPUs to manage:** Ultra (550B parameters) runs serverless behind the same API, so a solo builder can use a frontier-scale reasoning model without provisioning or hosting anything.
- **Cheap enough to call on every keystroke of a lesson:** Nano's per-token price means a hint costs a fraction of a penny, so a whole classroom can use it.

### Other Nebius tools

All inference runs on Nebius Token Factory. The app itself is hosted on Streamlit Community Cloud for the public demo. Nebius Serverless Endpoints would be the next step for a production deployment.

Model IDs are configurable via env vars (see below). `sensei/llm.py` strips Nemotron `<think>` reasoning blocks and parses JSON robustly.

## Setup

```bash
git clone <your-repo-url>
cd sensei-copilot
pip install -r requirements.txt

export NEBIUS_API_KEY="your_token_factory_key"   # from tokenfactory.nebius.com
python check_models.py                            # confirms the model IDs on your account
streamlit run app.py
```

No key yet? Run `SENSEI_MOCK=1 streamlit run app.py` for canned responses.

### Config

| Variable | Default |
|---|---|
| `NEBIUS_API_KEY` | required for live mode |
| `NEBIUS_BASE_URL` | `https://api.tokenfactory.nebius.com/v1/` |
| `SENSEI_FAST_MODEL` | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` |
| `SENSEI_MID_MODEL` | `nvidia/nemotron-3-super-120b-a12b` |
| `SENSEI_SMART_MODEL` | `nvidia/Nemotron-3-Ultra-550b-a55b` |
| `SENSEI_PIN` | optional PIN to lock the dashboard |
| `SENSEI_MOCK` | `1` to force mock mode |

### Deploy (Streamlit Community Cloud)

Push to GitHub → new app on share.streamlit.io → main file `app.py` → add `NEBIUS_API_KEY` under *Secrets*.

## Try it

1. Ninja mode → pick **"JavaScript - add up scores"** → *Help me, Sensei!*
2. Press **Still stuck** a few times to climb the ladder, then **I fixed it!**
3. Sensei dashboard → **Load demo data** → **Generate insights & mini-lesson**.

## Safety and privacy

Built for under-16s:
- Only a first name or nickname is collected. No accounts, emails or ages.
- Prompts keep tone age-appropriate and steer off-topic chat back to code.
- Session data lives in a local SQLite file (`sensei.db`) that the club controls.

## Project structure

```
app.py              Streamlit UI (Ninja mode + Sensei dashboard)
sensei/llm.py       Token Factory client, model routing, mock switch
sensei/coach.py     Hint ladder, no-spoiler guard, diagnosis, insights
sensei/prompts.py   All prompts + concept taxonomy
sensei/db.py        SQLite storage + demo data
sensei/mock.py      Canned responses for offline mode
check_models.py     Verifies model IDs on your Token Factory account
```

## Licence

MIT – see [LICENSE](LICENSE).
