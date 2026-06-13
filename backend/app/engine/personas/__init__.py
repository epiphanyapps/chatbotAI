"""Persona definitions and the system-prompt builder.

This replaces the old random string-overlay approach
(``personalities/hotwife_dominant.py``): a persona's voice now lives entirely in
a single, rich system prompt that the LLM follows for every turn, instead of
post-hoc ``.replace()`` hacks. New personas (Emma, Madison, Isabella — Issue #7)
are added as data here, not as new code.
"""

from __future__ import annotations

from app.engine.personas.base import Persona, build_system_prompt
from app.engine.personas.sophia import SOPHIA

# Registry keyed by persona slug. Extend with new personas as data.
PERSONAS: dict[str, Persona] = {
    SOPHIA.slug: SOPHIA,
}

DEFAULT_PERSONA = SOPHIA.slug


def get_persona(slug: str | None) -> Persona:
    """Resolve a persona by slug, falling back to the default."""
    return PERSONAS.get(slug or DEFAULT_PERSONA, SOPHIA)


__all__ = [
    "Persona",
    "build_system_prompt",
    "get_persona",
    "PERSONAS",
    "DEFAULT_PERSONA",
    "SOPHIA",
]
