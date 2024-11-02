from contextlib import contextmanager

import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session, scoped_session, sessionmaker

__factory = None
SessionLocal = None

def global_init2(db_file):
    file = open(db_file, 'r')
    print(file.read())

def global_init(db_file):
    global __factory, SessionLocal

    if __factory:
        __factory.close()

    if not db_file.strip():
        raise Exception('No db specified')

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    print(f"Connecting to db {conn_str}")

    engine = sa.create_engine(conn_str, echo=False)
    __factory = scoped_session(orm.sessionmaker(bind=engine))
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    from .models import Base, User, Challenge, UserWork, Prize, Brand
    Base.metadata.create_all(engine)


@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
    finally:
      session.close()