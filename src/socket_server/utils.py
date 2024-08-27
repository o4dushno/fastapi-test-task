from typing import List
from uuid import UUID

from src.chats import models
from src.socket_server import crud
from src.socket_server.exceptions import SocketPermissionError


async def check_dialog_permission(
    db, dialog: crud.Dialog | None, user: models.User
) -> bool:
    if dialog is None:
        return False

    if isinstance(dialog, models.PublicChat):
        return True

    return await crud.has_private_chat_permission(db, dialog.id, user.id)


async def get_message_history(
    db, user: models.User, conversation_id: UUID
) -> List[models.Message] | SocketPermissionError:

    data = await crud.get_dialog_by_conversation_id(db, conversation_id)

    if not await check_dialog_permission(db, data, user):
        return SocketPermissionError("You are not a member of this chat room")
    return await crud.get_conversation_messages(db, conversation_id)


async def have_enter_room_permission(
    db, user: models.User, conversation_id: UUID
) -> bool:
    dialog = await crud.get_dialog_by_conversation_id(db, conversation_id)
    return await check_dialog_permission(db, dialog, user)


async def save_user_message(
    db, user: models.User, message: str, conversation_id: UUID
) -> None:
    await crud.create_message(db, user, message, conversation_id)
