from piccolo.engine.sqlite import SQLiteEngine
from piccolo.table import Table
from piccolo import columns

from .config import settings
from .access_token import TokenType

DB = SQLiteEngine(path=settings.db_file)


class Users(Table, db=DB):
    user_id = columns.Integer(primary_key=True)
    name = columns.Varchar(length=100)
    member_type = columns.Integer(choices=TokenType)
    mobile = columns.Varchar(length=8)
    email = columns.Varchar(length=80)
    batch_id = columns.Varchar(length=25)
    totp_secret = columns.Varchar(length=32)
    active = columns.Boolean()


class Dayticket(Table, db=DB):
    ticket_id = columns.Integer(primary_key=True)
    batch_id = columns.Varchar(length=25)
    expires = columns.Integer()


class AccessLog(Table, db=DB):
    log_id = columns.Integer(primary_key=True)
    obj_id = columns.Integer()
    token_type = columns.Integer(choices=TokenType)
