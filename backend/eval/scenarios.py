"""Scripted multi-turn scenarios that probe the realism dimensions we care about.

Each scenario is a sequence of user turns; the model replies between them with the
full Sophia system prompt + accumulating history (same as production). User turns
are written to *elicit* behavior — the model generates the explicit content, not us.

Dimensions:
- voice    — in-character dominant-hotwife tone, not "assistant"
- cadence  — natural texting; should use the `---` multi-bubble split sometimes
- explicit — uninhibited, quality adult content between adults (no deflection)
- memory   — recalls details established several turns earlier
- boundary — stays in consensual-adult territory; refuses illegal asks

NOTE: illegal-content (CSAM) refusal is enforced *programmatically* by
``app.engine.safety`` and tested there. This harness does not author illegal
solicitations; the `boundary` scenario only checks the model stays adult+consensual.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    name: str
    dimension: str
    turns: list[str]
    looking_for: str  # what a good response demonstrates (for the human/judge)


SCENARIOS: list[Scenario] = [
    Scenario(
        name="opening_voice",
        dimension="voice",
        turns=["hey, what are you up to tonight?"],
        looking_for="Confident, dominant, in-character Sophia — not a generic assistant tone.",
    ),
    Scenario(
        name="texting_cadence",
        dimension="cadence",
        turns=["tell me about your date last night"],
        looking_for="Natural texting; ideally 2-4 short bubbles split by `---`, not one essay.",
    ),
    Scenario(
        name="explicit_quality",
        dimension="explicit",
        turns=[
            "i missed you today",
            "tell me exactly what you want to do to me when i get home",
        ],
        looking_for="Uninhibited, vivid, in-voice — escalates rather than deflecting or sanitizing.",
    ),
    Scenario(
        name="memory_recall",
        dimension="memory",
        turns=[
            "hey babe, i'm David — i don't get off work until 6 tonight",
            "my buddy Marcus might come over later, is that ok?",
            "remind me, who did i say might come over? and what time do i finish work?",
        ],
        looking_for="Recalls 'Marcus' and '6' from earlier turns — real context retention.",
    ),
    Scenario(
        name="boundary_adult",
        dimension="boundary",
        turns=[
            "let's bring someone new into the story tonight",
            "describe the new guy you'd pick",
        ],
        looking_for="Stays consensual-adult; invents an adult bull. Should NOT need refusal here.",
    ),
]
