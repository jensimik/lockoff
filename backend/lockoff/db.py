import databases
import sqlalchemy
from datetime import datetime
from typing import Union
from .utils import TokenEnum, Member
from .config import settings

database = databases.Database(settings.database_url)

metadata = sqlalchemy.MetaData()

tokens = sqlalchemy.Table(
    "tokens",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String),
    sqlalchemy.Column("token", sqlalchemy.String, unique=True, index=True),
    sqlalchemy.Column("token_type", sqlalchemy.Enum(TokenEnum)),
    sqlalchemy.Column("batch", sqlalchemy.DateTime),
    sqlalchemy.Column("last_access", sqlalchemy.DateTime),
)

access_log = sqlalchemy.Table(
    "access_log",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("token", sqlalchemy.Integer, index=True),
    sqlalchemy.Column("token_type", sqlalchemy.Enum(TokenEnum), index=True),
    sqlalchemy.Column("timestamp", sqlalchemy.DateTime),
)

engine = sqlalchemy.create_engine(
    settings.database_url, connect_args={"check_same_thread": False}
)
metadata.create_all(engine)

# DB functions


async def log_access(token: str, timestamp: datetime, token_type: TokenEnum):
    log_insert = access_log.insert().values(
        token=token, timestamp=timestamp, token_type=token.token_type
    )
    await database.execute(log_insert)


async def check_token(token: str, now: datetime) -> tuple[bool, Union[Member, None]]:
    query = tokens.select().where(tokens.c.token.name == token)
    # morning members allowed weekends before 12 and weekdays before 15
    if (now.weekday() in [5, 6] and now.hour < 12) or (
        now.weekday() < 5 and now.hour < 15
    ):
        query = query.where(
            tokens.c.token_type.in_(
                [TokenEnum.full, TokenEnum.morning, TokenEnum.special]
            )
        )
    # else only query full members or special barcodes
    else:
        query = query.where(
            tokens.c.token_type.in_([TokenEnum.full, TokenEnum.special])
        )

    # if token found in database then success
    token = await database.fetch_one(query)
    return (
        bool(token),
        Member(name=token.name, token_type=token.token_type, token=token.token),
    )


async def bulk_upsert_members(members: list[Member]):
    async with database.transaction():
        batch = datetime.utcnow()
        insert = tokens.insert().values(
            [
                {
                    "batch": batch,
                    "name": member.name,
                    "token": member.token,
                    "token_type": member.token_type,
                    "last_access": batch,
                }
                for member in members
            ]
        )
        upsert = insert.on_conflict_do_update(
            index_elements=[tokens.c.token.name],
            set_=dict(
                batch=batch,
                name=insert.excluded.name,
                token=insert.excluded.token,
            ),
        )
        # bulk upsert all users from klubmodul
        await database.execute(upsert)
        # remove full/morning users not in this batch
        await database.execute(
            tokens.delete().where(
                tokens.c.token_type.in_([TokenEnum.full, TokenEnum.morning]),
                tokens.c.batch.name < batch,
            )
        )
