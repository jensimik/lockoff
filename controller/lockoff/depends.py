from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from .config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user_ids(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_ids: list[int] = payload.get("sub")
        if user_ids is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return user_ids
