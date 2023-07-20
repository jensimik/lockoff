import aiosqlite
from fastapi import HTTPException, status
from fastapi.security import APIKeyQuery, OAuth2PasswordBearer
from jose import JWTError, jwt

from .config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

query_token = APIKeyQuery(name="token")


async def get_current_mobile(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        mobile: str = payload.get("sub")
        if mobile is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return mobile


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


# async def get_current_mobile(token: Annotated[str, Depends(oauth2_scheme)]):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
#         mobile: str = payload.get("sub")
#         if mobile is None:
#             raise credentials_exception
#     except JWTError:
#         raise credentials_exception
#     return mobile
