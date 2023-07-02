from aiotinydb import AIOTinyDB

from .config import settings

DB_member = AIOTinyDB(settings.db_member)
DB_dayticket = AIOTinyDB(settings.db_dayticket)
