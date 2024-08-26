import socketio
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from src.auth.views import router as auth_router
from src.chats.views import router as chats_router
from src.socket_server.sockets import sio

app = FastAPI(default_response_class=ORJSONResponse)

app.include_router(chats_router)
app.include_router(auth_router)

app.mount("/ws", socketio.ASGIApp(sio, other_asgi_app=app))
