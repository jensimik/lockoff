from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field, constr

username_type = Literal["mobile", "email"]


class AppleDeviceRegistration(BaseModel):
    pushToken: str
    pushServiceUrl: Optional[str] = ""


class AppleLog(BaseModel):
    logs: list[str] = []


class TokenCheckInput(BaseModel):
    token: str


class TokenCheck(BaseModel):
    user_id: int
    token_type: str
    name: Optional[str] = ""


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
