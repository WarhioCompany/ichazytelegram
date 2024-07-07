from random import randint

from sqlalchemy.orm import scoped_session, sessionmaker

from userwrapper import User
from db_data import db_session
import sqlalchemy as sa
from db_data.models import user_userworks_likes, UserWork

db_file = 'db/database.sqlite'

conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
print(f"Connecting to db {conn_str}")

engine = sa.create_engine(conn_str, echo=False)
__factory = scoped_session(sessionmaker(bind=engine))
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

from db_data.models import Base, User, Challenge, UserWork, Prize, Brand
Base.metadata.create_all(engine)