from sqlalchemy.orm import DeclarativeBase
import sqlalchemy.orm as orm
import sqlalchemy


class Base(DeclarativeBase):
    pass


user_userworks_likes = sqlalchemy.Table(
    "user_userworks_likes",
    Base.metadata,
    sqlalchemy.Column("user_id", sqlalchemy.ForeignKey('users.telegram_id'), primary_key=True),
    sqlalchemy.Column("userwork_id", sqlalchemy.ForeignKey('userworks.id'), primary_key=True)
)


class User(Base):
    __tablename__ = 'users'
    telegram_id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)

    name = sqlalchemy.Column(sqlalchemy.String)
    coins = sqlalchemy.Column(sqlalchemy.Integer, default=0)

    userworks = orm.relationship('UserWork', back_populates='user')
    liked_userworks = orm.relationship('UserWork', secondary=user_userworks_likes, back_populates='users_liked')

    def __eq__(self, other):
        return self.telegram_id == other.telegram_id


class Challenge(Base):
    __tablename__ = 'challenges'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    description = sqlalchemy.Column(sqlalchemy.String)

    image = sqlalchemy.Column(sqlalchemy.BLOB)

    price = sqlalchemy.Column(sqlalchemy.Integer)
    date_to = sqlalchemy.Column(sqlalchemy.DATE)
    work_type = sqlalchemy.Column(sqlalchemy.String)
    userwork_limit = sqlalchemy.Column(sqlalchemy.Integer)

    is_hard = sqlalchemy.Column(sqlalchemy.Boolean)
    coins_prize = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    prize_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)

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

    date_uploaded = sqlalchemy.Column(sqlalchemy.Date)
    type = sqlalchemy.Column(sqlalchemy.String)
    is_approved = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    users_liked = orm.relationship('User', secondary=user_userworks_likes, back_populates='liked_userworks')

    def __eq__(self, other):
        return self.id == other.id


class Prize(Base):
    __tablename__ = 'prizes'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)


class Brand(Base):
    __tablename__ = 'brands'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)