from uuid import UUID
from pydantic import BaseModel


class CreatePrivateChatUser(BaseModel):
    user2_email: str


class ChatRoomCreate(BaseModel):
    chat_name: str


class ChatConversationResponse(BaseModel):
    chat_id: UUID
    conversation_id: UUID
