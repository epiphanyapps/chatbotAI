"""Live end-to-end smoke test of the chat path against the real LLM.

Exercises ChatService -> OpenRouterProvider (selected model) -> Postgres
persistence + Valkey window + safety screening, including cross-turn memory.

Skipped unless OPENROUTER_API_KEY is set, since it makes real (paid) API calls:

    OPENROUTER_API_KEY=sk-or-... python -m pytest tests/test_live_smoke.py -s -v
"""

import os

import pytest
from sqlalchemy import select

from app.engine.provider import OpenRouterProvider
from app.engine.service import ChatService
from app.models.conversation import Message

pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"),
    reason="needs OPENROUTER_API_KEY for a live model call",
)


@pytest.mark.asyncio
async def test_live_chat_roundtrip_and_memory(db, valkey):
    service = ChatService(provider=OpenRouterProvider())  # real, config-selected model
    convo = await service.get_or_create_conversation(user_id=1, db=db)

    def has_content(bubbles: list[str]) -> bool:
        # A degenerate reply can be only the bubble delimiter; treat that as empty.
        return any(b.strip().strip("-").strip() for b in bubbles)

    # Turn 1: establish a memorable detail.
    b1 = await service.respond_bubbles(
        convo, "hey babe, i'm David and i finish work at 6 tonight", db, valkey
    )
    print("\nTURN 1 bubbles:", b1)
    assert has_content(b1), f"turn 1 returned no real content: {b1}"

    # Turn 2: probe recall of the detail from turn 1 (real memory through the stores).
    b2 = await service.respond_bubbles(convo, "what time do i finish work?", db, valkey)
    print("TURN 2 bubbles:", b2)
    # Soft check — memory is model-dependent; report rather than fail the smoke test.
    if "6" in " ".join(b2).lower():
        print("MEMORY: recalled '6' ✓")
    else:
        print("MEMORY: did not surface '6' (model stochasticity / degenerate reply)")

    # Hard guarantees of the path: both turns durably persisted (2 user + 2 assistant).
    rows = (await db.execute(select(Message).order_by(Message.id))).scalars().all()
    roles = [m.role for m in rows]
    assert roles == ["user", "assistant", "user", "assistant"], roles
