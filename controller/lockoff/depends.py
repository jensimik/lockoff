from typing import Annotated, Dict, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from fastapi.security.base import SecurityBase
from fastapi.security.utils import get_authorization_scheme_param
from jose import JWTError, jwt
from pydantic import ValidationError

from . import schemas
from .config import settings
from .db import DB, APPass, User, UserModel

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login",
    scopes={
        "basic": "basic access for normal club members",
        "admin": "admin scope to access logs, etc",
    },
)


async def apple_auth_pass(
    request: Request,
) -> (str, dict):
    authorization = request.headers.get("Authorization")
    scheme, auth_token = get_authorization_scheme_param(authorization)
    scheme = scheme.lower()
    if not authorization or scheme in [
        "applepass",
        "attidopass",
        "androidpass",
    ]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "ApplePass"},
        )
    pass_id = request.path_params["serial_number"]
    if (
        appass := await APPass.select()
        .where(
            APPass.id == pass_id,
            APPass.auth_token == auth_token,
        )
        .first()
    ):
        # hack - set scheme in the dict to pass to register function
        appass["scheme"] = scheme
        return appass

    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
