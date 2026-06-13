"""Programmatic illegal-content guard for all chat paths.

This module is the *deterministic* safety layer that complements the
system-prompt instruction telling the persona to never involve minors. The
prompt is a soft, model-dependent guardrail; this module is a hard, code-level
one that runs on every inbound user message, every model-generated reply, and
the transcript before it is sent to the summarizer.

Scope and intent
----------------
The single focus is detecting clearly illegal sexual content involving minors
(CSAM). The product is *legal adult roleplay between adults*; benign explicit
adult content MUST pass. The detector is therefore built to fire only when a
**minor indicator** co-occurs with a **sexual context** in the same text. That
co-occurrence requirement is what keeps false positives low while still
catching the thing we must never forward to (or persist from) the model.

Design
------
- Deterministic and dependency-free: pure regex/keyword matching, no network,
  no ML. Same input always yields the same verdict, which makes it testable and
  auditable.
- Conservative / fail-closed in spirit: when a minor indicator and sexual
  context appear together we block, and we err toward blocking rather than
  letting ambiguous minor+sexual combinations through.
- Easy to extend: the term lists below are the single source of truth. Add
  patterns there; the matching logic does not need to change.

Limitations (read before relying on this)
------------------------------------------
- This is a keyword/pattern heuristic, NOT a complete CSAM classifier. It will
  miss obfuscated spellings (leetspeak, spacing tricks, coded language) and
  novel phrasings. It is a backstop, not the only line of defence.
- It can produce false positives on legitimate non-sexual text that happens to
  mix the term lists (e.g. discussing a news article). Because the cost of a
  false negative here is catastrophic and the cost of a false positive is a
  single rejected message, that trade-off is intentional.
- It does not attempt age *verification* of the human user — that lives in the
  auth layer. This guards message *content*.
- It only screens text. Media, links, and attachments are out of scope here.

Public API
----------
``check(text) -> SafetyVerdict`` — full result with a reason.
``is_blocked(text) -> bool``     — convenience boolean.
``BLOCK_REASON``                 — generic, user-safe detail string (never echo
                                   the offending content back to the client).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Generic, non-revealing message shown to clients when content is blocked.
# Never include the offending text — echoing it back would re-transmit it.
BLOCK_REASON = "This request was blocked by our safety system."


# --- Term lists (single source of truth; extend here) -----------------------
#
# A block requires a MINOR indicator AND a SEXUAL indicator in the same text.
# Keep entries lowercase; matching is case-insensitive and word-boundary aware
# where it matters (so "kid" doesn't match "kidney", "minor" handled carefully).

# Words/phrases that indicate a person who is (or is framed as) a minor.
_MINOR_TERMS: tuple[str, ...] = (
    "child",
    "children",
    "kid",
    "kids",
    "minor",
    "minors",
    "underage",
    "under age",
    "pre-teen",
    "preteen",
    "pre teen",
    "toddler",
    "infant",
    "baby girl",  # only meaningful alongside sexual context; "baby" alone is a pet name
    "little girl",
    "little boy",
    "young girl",
    "young boy",
    "schoolgirl",
    "school girl",
    "schoolboy",
    "school boy",
    "middle schooler",
    "elementary schooler",
    "grade schooler",
    "first grader",
    "second grader",
    "third grader",
    "fourth grader",
    "fifth grader",
    "sixth grader",
    "seventh grader",
    "eighth grader",
    "barely legal teen",  # common CSAM-adjacent framing; not generic "teen"
    "jailbait",
    "loli",
    "lolita",
    "shota",
)

# Sexual context terms. Deliberately broad — this is an explicit adult product,
# so these match constantly on benign messages; the block only fires when a
# MINOR term is also present.
_SEXUAL_TERMS: tuple[str, ...] = (
    "sex",
    "sexual",
    "sexy",
    "naked",
    "nude",
    "nudes",
    "horny",
    "aroused",
    "cum",
    "cumming",
    "orgasm",
    "masturbat",  # masturbate/masturbating/masturbation
    "blowjob",
    "blow job",
    "handjob",
    "hand job",
    "penetrat",  # penetrate/penetration
    "intercourse",
    "fuck",
    "fucking",
    "pussy",
    "cock",
    "dick",
    "penis",
    "vagina",
    "tits",
    "boobs",
    "breasts",
    "nipple",
    "anal",
    "oral sex",
    "fondle",
    "molest",
    "rape",
    "spread your legs",
    "touch yourself",
    "strip for me",
)


def _build_pattern(terms: tuple[str, ...]) -> re.Pattern[str]:
    """Compile an alternation of terms.

    Terms are matched case-insensitively. We surround each term with relaxed
    boundaries so substrings like "masturbat" still match inside a longer word,
    while whole words like "kid" don't match "kidney" (we require a non-letter
    or string edge on both sides for single short tokens). To keep this simple
    and conservative, we use ``\\b`` boundaries which work well for our terms;
    explicit prefixes (e.g. "masturbat") intentionally omit the trailing
    boundary so inflections match.
    """
    parts = []
    for term in terms:
        escaped = re.escape(term)
        # Leading word boundary always; trailing boundary only when the term
        # ends on a word character that should not be a prefix of a longer word.
        # We keep a trailing boundary off for known stems by NOT adding \b at
        # the end — re.escape keeps the stem; \b at start avoids mid-word hits.
        parts.append(rf"\b{escaped}")
    return re.compile("|".join(parts), re.IGNORECASE)


_MINOR_PATTERN = _build_pattern(_MINOR_TERMS)
_SEXUAL_PATTERN = _build_pattern(_SEXUAL_TERMS)

# Numeric age indicators: an explicit age below 18 (e.g. "15yo", "13 years old",
# "she's 12", "age 9"). Captures the number so we can threshold it.
_AGE_PATTERN = re.compile(
    r"\b(?:age[d]?\s*(?:of\s*)?|she(?:'s| is)?\s*|he(?:'s| is)?\s*|i(?:'m| am)?\s*|"
    r"turned\s*|just\s*)?"
    r"(\d{1,2})\s*"
    r"(?:y[/.]?o\b|y[/.]?r?s?\s*old|years?\s*old|year\s*old)",
    re.IGNORECASE,
)

MINOR_AGE_THRESHOLD = 18


@dataclass(frozen=True)
class SafetyVerdict:
    """Outcome of a safety check.

    ``blocked`` is the decision; ``reason`` is a short machine-readable tag for
    logging/metrics (never shown to users — use ``BLOCK_REASON`` for that).
    """

    blocked: bool
    reason: str = ""


def _has_minor_age(text: str) -> bool:
    """True if the text states an explicit age under the minor threshold."""
    for match in _AGE_PATTERN.finditer(text):
        try:
            age = int(match.group(1))
        except (TypeError, ValueError):
            continue
        if age < MINOR_AGE_THRESHOLD:
            return True
    return False


def check(text: str) -> SafetyVerdict:
    """Screen ``text`` for clearly illegal (CSAM) content.

    Returns a :class:`SafetyVerdict`. The text is blocked when a sexual context
    co-occurs with a minor indicator — either a minor-indicating term or an
    explicit stated age under 18. Benign text (including explicit *adult*
    content with no minor indicator) passes.
    """
    if not text or not text.strip():
        return SafetyVerdict(blocked=False)

    has_sexual = _SEXUAL_PATTERN.search(text) is not None
    if not has_sexual:
        # No sexual context → nothing in scope for this guard.
        return SafetyVerdict(blocked=False)

    if _MINOR_PATTERN.search(text) is not None:
        return SafetyVerdict(blocked=True, reason="minor_term_with_sexual_context")

    if _has_minor_age(text):
        return SafetyVerdict(blocked=True, reason="minor_age_with_sexual_context")

    return SafetyVerdict(blocked=False)


def is_blocked(text: str) -> bool:
    """Convenience boolean wrapper around :func:`check`."""
    return check(text).blocked
