from typing import Annotated, Literal

from pydantic import BaseModel, Field, constr

username_type = Literal["mobile", "email"]


class PagesToPrint(BaseModel):
    pages_to_print: int


class RequestTOTP(BaseModel):
    username: constr(to_lower=True, min_length=6, max_length=50)
    username_type: username_type


class RequestLogin(RequestTOTP):
    totp: Annotated[str, Field(pattern=r"^[0-9]{6}$")]


class JWTToken(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str
    username_type: username_type
    scopes: list[str] = []


class StatusReply(BaseModel):
    status: str


class MeReplyUser(BaseModel):
    user_id: int
    name: str
    token: str
    member_type: str
    expires: str


class MeReply(BaseModel):
    users: list[MeReplyUser]
