from pydantic import BaseModel


class CreatePrivateChatUser(BaseModel):
    user2_email: str


class ChatRoomCreate(BaseModel):
    room_name: str
