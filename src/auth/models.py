import uuid
from datetime import datetime
from sqlalchemy import select, ForeignKey, Column, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from src.database.database import Base
from src.core.hash import verify_password


user_private_chats = Table(
    'user_private_chats',
    Base.metadata,
    Column('user_id', ForeignKey('users.id'), primary_key=True),
    Column('private_chat_id', ForeignKey('private_chats.id'), primary_key=True)
)

user_public_chats = Table(
    "user_public_chats", Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("public_chat_id", ForeignKey("public_chats.id"), primary_key=True)
)


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, index=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.datetime('now'))
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.datetime('now'), server_onupdate=func.datetime('now'),
        onupdate=func.datetime('now')
    )

    messages: Mapped[list["Message"]] = relationship()
    private_chats: Mapped[list["PrivateChat"]] = relationship(
        secondary=user_private_chats, back_populates="users"
    )
    public_chats: Mapped[list["PublicChat"]] = relationship(
        secondary=user_public_chats, back_populates="users"
    )

    @classmethod
    async def find_by_email(cls, db: AsyncSession, email: str):
        query = select(cls).where(cls.email == email)
        result = await db.execute(query)
        return result.scalars().first()

    @classmethod
    async def authenticate(cls, db: AsyncSession, email: str, password: str):
        user = await cls.find_by_email(db=db, email=email)
        if not user or not verify_password(password, user.password):
            return False
        return user
