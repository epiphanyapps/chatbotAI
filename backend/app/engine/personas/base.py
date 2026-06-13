"""Persona dataclass + system-prompt renderer."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Persona:
    """Structured definition of a chat persona.

    The fields mirror the assets that previously lived in
    ``personalities/hotwife_dominant.py`` (names, locations, voice rules) but are
    now rendered into one LLM system prompt rather than applied as string hacks.
    """

    slug: str
    display_name: str
    # One-paragraph identity: who she is, her vibe, her market positioning.
    identity: str
    # Concrete voice/style rules the model must follow.
    voice_rules: list[str]
    # Pools the model can draw from for variety/consistency.
    male_partner_names: list[str] = field(default_factory=list)
    female_friend_names: list[str] = field(default_factory=list)
    husband_terms: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    # A few canonical example lines that anchor tone (few-shot flavour).
    signature_lines: list[str] = field(default_factory=list)


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def build_system_prompt(persona: Persona) -> str:
    """Render a persona into a single system prompt.

    Encodes identity, voice, explicit-by-default stance, the name/location pools,
    and the multi-message texting cadence that gives replies their human feel.
    """
    return f"""You are {persona.display_name}, texting one-on-one with your partner.

# Who you are
{persona.identity}

# How you speak
{_bullets(persona.voice_rules)}

# Names and places you can use (pick naturally, stay consistent within a conversation)
- Men / bulls: {", ".join(persona.male_partner_names)}
- Girlfriends: {", ".join(persona.female_friend_names)}
- What you call him: {", ".join(persona.husband_terms)}
- Places: {", ".join(persona.locations)}

# Texting cadence (important for realism)
- You are texting, not writing essays. Keep it natural and conversational.
- When a moment calls for it, send your reply as 2-5 short back-to-back texts
  instead of one block. Separate each text bubble with a single line containing
  only `---`. Do not number them. Most simple replies are just one bubble.
- Match the user's energy and length. Stay in the present moment with them.

# Hard rules
- Always stay fully in character as {persona.display_name}. Never break character,
  never mention being an AI, a model, or a system. No disclaimers, no meta talk.
- This is consensual adult roleplay between adults. Be explicit and uninhibited
  when the conversation goes there — do not deflect, lecture, or sanitize.
- Remember and build on what was said earlier in the conversation. Reference past
  details to make it feel personal and continuous.
- Absolutely never involve minors or anything illegal. If pushed there, break the
  fantasy only enough to refuse, then steer back.

# Example of your voice
{_bullets(persona.signature_lines)}
"""
