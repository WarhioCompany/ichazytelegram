from datetime import datetime
from random import randint
import sqlalchemy
import sqlalchemy.orm as orm
from sqlalchemy.orm import scoped_session, sessionmaker, DeclarativeBase
from userwrapper import User
from db_data import db_session
import sqlalchemy as sa
#from db_data.models import user_userworks_likes, UserWork, user_to_promocodes, challenge_to_promocode
db_file = 'db/database.sqlite'
conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
print(f"Connecting to db {conn_str}")
engine = sa.create_engine(conn_str, echo=False)
__factory = scoped_session(sessionmaker(bind=engine))
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def drop_column(table_name, column_name):
    __factory.execute(sqlalchemy.text(f'ALTER TABLE {table_name} DROP COLUMN {column_name}'))
    __factory.commit()

class Base(DeclarativeBase):
    pass
class Challenge(Base):
    __tablename__ = 'challenges'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    description = sqlalchemy.Column(sqlalchemy.String)
    image = sqlalchemy.Column(sqlalchemy.BLOB, nullable=True)
    video = sqlalchemy.Column(sqlalchemy.BLOB, nullable=True)
    price = sqlalchemy.Column(sqlalchemy.Integer)
    date_to = sqlalchemy.Column(sqlalchemy.DATE)
    work_type = sqlalchemy.Column(sqlalchemy.String)
    userwork_limit = sqlalchemy.Column(sqlalchemy.Integer)
    winner_limit = sqlalchemy.Column(sqlalchemy.Integer)
    coins_prize = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    is_hard = sqlalchemy.Column(sqlalchemy.Boolean)
    prize_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    post_link = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    def __eq__(self, other):
        return self.id == other.id
class UserWork(Base):
    __tablename__ = 'userworks'
    __table_args__ = {'extend_existing': True}
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    data = sqlalchemy.Column(sqlalchemy.BLOB)
    user_id = sqlalchemy.Column(sqlalchemy.Integer)
    challenge_id = sqlalchemy.Column(sqlalchemy.Integer)
    date_uploaded = sqlalchemy.Column(sqlalchemy.Integer)
    type = sqlalchemy.Column(sqlalchemy.String)
    is_approved = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    def __eq__(self, other):
        return self.id == other.id
class Prize(Base):
    __tablename__ = 'prizes'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    description = sqlalchemy.Column(sqlalchemy.String)
class Brand(Base):
    __tablename__ = 'brands'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
class Promocode(Base):
    __tablename__ = 'promocodes'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    brand_id = sqlalchemy.Column(sqlalchemy.Integer)
    promo = sqlalchemy.Column(sqlalchemy.String)
    telegram_contact = sqlalchemy.Column(sqlalchemy.String)
    is_expired = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
class UnauthorizedPromocode(Base):
    __tablename__ = 'unauthorized_promocode'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    promocode_id = sqlalchemy.Column(sqlalchemy.Integer)
    user_id = sqlalchemy.Column(sqlalchemy.Integer)
    username = sqlalchemy.Column(sqlalchemy.String)
    def __eq__(self, other):
        return self.promocode_id == other.promocode_id
class User(Base):
    __tablename__ = 'users'
    telegram_id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    telegram_username = sqlalchemy.Column(sqlalchemy.String, default='')
    telegram_name = sqlalchemy.Column(sqlalchemy.String)
    invited_by = sqlalchemy.Column(sqlalchemy.String)
    name = sqlalchemy.Column(sqlalchemy.String)
    coins = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    def __eq__(self, other):
        return self.telegram_id == other.telegram_id
Base.metadata.create_all(engine)

userworks = __factory.query(UserWork).all()

print(len(userworks))

UserWork.__table__.drop(engine)
print(len(userworks))

class UserworkNew(Base):
    __tablename__ = 'userworks'
    __table_args__ = {'extend_existing': True}
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    data = sqlalchemy.Column(sqlalchemy.BLOB)
    user_id = sqlalchemy.Column(sqlalchemy.Integer)
    challenge_id = sqlalchemy.Column(sqlalchemy.Integer)
    date_uploaded = sqlalchemy.Column(sqlalchemy.Integer)
    type = sqlalchemy.Column(sqlalchemy.String)
    status = sqlalchemy.Column(sqlalchemy.String)

    def __eq__(self, other):
        return self.id == other.id

Base.metadata.create_all(engine)

for userwork in userworks:
    u = UserworkNew(
        id=userwork.id,
        data=userwork.data,
        user_id=userwork.user_id,
        challenge_id=userwork.challenge_id,
        date_uploaded=userwork.date_uploaded,
        type=userwork.type,
        status='approved' if userwork.is_approved else 'on_moderation'
    )
    __factory.add(u)

__factory.commit()

drop_column('userworks', 'is_approved')