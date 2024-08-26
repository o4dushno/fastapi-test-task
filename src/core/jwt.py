import uuid
import sys
from datetime import timedelta, datetime, timezone

from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Response, Depends
from fastapi.security import OAuth2PasswordBearer

from src.auth.schemas import User, TokenPair, JwtTokenSchema
from src.auth.utils import cached_get_user_by_uuid
from src.core import config
from src.core.exceptions import AuthFailedException, AuthTokenExpiredException
from src.database.dependencies import get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login/")


SUB = "sub"
EXP = "exp"
IAT = "iat"
JTI = "jti"


def _get_utc_now():
    if sys.version_info >= (3, 2):
        # For Python 3.2 and later
        current_utc_time = datetime.now(timezone.utc)
    else:
        # For older versions of Python
        current_utc_time = datetime.utcnow()
    return current_utc_time


def _create_access_token(
    payload: dict, minutes: int | None = None
) -> JwtTokenSchema:
    expire = _get_utc_now() + timedelta(
        minutes=minutes or config.ACCESS_TOKEN_EXPIRES_MINUTES
    )

    payload[EXP] = expire

    token = JwtTokenSchema(
        token=jwt.encode(
            payload, config.SECRET_KEY, algorithm=config.ALGORITHM
        ),
        payload=payload,
        expire=expire,
    )

    return token


def _create_refresh_token(payload: dict) -> JwtTokenSchema:
    expire = _get_utc_now() + timedelta(
        minutes=config.REFRESH_TOKEN_EXPIRES_MINUTES
    )

    payload[EXP] = expire

    token = JwtTokenSchema(
        token=jwt.encode(
            payload, config.SECRET_KEY, algorithm=config.ALGORITHM
        ),
        expire=expire,
        payload=payload,
    )

    return token


def create_token_pair(user: User) -> TokenPair:
    payload = {SUB: str(user.id), JTI: str(uuid.uuid4()), IAT: _get_utc_now()}

    return TokenPair(
        access=_create_access_token(payload={**payload}),
        refresh=_create_refresh_token(payload={**payload}),
    )


async def decode_access_token(token: str, db: AsyncSession):
    try:
        payload = jwt.decode(
            token, config.SECRET_KEY, algorithms=[config.ALGORITHM]
        )
    except JWTError:
        raise AuthFailedException()

    return payload


def mail_token(user: User):
    """Return 2 hour lifetime access_token"""
    payload = {SUB: str(user.id), JTI: str(uuid.uuid4()), IAT: _get_utc_now()}
    return _create_access_token(payload=payload, minutes=2 * 60).token


def add_refresh_token_cookie(response: Response, token: str):
    exp = _get_utc_now() + timedelta(
        minutes=config.REFRESH_TOKEN_EXPIRES_MINUTES
    )
    exp.replace(tzinfo=timezone.utc)

    response.set_cookie(
        key="refresh",
        value=token,
        expires=int(exp.timestamp()),
        httponly=True,
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    credentials_exception = AuthTokenExpiredException()
    try:
        payload = jwt.decode(
            token, config.SECRET_KEY, algorithms=[config.ALGORITHM]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await cached_get_user_by_uuid(db, uuid.UUID(user_id))
    if user is None:
        raise credentials_exception
    return user
