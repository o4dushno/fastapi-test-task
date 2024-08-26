from uuid import UUID
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError

from src.auth.models import User
from src.chats.models import Conversation, PrivateChat, PublicChat


async def create_private_chat(db, users: List[User]):
    try:
        new_conversation = Conversation(is_group=False)
        db.add(new_conversation)
        await db.flush()

        new_chat = PrivateChat(conversation_id=new_conversation.id)
        new_chat.users.extend(users)
        db.add(new_chat)
        await db.commit()
        await db.refresh(new_chat)
        return new_chat
    except SQLAlchemyError as e:
        await db.rollback()
        raise e


async def create_chat_room(db, name: str, owner_id: UUID):
    new_conversation = Conversation(is_group=True)
    db.add(new_conversation)
    await db.flush()

    new_public_chat = PublicChat(
        name=name,
        owner_id=owner_id,
    )
    new_public_chat.conversations.append(new_conversation)
    db.add(new_public_chat)
    await db.commit()
    await db.refresh(new_public_chat)
    await db.refresh(new_conversation)
    return new_public_chat, new_conversation


async def get_public_chat_by_uuid(db, chat_id: UUID):
    public_chat = await db.execute(
        select(PublicChat)
        .options(joinedload(PublicChat.users))
        .where(PublicChat.id == chat_id)
    )
    return public_chat.scalars().first()


async def enjoy_user_to_public_chat(
    db, public_chat: PublicChat, current_user: User
):
    public_chat.users.append(current_user)
    db.add(public_chat)
    await db.commit()
