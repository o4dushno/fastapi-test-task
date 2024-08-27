from uuid import UUID

from typing import TypeAlias, List

from sqlalchemy import select, exists
from sqlalchemy.orm import joinedload

from src.auth.models import User, user_private_chats
from src.chats.models import Message, PrivateChat, PublicChat, Conversation


Dialog: TypeAlias = PrivateChat | PublicChat


async def get_conversation_by_id(
    db, conversation_id: UUID
) -> Conversation:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
    )
    return result.scalars().first()


async def get_dialog_by_conversation_id(
    db, conversation_id: UUID
) -> Dialog | None:

    conversation = await db.execute(
        select(Conversation)
        .options(
            joinedload(Conversation.public_chat).joinedload(PublicChat.users),
            joinedload(Conversation.private_chats).joinedload(
                PrivateChat.users
            ),
        ).where(Conversation.id == conversation_id)
    )
    data = conversation.scalars().first()
    if not data:
        return None
    return data.public_chat or data.private_chats


async def get_conversation_messages(
    db, conversation_id: UUID
) -> List[Message]:

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.timestamp)
    )
    return result.scalars().all()


async def create_message(
    db, user: User, message: str, conversation_id: UUID
) -> None:

    db_message = Message(
        user_id=user.id, content=message, conversation_id=conversation_id
    )
    db.add(db_message)
    await db.commit()


async def has_private_chat_permission(
    db, chat_id: UUID, user_id: UUID
) -> bool:
    stmt = select(
        exists().where(
            user_private_chats.c.private_chat_id == chat_id,
            user_private_chats.c.user_id == user_id,
        )
    )
    result = await db.execute(stmt)
    return result.scalar()
