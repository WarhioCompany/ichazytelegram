from random import randint

from sqlalchemy.orm import scoped_session, sessionmaker

from userwrapper import User
from db_data import db_session
import sqlalchemy as sa
from db_data.models import user_userworks_likes, UserWork, user_to_promocodes, challenge_to_promocode

db_file = 'db/database.sqlite'

conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
print(f"Connecting to db {conn_str}")

engine = sa.create_engine(conn_str, echo=False)
__factory = scoped_session(sessionmaker(bind=engine))
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

from db_data.models import Base, User, Challenge, UserWork, Prize, Brand, Promocode, user_to_promocodes, UnauthorizedPromocode
Base.metadata.create_all(engine)

UserWork.__table__.drop(engine)
user_to_promocodes.drop(engine)
user_userworks_likes.drop(engine)
UnauthorizedPromocode.__table__.drop(engine)
User.__table__.drop(engine)

exit()
Challenge.__table__.drop(engine)
Promocode.__table__.drop(engine)
Prize.__table__.drop(engine)
Brand.__table__.drop(engine)
challenge_to_promocode.drop(engine)

exit()
User.__table__.drop(engine)
UserWork.__table__.drop(engine)
Challenge.__table__.drop(engine)