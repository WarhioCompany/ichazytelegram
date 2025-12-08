from sqlalchemy.orm import DeclarativeBase
import sqlalchemy.orm as orm
import sqlalchemy

from datetime import datetime

from db_data.db_session import session_scope


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

# completion of sub challenges is required to access a main challenge
challenge_relationships = sqlalchemy.Table(
    'challenge_relationships', Base.metadata,
    sqlalchemy.Column('main_challenge_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('challenges.id'), primary_key=True),
    sqlalchemy.Column('sub_challenge_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('challenges.id'), primary_key=True)
)


challenge_to_prize = sqlalchemy.Table(
    "challenge_to_prize",
    Base.metadata,
    sqlalchemy.Column("challenge_id", sqlalchemy.ForeignKey('challenges.id')),
    sqlalchemy.Column("prize_id", sqlalchemy.ForeignKey('prizes.id'))
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
    used_boost_promocodes = orm.relationship('UserBoostPromocode', back_populates='user')

    def __eq__(self, other):
        return self.telegram_id == other.telegram_id


class Challenge(Base):
    __tablename__ = 'challenges'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    description = sqlalchemy.Column(sqlalchemy.String)
    is_hidden = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    preview = sqlalchemy.Column(sqlalchemy.BLOB)
    preview_type = sqlalchemy.Column(sqlalchemy.String) #image, video

    price = sqlalchemy.Column(sqlalchemy.Integer)
    date_to = sqlalchemy.Column(sqlalchemy.DATE)
    work_type = sqlalchemy.Column(sqlalchemy.String)
    userwork_limit = sqlalchemy.Column(sqlalchemy.Integer)
    winner_limit = sqlalchemy.Column(sqlalchemy.Integer)

    coins_prize = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)

    is_hard = sqlalchemy.Column(sqlalchemy.Boolean)
    promocodes = orm.relationship('Promocode', secondary=challenge_to_promocode, back_populates='challenges')

    prizes = orm.relationship('Prize', secondary=challenge_to_prize, back_populates='challenges')

    post_link = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    userworks = orm.relationship('UserWork', back_populates='challenge')

    challenges_required_to_complete = orm.relationship(
        'Challenge',
        secondary=challenge_relationships,
        primaryjoin="challenges.c.id == challenge_relationships.c.main_challenge_id",
        secondaryjoin="challenges.c.id == challenge_relationships.c.sub_challenge_id",
        back_populates='required_by_challenges',
        foreign_keys=[challenge_relationships.c.main_challenge_id, challenge_relationships.c.sub_challenge_id]
    )
    required_by_challenges = orm.relationship(
        'Challenge',
        secondary=challenge_relationships,
        primaryjoin="challenges.c.id == challenge_relationships.c.sub_challenge_id",
        secondaryjoin="challenges.c.id == challenge_relationships.c.main_challenge_id",
        back_populates='challenges_required_to_complete',
        foreign_keys=[challenge_relationships.c.sub_challenge_id, challenge_relationships.c.main_challenge_id]
    )
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

    preview = sqlalchemy.Column(sqlalchemy.BLOB)

    barrier_type = sqlalchemy.Column(sqlalchemy.String, default=None) # referrals, subscribers, promocodes - https://t.me/c/1892561917/6758
    barrier_value = sqlalchemy.Column(sqlalchemy.Integer, default=0)

    challenges = orm.relationship('Challenge', secondary=challenge_to_prize, back_populates='prizes')



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
    coins = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    need_confirmation = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    is_image_proof_required = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    is_subscription_required = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    required_channel_id = sqlalchemy.Column(sqlalchemy.String)

    # telegram_contact = sqlalchemy.Column(sqlalchemy.String)

    users_used = orm.relationship('User', secondary=user_to_promocodes, back_populates='used_promocodes')
    challenges = orm.relationship('Challenge', secondary=challenge_to_promocode, back_populates='promocodes')

    is_expired = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    profit = sqlalchemy.Column(sqlalchemy.Float, default=0)

    def __eq__(self, other):
        return self.id == other.id


# Temporary object for promocodes that need confirmation on moder's approval queue.
# After promocode has been approved/declined it is deleted
class PromocodeOnModeration(Base):
    __tablename__ = 'promocodes_on_moderation'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)

    promocode_id = sqlalchemy.Column(sqlalchemy.Integer)

    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.telegram_id'))
    user = orm.relationship('User')

    image_proof = sqlalchemy.Column(sqlalchemy.BLOB, nullable=True)

    promocode_type = sqlalchemy.Column(sqlalchemy.String) # coins, boost


    def get_promocode(self):
        with session_scope() as session:
            if self.promocode_type == 'coins':
                return session.query(Promocode).filter(Promocode.id == self.promocode_id).one()
            elif self.promocode_type == 'boost':
                return session.query(BoostPromocode).filter(BoostPromocode.id == self.promocode_id).one()

# Boost promocode multiplies user's income by some coefficient
# It can last either some number of challenges (count-type) or to some point in the future (date-type)
class BoostPromocode(Base):
    __tablename__ = 'boost_promocode'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)

    promo = sqlalchemy.Column(sqlalchemy.String)

    promocode_type = sqlalchemy.Column(sqlalchemy.String, default='count') # date/count
    coefficient = sqlalchemy.Column(sqlalchemy.Float, default=1)

    absolute_value = sqlalchemy.Column(sqlalchemy.Integer, default=5) # either date when the promo will expire in seconds or remaining challenges

    need_confirmation = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    is_expired = sqlalchemy.Column(sqlalchemy.Boolean, default=True)

    # users_used_count = sqlalchemy.Column(sqlalchemy.Integer)


# Boost promocode that is bound to user
class UserBoostPromocode(Base):
    __tablename__ = 'user_boost_promocode'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)

    boost_promocode_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('boost_promocode.id'))
    boost_promocode = orm.relationship('BoostPromocode')

    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.telegram_id'))
    user = orm.relationship('User')

    value = sqlalchemy.Column(sqlalchemy.Integer) # either date when the promo will expire in seconds or remaining challenges

    confirmed = sqlalchemy.Column(sqlalchemy.Boolean)

    def __init__(self, boost_promocode: BoostPromocode, user: User):
        super().__init__()
        self.boost_promocode = boost_promocode
        self.user = user

        if boost_promocode.promocode_type == 'count': # bound to number of challenges
            self.value = self.boost_promocode.absolute_value
        else: # (date) || bound to point in the future
            self.value = datetime.now().timestamp() + self.boost_promocode.absolute_value

        if not boost_promocode.need_confirmation:
            self.confirmed = True # set as confirmed the promo doesn't need approval
        else:
            self.confirmed = False

    def __eq__(self, other):
        return self.id == other.id


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
