import uuid
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.chats import models
from src.chats import schemas
from src.chats.crud import (
    create_chat_room,
    create_private_chat,
    enjoy_user_to_public_chat,
    get_public_chat_by_uuid,
)
from src.chats.utils import create_room_conversation
from src.core.jwt import get_current_user
from src.core.exceptions import BadRequestException, NotFoundException
from src.database.dependencies import get_db


router = APIRouter()


@router.post("/private_chat")
async def create_private_chat_view(
    user2: schemas.CreatePrivateChatUser,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Создать приватный чат с пользователем."""
    # TODO Запретить создавать диалог повторно
    second_user = await models.User.find_by_email(
        db=db, email=user2.user2_email
    )
    if not second_user:
        raise NotFoundException(detail="User not found")

    if second_user is current_user:
        raise BadRequestException(detail="You can't create chat with yourself")

    new_chat = await create_private_chat(db, [current_user, second_user])
    return {
        "chat_id": new_chat.id,
        "conversation_id": new_chat.conversation_id
    }


@router.post("/chat/")
async def create_chat_room_view(
    chatroom: schemas.ChatRoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    public_chat, conversation = await create_chat_room(db, chatroom.room_name, current_user.id)
    return {
        "room_id": public_chat.id,
        "conversation_id": conversation.id
    }


@router.post("/chat/{chat_id}/enjoy")
async def enjoy_public_chat(
    chat_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Вступить в чат."""
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
    uuid_chat_id = uuid.UUID(chat_id)
    public_chat = await get_public_chat_by_uuid(db, uuid_chat_id)
    if current_user.id not in [user.id for user in public_chat.users]:
        # Чтобы создать комнату в чате надо к нему присоединиться
        raise BadRequestException(detail="You are not a member of this room")

    conversation = await create_room_conversation(db, uuid_chat_id)
    return {"room_id": chat_id, "conversation_id": conversation.id}
