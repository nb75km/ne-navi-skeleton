import pytest
import sqlalchemy as sa
from sqlalchemy.engine import Engine

@pytest.mark.db_check
def test_pgvector_available(db_engine: Engine):
    with db_engine.connect() as conn:
        (ext,) = conn.execute(sa.text(
            "SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector'"
        )).one()
        assert ext == 1

@pytest.mark.db_check
def test_tables_exist(db_engine: Engine):
    insp = sa.inspect(db_engine)
    assert insp.has_table("messages", schema="chat")
    assert insp.has_table("transcripts", schema="minutes")