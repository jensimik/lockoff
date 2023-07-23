from typing import Annotated

import aiosqlite
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from pydantic import ValidationError

from . import schemas
from .config import settings

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login",
    scopes={
        "basic": "basic access for normal club members",
        "admin": "admin scope to access logs, etc",
    },
)


async def get_current_user_id(
    security_scopes: SecurityScopes, token: Annotated[str, Depends(oauth2_scheme)]
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
        user_id_raw: str = payload.get("sub")
        if user_id_raw is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = schemas.TokenData(user_id=user_id_raw, scopes=token_scopes)
    except (JWTError, ValidationError, ValidationError, ValueError):
        raise credentials_exception
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return token_data.user_id


async def get_db():
    """Return a database connection for use as a dependency.
    This connection has the Row row factory automatically attached."""

    db = await aiosqlite.connect(settings.db_file)
    # Provide a smarter version of the results. This keeps from having to unpack
    # tuples manually.
    db.row_factory = aiosqlite.Row

    try:
        yield db
    finally:
        await db.close()


DBcon = Annotated[aiosqlite.Connection, Depends(get_db)]
