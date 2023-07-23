from pydantic import BaseModel
from pydantic.typing import Literal


class RequestTOTP(BaseModel):
    username: str
    username_type: Literal["mobile", "email"]


class JWTToken(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str
    username_type: Literal["mobile", "email"]
    scopes: list[str] = []


class StatusReply(BaseModel):
    status: str


class MeReplyUser(BaseModel):
    user_id: int
    name: str
    token: str


class MeReply(BaseModel):
    is_admin: bool
    users: list[MeReplyUser]
