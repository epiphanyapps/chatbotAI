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
from app.engine.provider import LLMProvider, get_provider
from app.models.conversation import Conversation

# Personas emit multiple text bubbles separated by a line containing only this.
BUBBLE_DELIMITER = "---"


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
        """Stream assistant token deltas; persist the full turn when done.

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
          4. stream — a failure here rolls back with nothing pushed to Valkey;
          5. persist the assistant turn, then push *both* sides to the window
             together, only after the full turn succeeded.
        """
        recent = await ctx.load_recent(conversation.id, db, valkey)
        messages = ctx.build_messages(conversation, recent, user_text)

        # Persist the user turn durably first, but keep it out of the cache until
        # the assistant reply lands — see the docstring above.
        await ctx.append_turn(conversation, "user", user_text, db, valkey, push_cache=False)

        collected: list[str] = []
        async for delta in self.provider.stream(messages):
            collected.append(delta)
            yield delta

        reply = "".join(collected).strip()
        if reply:
            await ctx.append_turn(
                conversation, "assistant", reply, db, valkey, push_cache=False
            )
            # Both sides are now in the DB; warm the cache as one atomic pair so
            # the window can never hold a user turn without its reply.
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
