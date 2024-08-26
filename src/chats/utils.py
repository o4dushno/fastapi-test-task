import uuid

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.chats.models import Conversation, PublicChat


async def create_room_conversation(db, chat_id: uuid.UUID):
    new_conversation = Conversation(is_group=True)

    public_chat = await db.execute(
        select(PublicChat)
        .options(joinedload(PublicChat.conversations))
        .where(PublicChat.id == chat_id)
    )
    public_chat = public_chat.scalars().first()

    public_chat.conversations.append(new_conversation)
    await db.commit()
    return new_conversation
