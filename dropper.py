from random import randint

from sqlalchemy.orm import scoped_session, sessionmaker

from userwrapper import User
from db_data import db_session
import sqlalchemy as sa
from db_data.models import user_userworks_likes, UserWork, user_to_promocodes, challenge_to_promocode
import os
from db_data.models import *


engine = None
def init():
    global engine
    db_file = 'db/database.sqlite'

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    print(f"Connecting to db {conn_str}")

    engine = sa.create_engine(conn_str, echo=False)
    __factory = scoped_session(sessionmaker(bind=engine))
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    Base.metadata.create_all(engine)


def soft_drop():
    init()
    UserWork.__table__.drop(engine)
    user_to_promocodes.drop(engine)
    user_userworks_likes.drop(engine)
    User.__table__.drop(engine)
    Event.__table__.drop(engine)
    PromocodeOnModeration.__table__.drop(engine)


def hard_drop():
    os.remove('db/database.sqlite')


soft_drop()