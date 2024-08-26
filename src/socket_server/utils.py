from typing import List, TypeAlias
from uuid import UUID

from src.chats import models
from src.socket_server import crud
from src.socket_server.exceptions import SocketPermissionError


Dialog: TypeAlias = models.PrivateChat | models.PublicChat


def check_dialog_permission(dialog: Dialog | None, user: models.User) -> bool:
    return dialog is not None and (
        isinstance(dialog, models.PublicChat)
        or user.id in [user.id for user in dialog.users]
    )


async def get_message_history(
    db, user: models.User, conversation_id: UUID
) -> List[models.Message] | SocketPermissionError:

    data: Dialog | None = await crud.get_dialog_by_conversation_id(
        db, conversation_id
    )

    if not check_dialog_permission(data, user):
        return SocketPermissionError("You are not a member of this chat room")
    return await crud.get_conversation_messages(db, conversation_id)


async def have_enter_room_permission(
    db, user: models.User, conversation_id: UUID
) -> bool:
    data: Dialog | None = await crud.get_dialog_by_conversation_id(
        db, conversation_id
    )
    return check_dialog_permission(data, user)


async def save_user_message(
    db, user: models.User, message: str, conversation_id: UUID
) -> None:
    await crud.create_message(db, user, message, conversation_id)
