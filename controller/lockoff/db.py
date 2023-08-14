from piccolo import columns
from piccolo.engine import SQLiteEngine
from piccolo.query import Min, Max  # noqa: F401
from piccolo.query.methods.select import Count  # noqa: F401
from piccolo.query import WhereRaw  # noqa: F401
from piccolo.table import Table
from piccolo.utils.pydantic import create_pydantic_model

from .access_token import TokenType, TokenMedia
from .config import settings

DB = SQLiteEngine(path=settings.db_file)


class User(Table, tablename="users", db=DB):
    id = columns.Integer(primary_key=True)
    name = columns.Varchar(length=100)
    token_type = columns.Integer(choices=TokenType)
    mobile = columns.Varchar(length=64)
    email = columns.Varchar(length=64)
    batch_id = columns.Varchar(length=25)
    totp_secret = columns.Varchar(length=32)
    season_digital = columns.Varchar(length=4)
    season_print = columns.Varchar(length=4)
    active = columns.Boolean()


class Dayticket(Table, tablename="dayticket", db=DB):
    id = columns.Integer(primary_key=True)
    batch_id = columns.Varchar(length=25)
    expires = columns.Integer()


class AccessLog(Table, tablename="accesslog", db=DB):
    id = columns.Integer(primary_key=True)
    obj_id = columns.Integer()
    token_type = columns.Integer(choices=TokenType)
    token_media = columns.Integer(choices=TokenMedia)
    timestamp = columns.Varchar(length=25)


class APDevice(Table, tablename="ap_device", db=DB):
    id = columns.Varchar(primary_key=True)
    push_token = columns.Varchar()
    push_service_url = columns.Varchar()
    device_type = columns.Varchar()


class APPass(Table, tablename="ap_pass", db=DB):
    id = columns.Varchar(primary_key=True)
    user_id = columns.Integer()
    auth_token = columns.Varchar()
    update_tag = columns.Integer(default=0)


class APReg(Table, tablename="ap_reg", db=DB):
    device_library_identifier = columns.Varchar()
    serial_number = columns.Varchar()


class GPass(Table, tablename="g_pass", db=DB):
    id = columns.Varchar(primary_key=True)
    user_id = columns.Integer()
    totp = columns.Varchar()
    installed = columns.Boolean()


DayticketModel = create_pydantic_model(Dayticket)
UserModel = create_pydantic_model(User)
AccessLogModel = create_pydantic_model(AccessLog)
