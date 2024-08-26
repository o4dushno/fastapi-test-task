import uuid

from sqlalchemy.future import select
from functools import lru_cache

from src.auth.models import User


async def cached_get_user_by_uuid(db, _uuid: uuid.UUID):
    @lru_cache(maxsize=1000)
    async def _get_user_by_uuid(uuid):
        result = await db.execute(select(User).where(User.id == uuid))
        return result.scalars().first()
    return await _get_user_by_uuid(_uuid)
