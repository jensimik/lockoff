import aiosql
import pathlib
from aiotinydb import AIOTinyDB

from .config import settings

module_directory = pathlib.Path(__file__).resolve().parent

queries = aiosql.from_path(module_directory / "queries.sql", "aiosqlite")

DB_member = AIOTinyDB(settings.db_member)
DB_dayticket = AIOTinyDB(settings.db_dayticket)
