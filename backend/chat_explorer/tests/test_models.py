import sqlalchemy as sa
from app.db import SessionLocal, models as M


def test_conversation_message_crud(db_engine):
    sess = SessionLocal()
    conv = M.Conversation(conversation_uid="conv-1")
    msg = M.Message(conversation=conv, role="user", body="Hello")
    sess.add(conv)
    sess.commit()

    rows = sess.scalars(sa.select(M.Message)).all()
    assert rows and rows[0].conversation.conversation_uid == "conv-1"