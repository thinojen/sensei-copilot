"""Sanity check: list Nemotron models on your Token Factory account and ping the ones the app uses.

Usage:  NEBIUS_API_KEY=... python check_models.py
"""
import os

from openai import OpenAI

from sensei import llm

client = OpenAI(base_url=llm.BASE_URL, api_key=os.environ["NEBIUS_API_KEY"])

available = sorted(m.id for m in client.models.list().data)
print("NVIDIA models available on your account:")
for m in available:
    if "nemotron" in m.lower() or m.lower().startswith("nvidia/"):
        print("  ", m)

print("\nModels the app is configured to use:")
for label, model in [("FAST", llm.FAST_MODEL), ("MID", llm.MID_MODEL), ("SMART", llm.SMART_MODEL)]:
    ok = model in available
    print(f"  {label:5} {model}  {'OK' if ok else 'NOT FOUND - set SENSEI_' + label + '_MODEL'}")
    if ok:
        r = client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": "Say hi in 3 words."}], max_tokens=200
        )
        print("        ->", llm.clean(r.choices[0].message.content or "")[:80])
