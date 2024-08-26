import socketio
import uuid

from src.core.jwt import get_current_user
from src.database.database import SessionFactory
from src.socket_server.exceptions import (
    SocketPermissionError,
    SocketUserNotFoundError,
)
from src.socket_server.utils import (
    get_message_history,
    have_enter_room_permission,
    save_user_message,
)


sio = socketio.AsyncServer(async_mode='asgi')

connected_users = {}


@sio.event
async def connect(sid, environ, auth):
    token = auth.get("token")

    if not token:
        await sio.emit('error', to=sid, data={"message": "Token missing"})
        return False

    # Проверяем данные пользователя
    async with SessionFactory() as db:
        try:
            user = await get_current_user(token, db)
            if not user:
                raise SocketUserNotFoundError()
        except Exception as e:
            print(f"Authentication failed: {e}")
            await sio.emit(
                'error', to=sid, data={"message": "Authentication failed"}
            )
            return False

    # Сохраняем ID сессии и пользователя
    connected_users[sid] = user


@sio.event
async def enter_room(sid, room_id):
    async with SessionFactory() as db:
        # Проверяем что пользователю можно присоединиться к комнате
        if not await have_enter_room_permission(
            db, connected_users[sid], uuid.UUID(room_id)
        ):
            await sio.emit(
                'error', to=sid,
                data={"room_id": room_id, "message": "Access denied"},
            )
            return False

    await sio.enter_room(sid, str(room_id))
    print(f"User {sid} joined room {room_id}")


@sio.event
async def leave_room(sid, room_id):
    await sio.leave_room(sid, str(room_id))


@sio.event
async def send_message(sid, data):
    room = data.get('room')
    message = data.get('message')

    # Для отправки сообщения нужен номер комнаты и сообщение
    if not room or message is None:
        await sio.emit(
            'error', data={"message": "Room or message missing"}, to=sid
        )
        return

    # Сохраняем сообщение пользователя в БД
    async with SessionFactory() as db:
        await save_user_message(
            db, connected_users[sid], message, uuid.UUID(room)
        )

    # Отправляем сообщение всем участникам комнаты
    await sio.emit(
        'receive_message',
        data={"user": connected_users[sid].email, "message": message},
        room=room
    )


@sio.event
async def message_history(sid, room_id):
    async with SessionFactory() as db:
        # Получаем историю сообщений
        messages = await get_message_history(
            db, connected_users[sid], uuid.UUID(room_id)
        )
        if isinstance(messages, SocketPermissionError):
            # Ошибка если пользователю нельзя читать этот диалог
            await sio.emit(
                'error', to=sid,
                data={"room_id": room_id, "message": "Access denied"},
            )
            return
        serialized_mgs = [await message.to_dict(db) for message in messages]
    await sio.emit('message_history', data=serialized_mgs, to=sid)


@sio.event
async def disconnect(sid):
    if sid in connected_users:
        del connected_users[sid]
    print(f"User disconnected: {sid}")
