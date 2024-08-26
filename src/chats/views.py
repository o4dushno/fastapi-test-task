import uuid
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.chats import models
from src.chats import schemas
from src.chats.crud import (
    create_public_chat_crud,
    create_private_chat_crud,
    enjoy_user_to_public_chat,
    get_public_chat_by_uuid,
    public_chat_exists,
    users_private_chat_exists,
)
from src.chats.utils import create_room_conversation
from src.core.jwt import get_current_user
from src.core.exceptions import BadRequestException, NotFoundException
from src.database.dependencies import get_db


router = APIRouter()


@router.post("/private_chat")
async def create_private_chat(
    user2: schemas.CreatePrivateChatUser,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Создать приватный чат с пользователем."""
    second_user = await models.User.find_by_email(
        db=db, email=user2.user2_email
    )
    if not second_user:
        raise NotFoundException(detail="User not found")

    if second_user is current_user:
        raise BadRequestException(detail="You can't create chat with yourself")

    exists_private_chat = await users_private_chat_exists(
        db, [current_user, second_user]
    )

    if exists_private_chat:
        raise BadRequestException(
            detail=f"Private chat with user {user2.user2_email} already exists"
        )

    new_chat, conversation = await create_private_chat_crud(
        db, [current_user, second_user]
    )
    return {
        "chat_id": new_chat.id,
        "conversation_id": conversation.id
    }


@router.post("/chat/")
async def create_public_chat(
    chatroom: schemas.ChatRoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Создать публичный чат."""
    if await public_chat_exists(db, chatroom.chat_name):
        raise BadRequestException(detail="Chat already exists")

    public_chat, conversation = await create_public_chat_crud(
        db, chatroom.chat_name, current_user.id
    )
    return {
        "chat_id": public_chat.id,
        "conversation_id": conversation.id
    }


@router.post("/chat/{chat_id}/enjoy")
async def enjoy_public_chat(
    chat_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Присоединиться к публичному чату."""
    public_chat = await get_public_chat_by_uuid(db, uuid.UUID(chat_id))
    if not public_chat:
        raise NotFoundException(detail="Chat not found")

    if current_user.id in [user.id for user in public_chat.users]:
        raise BadRequestException(
            detail="You are already a member of this room"
        )

    await enjoy_user_to_public_chat(db, public_chat, current_user)
    return Response()


@router.post("/chat/{chat_id}/create_conversation")
async def create_public_chat_conversation(
    chat_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Создание комнаты в публичном чате."""
    uuid_chat_id = uuid.UUID(chat_id)
    public_chat = await get_public_chat_by_uuid(db, uuid_chat_id)
    if current_user.id not in [user.id for user in public_chat.users]:
        # Чтобы создать комнату в чате надо к нему присоединиться
        raise BadRequestException(detail="You are not a member of this room")

    conversation = await create_room_conversation(db, uuid_chat_id)
    return {"chat_id": chat_id, "conversation_id": conversation.id}
