from pydantic import BaseModel, model_validator


class RequestMobileTOTP(BaseModel):
    mobile: str | None = None


class RequestEmailTOTP(BaseModel):
    email: str | None = None


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
