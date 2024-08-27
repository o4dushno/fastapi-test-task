import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Response,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import schemas
from src.chats import models
from src.auth.forms import OAuth2PasswordRequestCustomForm
from src.core.hash import get_password_hash
from src.core.jwt import (
    create_token_pair,
    decode_access_token,
    mail_token,
    add_refresh_token_cookie,
    SUB,
)
from src.database.dependencies import get_db
from src.core.exceptions import (
    BadRequestException,
    NotFoundException,
    ForbiddenException,
)
from src.auth.tasks import user_mail_event


router = APIRouter()


@router.post(
    "/register/",
    tags=['auth'],
    response_model=schemas.User,
    summary="Регистрация пользователя",
)
async def register(
    data: schemas.UserRegister,
    bg_task: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    user = await models.User.find_by_email(db=db, email=data.email)
    if user:
        raise HTTPException(status_code=400, detail="Email has already registered")

    # hashing password
    user_data = data.dict(exclude={"confirm_password"})
    user_data["password"] = get_password_hash(user_data["password"])

    # save user to db
    user = models.User(**user_data)
    user.is_active = False
    await user.save(db=db)

    # send verify email
    user_schema = schemas.User.from_orm(user)
    verify_token = mail_token(user_schema)

    mail_task_data = schemas.MailTaskSchema(
        user=user_schema, body=schemas.MailBodySchema(type="verify", token=verify_token)
    )
    bg_task.add_task(user_mail_event, mail_task_data)

    return user_schema


@router.post(
    "/login/",
    tags=['auth'],
    response_model=schemas.TokenScheme,
    summary="Авторизация пользователя",
)
async def login(
    response: Response,
    data: OAuth2PasswordRequestCustomForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await models.User.authenticate(
        db=db, email=data.username, password=data.password
    )

    if not user:
        raise BadRequestException(detail="Incorrect email or password")

    if not user.is_active:
        raise ForbiddenException()

    user = schemas.User.from_orm(user)

    token_pair = create_token_pair(user=user)

    add_refresh_token_cookie(response=response, token=token_pair.refresh.token)

    return {"access_token": token_pair.access.token, "token_type": "bearer"}


@router.get(
    "/verify/",
    tags=['auth'],
    response_model=schemas.SuccessResponseScheme,
    summary="Верификация пользователя",
)
async def verify(token: str, db: AsyncSession = Depends(get_db)):
    payload = await decode_access_token(token=token, db=db)
    user = await models.User.find_by_id(db=db, id=uuid.UUID(payload[SUB]))
    if not user:
        raise NotFoundException(detail="User not found")

    user.is_active = True
    await user.save(db=db)
    return {"msg": "Successfully activated"}
