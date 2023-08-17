from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@asynccontextmanager
async def testing_lifespan(app: FastAPI):
    yield


@pytest.fixture
def client(mocker) -> TestClient:
    """unauthenticated client"""
    mocker.patch("lockoff.lifespan.lifespan", testing_lifespan)
    from lockoff.main import app

    with TestClient(
        app=app,
        base_url="http://test",
    ) as client:
        yield client
