import sqlite3
from contextlib import asynccontextmanager

import pytest
from lockoff.depends import get_db


@pytest.mark.asyncio
async def test_get_db(mocker):
    mocker.patch("lockoff.config.settings.db_file", ":memory:")

    async with get_db() as db:
        assert isinstance(db._conn, sqlite3.Connection)
        assert db._running
