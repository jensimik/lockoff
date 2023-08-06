from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from pydantic import ValidationError

from . import schemas
from .config import settings
from .db import User, UserModel

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login",
    scopes={
        "basic": "basic access for normal club members",
        "admin": "admin scope to access logs, etc",
    },
)


async def get_current_users(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        sub: str = payload.get("sub")
        if sub is None:
            raise credentials_exception
        sub_type: str = payload.get("sub_type")
        token_scopes = payload.get("scopes", [])
        token_data = schemas.TokenData(
            username=sub, username_type=sub_type, scopes=token_scopes
        )
    except (JWTError, ValidationError, ValidationError, ValueError):
        raise credentials_exception
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    if token_data.username_type == "email":
        return [
            UserModel(**u)
            for u in await User.select().where(User.email == token_data.username)
        ]
    elif token_data.username_type == "mobile":
        return [
            UserModel(**u)
            for u in await User.select().where(User.mobile == token_data.username)
        ]
