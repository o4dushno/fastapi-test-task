import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.auth.models import User, user_private_chats, user_public_chats
from src.core.jwt import cached_get_user_by_uuid
from src.database.database import Base


class PublicChat(Base):
    __tablename__ = "public_chats"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, index=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="public_chat",
        cascade="all, delete-orphan"
    )
    users: Mapped[list["User"]] = relationship(
        "User", secondary=user_public_chats, back_populates="public_chats"
    )

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.id}, name={self.name}>"


class PrivateChat(Base):
    __tablename__ = "private_chats"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, index=True, default=uuid.uuid4
    )

    users: Mapped[list["User"]] = relationship(secondary=user_private_chats, back_populates="private_chats")

    conversation: Mapped["Conversation"] = relationship(
        back_populates="private_chats",
        foreign_keys="[Conversation.private_chat_id]",
    )

    def __str__(self):
        return f"Чат <{self.id}>"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, index=True, default=uuid.uuid4
    )
    content: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(server_default=func.datetime('now'))

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.id"))

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

    async def to_dict(self, db):
        return {
            "id": str(self.id),
            "content": self.content,
            "timestamp": str(self.timestamp),
            "user_id": str(self.user_id),
            "user_email": getattr(
                await cached_get_user_by_uuid(db, self.user_id),
                'email', None
            ),
            "conversation_id": str(self.conversation_id),
        }

    def __repr__(self):
        return f"Message(id={self.id}, timestamp={self.timestamp})"


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, index=True, default=uuid.uuid4
    )
    is_group: Mapped[bool] = mapped_column(default=False)
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation")

    public_chat_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("public_chats.id"), nullable=True
    )
    public_chat: Mapped["PublicChat"] = relationship(
        back_populates="conversations",
    )

    private_chat_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("private_chats.id"), nullable=True
    )
    private_chats: Mapped["PrivateChat"] = relationship(
        back_populates="conversation", uselist=False,

    )

    def __str__(self):
        return f"Диалог {self.id}"

    def __repr__(self):
        return f"Conversation(id={self.id}, is_group={self.is_group})"
