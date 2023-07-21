import pathlib

import aiosql

module_directory = pathlib.Path(__file__).resolve().parent

queries = aiosql.from_path(module_directory / "queries.sql", "aiosqlite")
