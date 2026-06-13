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
        """Stream assistant token deltas; persist the full turn when done."""
        await ctx.append_turn(conversation, "user", user_text, db, valkey)
        recent = await ctx.load_recent(conversation.id, db, valkey)
        # load_recent already includes the just-appended user turn; drop it so we
        # don't duplicate it as the final user message.
        history = recent[:-1] if recent and recent[-1]["role"] == "user" else recent
        messages = ctx.build_messages(conversation, history, user_text)

        collected: list[str] = []
        async for delta in self.provider.stream(messages):
            collected.append(delta)
            yield delta

        reply = "".join(collected).strip()
        if reply:
            await ctx.append_turn(conversation, "assistant", reply, db, valkey)
            await ctx.maybe_summarize(conversation, db, self.provider)

    async def respond_bubbles(
        self, conversation: Conversation, user_text: str, db: AsyncSession, valkey
    ) -> list[str]:
        """Non-streaming path: return the reply as texting-style bubbles."""
        reply = "".join(
            [chunk async for chunk in self.respond_stream(conversation, user_text, db, valkey)]
        )
        return split_bubbles(reply)
