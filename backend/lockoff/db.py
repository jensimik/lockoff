import databases
import sqlalchemy
from .utils import TokenEnum
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
