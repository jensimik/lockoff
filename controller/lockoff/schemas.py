from pydantic import BaseModel


class RequestTOTP(BaseModel):
    mobile: str


class Login(BaseModel):
    mobile: str
    totp: str


class JWTToken(BaseModel):
    access_token: str
    token_type: str


class StatusReply(BaseModel):
    status: str
