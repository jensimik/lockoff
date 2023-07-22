from pydantic import BaseModel


class RequestTOTP(BaseModel):
    mobile: str


class Login(BaseModel):
    mobile: str
    totp: str


class JWTToken(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    mobile: str | None = None
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
