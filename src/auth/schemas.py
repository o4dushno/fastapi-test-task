from datetime import datetime
from pydantic import BaseModel, UUID4, validator, EmailStr


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: UUID4

    class Config:
        orm_mode = True

    @validator("id")
    def convert_to_str(cls, v, values, **kwargs):
        return str(v) if v else v


class UserRegister(UserBase):
    password: str
    confirm_password: str

    @validator("confirm_password")
    def verify_password_match(cls, v, values, **kwargs):
        password = values.get("password")

        if v != password:
            raise ValueError("The two passwords did not match.")

        return v


class JwtTokenSchema(BaseModel):
    token: str
    payload: dict
    expire: datetime


class TokenPair(BaseModel):
    access: JwtTokenSchema
    refresh: JwtTokenSchema


class SuccessResponseScheme(BaseModel):
    msg: str


class MailBodySchema(BaseModel):
    token: str
    type: str


class MailTaskSchema(BaseModel):
    user: User
    body: MailBodySchema
