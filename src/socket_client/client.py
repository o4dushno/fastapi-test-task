import socketio
import asyncio

import socketio.exceptions


sio = socketio.AsyncClient()


@sio.event
async def connect():
    print('Successfully connected to socket.io server!')


@sio.event
async def disconnect():
    print('Disconnected from socket.io server')


@sio.event
async def receive_message(data):
    print(f'{data.get("user")}: {data.get("message")}')


@sio.event
async def message_history(data):
    for message in data:
        print(f'{message.get("user_email")} ({message.get("timestamp")}): {message.get("content")}')


@sio.event
async def error(data):
    print(f'Error: {data}')


async def ainput(prompt: str = ""):
    # Неблокирующий input
    return await asyncio.to_thread(input, prompt)


async def send_messages(room):
    print("System: Введите exit для выхода")
    while True:
        message = await ainput("Ваше сообщение: ")
        if message.lower() == "exit":
            print("System: Exiting...")
            break

        await sio.emit(
            "send_message", data={"message": message, "room": room}
        )
        await sio.sleep(.1)


async def start_client():
    token = input("Token:\n")
    room = input("ID комнаты:\n")

    try:
        await sio.connect(
            'http://localhost:8081/',
            auth={"token": token},
            socketio_path='/ws/socket.io/',
        )
    except socketio.exceptions.ConnectionError:
        print("Failed to connect to socket.io server")
        return

    # Присоединяемся к чату
    result = await sio.call("enter_room", room)
    if result is None:
        # Ждем получения истории сообщений
        await sio.call("message_history", room)
        await send_messages(room)
        await sio.emit("leave_room", room)
    await sio.disconnect()


if __name__ == '__main__':
    asyncio.run(start_client())
