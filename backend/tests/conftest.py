"""
Shared pytest fixtures for DB-related tests.
"""

import os
import pytest
import sqlalchemy as sa
from sqlalchemy.engine import Engine, create_engine


@pytest.fixture(scope="session")
def db_engine() -> Engine:
    """
    Returns a SQLAlchemy Engine connected to the DATABASE_URL
    declared for the running container.
    """
    db_url = os.getenv("DATABASE_URL") or \
        "postgresql+psycopg2://app:app@postgres:5432/app"
    engine = create_engine(db_url, future=True)
    yield engine
    engine.dispose()