from piccolo import columns
from piccolo.engine import SQLiteEngine
from piccolo.query import Min, Max  # noqa: F401
from piccolo.query.methods.select import Count  # noqa: F401
from piccolo.table import Table
from piccolo.utils.pydantic import create_pydantic_model

from .access_token import TokenType
from .config import settings

DB = SQLiteEngine(path=settings.db_file)


class User(Table, tablename="users", db=DB):
    user_id = columns.Integer(primary_key=True)
    name = columns.Varchar(length=100)
    token_type = columns.Integer(choices=TokenType)
    mobile = columns.Varchar(length=64)
    email = columns.Varchar(length=64)
    batch_id = columns.Varchar(length=25)
    totp_secret = columns.Varchar(length=32)
    active = columns.Boolean()


class Dayticket(Table, tablename="dayticket", db=DB):
    id = columns.Integer(primary_key=True)
    batch_id = columns.Varchar(length=25)
    expires = columns.Integer()


class AccessLog(Table, tablename="accesslog", db=DB):
    id = columns.Integer(primary_key=True)
    obj_id = columns.Integer()
    token_type = columns.Integer(choices=TokenType)
    timestamp = columns.Varchar(length=25)


DayticketModel = create_pydantic_model(Dayticket)
UserModel = create_pydantic_model(User)
AccessLogModel = create_pydantic_model(AccessLog)
