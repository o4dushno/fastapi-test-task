from uuid import UUID

from typing import TypeAlias

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.chats import models


Dialog: TypeAlias = models.PrivateChat | models.PublicChat


async def get_conversation_by_id(
    db, conversation_id: UUID
) -> models.Conversation:
    result = await db.execute(
        select(models.Conversation)
        .where(models.Conversation.id == conversation_id)
    )
    return result.scalars().first()


async def get_dialog_by_conversation_id(
    db, conversation_id: UUID
) -> Dialog | None:

    conversation = await db.execute(
        select(models.Conversation)
        .options(
            joinedload(models.Conversation.public_chat).joinedload(
                models.PublicChat.users
            ),
            joinedload(models.Conversation.private_chats).joinedload(
                models.PrivateChat.users
            ),
        ).where(models.Conversation.id == conversation_id)
    )
    data = conversation.scalars().first()
    if not data:
        return None
    return data.public_chat or data.private_chats


async def get_conversation_messages(
    db, conversation_id: UUID
) -> models.Message:

    result = await db.execute(
        select(models.Message)
        .where(models.Message.conversation_id == conversation_id)
        .order_by(models.Message.timestamp)
    )
    return result.scalars().all()


async def create_message(
    db, user: models.User, message: str, conversation_id: UUID
) -> None:

    db_message = models.Message(
        user_id=user.id, content=message, conversation_id=conversation_id
    )
    db.add(db_message)
    await db.commit()
