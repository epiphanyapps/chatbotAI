"""ChatService — orchestrates a single turn end to end.

Builds context → streams from the provider → persists both sides of the turn →
folds older history into a summary. Two entry points share all of that:
``respond_stream`` (token stream for the WebSocket) and ``respond_bubbles``
(full reply split into texting-style bubbles for REST / Telegram).
"""

from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine import context as ctx
from app.engine import safety
from app.engine.provider import LLMProvider, get_provider
from app.models.conversation import Conversation

# Personas emit multiple text bubbles separated by a line containing only this.
BUBBLE_DELIMITER = "---"


class BlockedContentError(Exception):
    """Raised when generated output is blocked by the safety guard.

    The reply is neither persisted nor sent. Callers should surface a generic
    error to the client without echoing any content.
    """


def split_bubbles(text: str) -> list[str]:
    """Split a reply into individual text bubbles on the delimiter line."""
    parts = [p.strip() for p in text.split(BUBBLE_DELIMITER)]
    bubbles = [p for p in parts if p]
    return bubbles or [text.strip()]


class ChatService:
    def __init__(self, provider: LLMProvider | None = None) -> None:
        self.provider = provider or get_provider()

    async def get_or_create_conversation(
        self, user_id: int, db: AsyncSession, persona: str = "sophia"
    ) -> Conversation:
        """Return the user's active conversation, creating one if needed."""
        result = await db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.last_message_at.desc())
            .limit(1)
        )
        conversation = result.scalar_one_or_none()
        if conversation is None:
            conversation = Conversation(user_id=user_id, persona=persona)
            db.add(conversation)
            await db.flush()
        return conversation

    async def respond_stream(
        self, conversation: Conversation, user_text: str, db: AsyncSession, valkey
    ) -> AsyncIterator[str]:
        """Stream assistant token deltas LIVE; screen the full reply at the end.

        Tokens are forwarded to the client as they arrive (no output buffering),
        so live streaming is preserved, while the full text is accumulated. When
        the stream completes the assembled reply is screened by the safety guard:

          - SAFE  → persist the assistant turn and warm the cache as normal.
          - BLOCKED (e.g. CSAM) → raise :class:`BlockedContentError`. The
            assistant turn is NEITHER persisted NOR pushed to the cache; the
            client has already received the tokens and must retract them (the WS
            handler emits a ``retract`` event). Any delta already sent cannot be
            un-sent on the wire — retraction is a client-side discard.

        Valkey is not transactional with Postgres, so we must not push a turn to
        the cache window before it is durably persisted: if the provider throws
        mid-stream the DB transaction rolls back, but a cache push would survive
        as an orphaned user-only turn and poison the next prompt (issue #21).

        Ordering is therefore:
          1. load recent history *before* persisting the current user turn, so a
             cold-cache hydration from Postgres can never see (or warm the cache
             with) an un-paired user turn;
          2. assemble the messages (user_text appears exactly once);
          3. persist the user turn to Postgres only (no cache push);
          4. stream tokens live — a provider failure here rolls back with nothing
             pushed to Valkey;
          5. screen the assembled reply. If SAFE, persist the assistant turn and
             push *both* sides to the window together. If BLOCKED, persist only
             the user turn to the cache (it is durable in Postgres after the
             handler commits) so Valkey and Postgres stay consistent, then raise.
        """
        recent = await ctx.load_recent(conversation.id, db, valkey)
        messages = ctx.build_messages(conversation, recent, user_text)

        # Persist the user turn durably first, but keep it out of the cache until
        # we know the turn's fate — see the docstring above.
        await ctx.append_turn(conversation, "user", user_text, db, valkey, push_cache=False)

        # Stream tokens to the client live while accumulating the full reply.
        collected: list[str] = []
        async for delta in self.provider.stream(messages):
            collected.append(delta)
            yield delta

        reply = "".join(collected).strip()
        if not reply:
            return

        if safety.is_blocked(reply):
            # Blocked output: do NOT persist or cache the assistant turn. The user
            # turn is committed by the handler, so push just it to the window to
            # keep Valkey consistent with Postgres (no orphan, no missing turn).
            await ctx.push_window(
                conversation.id, [{"role": "user", "content": user_text}], valkey
            )
            raise BlockedContentError(safety.BLOCK_REASON)

        await ctx.append_turn(
            conversation, "assistant", reply, db, valkey, push_cache=False
        )
        # Both sides are now in the DB; warm the cache as one atomic pair so the
        # window can never hold a user turn without its reply.
        await ctx.push_window(
            conversation.id,
            [
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": reply},
            ],
            valkey,
        )
        await ctx.maybe_summarize(conversation, db, self.provider)

    async def respond_bubbles(
        self, conversation: Conversation, user_text: str, db: AsyncSession, valkey
    ) -> list[str]:
        """Non-streaming path: return the reply as texting-style bubbles."""
        reply = "".join(
            [chunk async for chunk in self.respond_stream(conversation, user_text, db, valkey)]
        )
        return split_bubbles(reply)
