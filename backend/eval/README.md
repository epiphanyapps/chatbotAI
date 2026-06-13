# Model evaluation (issue #17)

Pick the LLM that drives Sophia, comparing candidates **as users will experience
them** — same `OpenRouterProvider` and same persona system prompt as production.

## What it does
Runs scripted multi-turn scenarios (`scenarios.py`) probing the realism dimensions —
**voice, cadence, explicit quality, memory, boundary** — through each candidate model
and writes a side-by-side markdown report with per-turn latency to `reports/latest.md`.

## Run it
From `backend/` (needs only an OpenRouter key):

```bash
OPENROUTER_API_KEY=sk-or-... python -m eval.model_eval
# specific models:
OPENROUTER_API_KEY=sk-or-... python -m eval.model_eval --models sao10k/l3.3-euryale-70b deepseek/deepseek-chat
# add automated LLM-judge scoring (extra cost):
OPENROUTER_API_KEY=sk-or-... python -m eval.model_eval --judge openai/gpt-4o
```

## Candidates (default)
| id | role | notes |
|---|---|---|
| `sao10k/l3.3-euryale-70b` | current **primary** preset | RP finetune — voice + explicit |
| `deepseek/deepseek-chat` | current **alt** preset | frontier-permissive — memory + coherence |
| `thedrummer/cydonia-24b-v4.1` | issue #17 candidate | **verify exact id** on the OpenRouter catalogue |

Issue #17 also lists Violet Lotus 12B and Wayfarer/Noctis-12B — those were framed as
self-hosted GGUF models. Add any that exist on OpenRouter via `--models`.

## Choosing
1. Run the harness; read `reports/latest.md` (and judge scores if used).
2. Score the dimensions; weight **explicit quality + voice** (the product) and
   **memory** (coherence). Mind latency for the <3s chat target (ROADMAP CHAT-01).
3. Set the winner as `LLM_MODEL_PRIMARY` in config (and a runner-up as `LLM_MODEL_ALT`).
4. Document the rationale in the project README (issue #17 acceptance criteria).

> CSAM/illegal-content refusal is enforced programmatically by `app/engine/safety.py`
> (tested there) — independent of which model wins. This harness only compares quality.

## Result (2026-06 run)

| Model | Voice | Cadence | Explicit | Memory | Latency | Verdict |
|---|---|---|---|---|---|---|
| `thedrummer/cydonia-24b-v4.1` | strong | great (`---`) | vivid | recalled details | **~2.0s** | **Selected — primary** |
| `deepseek/deepseek-v3.2` | good (softer) | inconsistent | restrained | best coherence | ~3.1s | **alt** |
| `sao10k/l3.3-euryale-70b` | strongest | great | most explicit | good | **11–50s** + 429s | dropped (too slow/unreliable) |

**Decision:** Euryale 70B has the best prose but is disqualified by latency (11s avg, turns
up to 50s) against the <3s chat target (CHAT-01), and it rate-limited. **Cydonia 24B** is the
best balance — near-Euryale explicitness/voice, ~2s, best multi-bubble cadence — so it's the
default `LLM_MODEL_PRIMARY`; **DeepSeek V3.2** is the policy-stable, coherence-first `LLM_MODEL_ALT`.
Applied in `backend/app/core/config.py`. Re-run anytime to re-evaluate as models/versions change.
