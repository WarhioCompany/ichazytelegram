from sqlalchemy.orm import DeclarativeBase
import sqlalchemy.orm as orm
import sqlalchemy

from datetime import datetime


class Base(DeclarativeBase):
    pass


user_userworks_likes = sqlalchemy.Table(
    "user_userworks_likes",
    Base.metadata,
    sqlalchemy.Column("user_id", sqlalchemy.ForeignKey('users.telegram_id')),
    sqlalchemy.Column("userwork_id", sqlalchemy.ForeignKey('userworks.id'))
)

user_to_promocodes = sqlalchemy.Table(
    "user_to_promocodes",
    Base.metadata,
    sqlalchemy.Column("user_id", sqlalchemy.ForeignKey('users.telegram_id')),
    sqlalchemy.Column("promocode_id", sqlalchemy.ForeignKey('promocodes.id')),
)

challenge_to_promocode = sqlalchemy.Table(
    "challenge_to_promocode",
    Base.metadata,
    sqlalchemy.Column("challenge_id", sqlalchemy.ForeignKey('challenges.id')),
    sqlalchemy.Column("promocode_id", sqlalchemy.ForeignKey('promocodes.id'))
)


class User(Base):
    __tablename__ = 'users'
    telegram_id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    telegram_username = sqlalchemy.Column(sqlalchemy.String, default='')
    telegram_name = sqlalchemy.Column(sqlalchemy.String, default='')

    invited_by = sqlalchemy.Column(sqlalchemy.String)

    name = sqlalchemy.Column(sqlalchemy.String)
    coins = sqlalchemy.Column(sqlalchemy.Integer, default=0)

    userworks = orm.relationship('UserWork', back_populates='user')
    liked_userworks = orm.relationship('UserWork', secondary=user_userworks_likes, back_populates='users_liked')

    used_promocodes = orm.relationship('Promocode', secondary=user_to_promocodes, back_populates='users_used')

    def __eq__(self, other):
        return self.telegram_id == other.telegram_id


class Challenge(Base):
    __tablename__ = 'challenges'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    description = sqlalchemy.Column(sqlalchemy.String)
#    is_hidden = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    image = sqlalchemy.Column(sqlalchemy.BLOB, nullable=True)
    video = sqlalchemy.Column(sqlalchemy.BLOB, nullable=True)

    price = sqlalchemy.Column(sqlalchemy.Integer)
    date_to = sqlalchemy.Column(sqlalchemy.DATE)
    work_type = sqlalchemy.Column(sqlalchemy.String)
    userwork_limit = sqlalchemy.Column(sqlalchemy.Integer)
    winner_limit = sqlalchemy.Column(sqlalchemy.Integer)

    coins_prize = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)

    is_hard = sqlalchemy.Column(sqlalchemy.Boolean)
    promocodes = orm.relationship('Promocode', secondary=challenge_to_promocode, back_populates='challenges')

    prize_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('prizes.id'), nullable=True)
    prize = orm.relationship('Prize')

    post_link = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    userworks = orm.relationship('UserWork', back_populates='challenge')

    def __eq__(self, other):
        return self.id == other.id


class UserWork(Base):
    __tablename__ = 'userworks'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    data = sqlalchemy.Column(sqlalchemy.BLOB)

    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.telegram_id'))
    user = orm.relationship('User')
    challenge_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('challenges.id'))
    challenge = orm.relationship('Challenge')

    date_uploaded = sqlalchemy.Column(sqlalchemy.Integer)
    type = sqlalchemy.Column(sqlalchemy.String)  # image / video
    #is_approved = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    # approved, disapproved, on_moderation
    status = sqlalchemy.Column(sqlalchemy.String, default='on_moderation')

    users_liked = orm.relationship('User', secondary=user_userworks_likes, back_populates='liked_userworks')

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

    brand_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('brands.id'))
    brand = orm.relationship('Brand')

    promo = sqlalchemy.Column(sqlalchemy.String)

    telegram_contact = sqlalchemy.Column(sqlalchemy.String)

    users_used = orm.relationship('User', secondary=user_to_promocodes, back_populates='used_promocodes')
    challenges = orm.relationship('Challenge', secondary=challenge_to_promocode, back_populates='promocodes')

    is_expired = sqlalchemy.Column(sqlalchemy.Boolean, default=False)


class UnauthorizedPromocode(Base):
    __tablename__ = 'unauthorized_promocode'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)

    promocode_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('promocodes.id'))
    promocode = orm.relationship('Promocode')

    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.telegram_id'))
    user = orm.relationship('User')
    username = sqlalchemy.Column(sqlalchemy.String)

    def __eq__(self, other):
        return self.promocode_id == other.promocode_id


class Event(Base):
    __tablename__ = 'events'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)

    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.telegram_id'))
    user = orm.relationship('User')

    event_type = sqlalchemy.Column(sqlalchemy.String)
    date = sqlalchemy.Column(sqlalchemy.Integer)

    active = sqlalchemy.Column(sqlalchemy.BOOLEAN)

    def time_elapsed(self):
        return (datetime.now() - datetime.fromtimestamp(self.date)).total_seconds()
