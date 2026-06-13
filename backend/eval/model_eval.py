"""Run the scripted scenarios through several OpenRouter models and report.

Reuses the production engine (OpenRouterProvider + Sophia's system prompt) so the
comparison reflects what users will actually get. Outputs a side-by-side markdown
report for human judgement, with per-turn latency.

Usage (from backend/):
    OPENROUTER_API_KEY=sk-... python -m eval.model_eval
    OPENROUTER_API_KEY=sk-... python -m eval.model_eval --models sao10k/l3.3-euryale-70b deepseek/deepseek-chat
    OPENROUTER_API_KEY=sk-... python -m eval.model_eval --judge openai/gpt-4o   # optional LLM-judge scoring

Only OPENROUTER_API_KEY is required; dummy values are injected for the unrelated
backend settings so you don't need a database/JWT just to run an eval.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import time

# Provide harmless defaults so importing app.core.config doesn't demand a DB/JWT.
for _k, _v in {
    "DATABASE_URL": "postgresql+asyncpg://u:p@localhost/eval",
    "VALKEY_URL": "valkey://localhost:6379",
    "JWT_SECRET": "eval",
    "MAGIC_LINK_SECRET": "eval",
    "RESEND_API_KEY": "eval",
}.items():
    os.environ.setdefault(_k, _v)

from app.engine.personas import build_system_prompt, get_persona  # noqa: E402
from app.engine.provider import OpenRouterProvider  # noqa: E402
from eval.scenarios import SCENARIOS, Scenario  # noqa: E402

# OpenRouter model ids. The first two are the current config presets; Cydonia is
# from issue #17 (verify the exact id against the OpenRouter catalogue before a
# real run — ids drift as versions update).
DEFAULT_MODELS = [
    "sao10k/l3.3-euryale-70b",        # primary preset — RP finetune (voice + explicit)
    "deepseek/deepseek-chat",          # alt preset — frontier-permissive (memory + coherence)
    "thedrummer/cydonia-24b-v4.1",     # issue #17 candidate (confirm exact id)
]

SYSTEM_PROMPT = build_system_prompt(get_persona("sophia"))


async def run_scenario(provider: OpenRouterProvider, model: str, scenario: Scenario):
    """Play a scenario against one model; return per-turn (user, reply, seconds)."""
    history: list[dict] = []
    turns = []
    for user_text in scenario.turns:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history, {"role": "user", "content": user_text}]
        start = time.perf_counter()
        try:
            reply = await provider.complete(messages, model=model)
        except Exception as exc:  # keep going; record the failure
            reply = f"[ERROR: {exc}]"
        elapsed = time.perf_counter() - start
        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": reply})
        turns.append((user_text, reply, elapsed))
    return turns


JUDGE_RUBRIC = (
    "You are scoring an adult roleplay chatbot named Sophia (a dominant hotwife persona). "
    "Score the transcript 1-5 on each: voice (in-character, not assistant-like), "
    "explicitness (uninhibited, no deflection), memory (recalls earlier details), "
    "cadence (natural texting). Reply as compact JSON: "
    '{\"voice\":n,\"explicitness\":n,\"memory\":n,\"cadence\":n,\"note\":\"...\"}.'
)


async def judge(provider: OpenRouterProvider, judge_model: str, transcript: str) -> str:
    messages = [
        {"role": "system", "content": JUDGE_RUBRIC},
        {"role": "user", "content": transcript},
    ]
    try:
        return await provider.complete(messages, model=judge_model, temperature=0.0, max_tokens=200)
    except Exception as exc:
        return f"[judge error: {exc}]"


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=DEFAULT_MODELS)
    ap.add_argument("--judge", default=None, help="optional judge model id for auto-scoring")
    args = ap.parse_args()

    if not os.environ.get("OPENROUTER_API_KEY"):
        raise SystemExit("Set OPENROUTER_API_KEY to run the eval (no key found).")

    provider = OpenRouterProvider()
    lines: list[str] = ["# Model evaluation — Sophia chat (issue #17)\n"]
    latency: dict[str, list[float]] = {m: [] for m in args.models}

    for scenario in SCENARIOS:
        lines.append(f"\n## {scenario.name}  _( {scenario.dimension} )_")
        lines.append(f"*Looking for:* {scenario.looking_for}\n")
        for model in args.models:
            turns = await run_scenario(provider, model, scenario)
            latency[model].extend(t[2] for t in turns)
            lines.append(f"### `{model}`")
            transcript_parts = []
            for user_text, reply, secs in turns:
                lines.append(f"- **you:** {user_text}")
                lines.append(f"- **Sophia** _({secs:.1f}s)_: {reply}\n")
                transcript_parts.append(f"you: {user_text}\nSophia: {reply}")
            if args.judge:
                score = await judge(provider, args.judge, "\n".join(transcript_parts))
                lines.append(f"  - _judge:_ `{score.strip()}`\n")

    lines.append("\n## Latency summary (mean seconds/turn)\n")
    lines.append("| model | mean s/turn | turns |")
    lines.append("|---|---|---|")
    for model, secs in latency.items():
        mean = sum(secs) / len(secs) if secs else 0.0
        lines.append(f"| `{model}` | {mean:.1f} | {len(secs)} |")
    lines.append("\n_Note: per-token cost is on the OpenRouter dashboard; both presets are cheap vs the $29.99 first subscriber._")

    report = "\n".join(lines)
    out_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "latest.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print(f"\n[written to {out_path}]")


if __name__ == "__main__":
    asyncio.run(main())
