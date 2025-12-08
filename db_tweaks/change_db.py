from sqlalchemy.orm import scoped_session, sessionmaker, DeclarativeBase
import sqlalchemy
db_file = 'db/database.sqlite'
conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
print(f"Connecting to db {conn_str}")
engine = sqlalchemy.create_engine(conn_str, echo=False)
__factory = scoped_session(sessionmaker(bind=engine))
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def drop_column(table_name, column_name):
    __factory.execute(sqlalchemy.text(f"ALTER TABLE {table_name} DROP COLUMN '{column_name}'"))
    __factory.commit()


def add_column(table_name, column_name, column_type, default_value=None):
    if default_value is None:
        default_value = 'NULL'
    __factory.execute(sqlalchemy.text(f"ALTER TABLE {table_name} ADD '{column_name}' {column_type} DEFAULT {default_value}"))
    __factory.commit()


def drop_table(table_name):
    __factory.execute(sqlalchemy.text(f"DROP TABLE {table_name}"))



add_column('promocodes', 'profit', 'FLOAT', 0)
add_column('promocodes', 'is_image_proof_required', 'BOOLEAN', 'FALSE')
add_column('promocodes', 'is_subscription_required', 'BOOLEAN', 'FALSE')
add_column('promocodes', 'required_channel_id', 'VARCHAR')

add_column('challenges', 'is_hidden', 'BOOLEAN', 'FALSE')
add_column('challenges', 'preview_type', 'VARCHAR')
add_column('challenges', 'preview', 'BLOB')

add_column('prizes', 'barrier_type', 'VARCHAR')
add_column('prizes', 'barrier_value', 'INTEGER')
add_column('prizes', 'preview', 'BLOB')


drop_column('promocodes', 'telegram_contact')



class Base(DeclarativeBase):
    pass

class Challenge(Base):
    __tablename__ = 'challenges'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    description = sqlalchemy.Column(sqlalchemy.String)
    is_hidden = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    image = sqlalchemy.Column(sqlalchemy.BLOB, nullable=True)
    video = sqlalchemy.Column(sqlalchemy.BLOB, nullable=True)
    preview = sqlalchemy.Column(sqlalchemy.BLOB)
    preview_type = sqlalchemy.Column(sqlalchemy.String)

    price = sqlalchemy.Column(sqlalchemy.Integer)
    date_to = sqlalchemy.Column(sqlalchemy.DATE)
    work_type = sqlalchemy.Column(sqlalchemy.String)
    userwork_limit = sqlalchemy.Column(sqlalchemy.Integer)
    winner_limit = sqlalchemy.Column(sqlalchemy.Integer)

    coins_prize = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)

    is_hard = sqlalchemy.Column(sqlalchemy.Boolean)
    #promocodes = orm.relationship('Promocode', secondary=challenge_to_promocode, back_populates='challenges')

    prize_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    #prize = orm.relationship('Prize')

    post_link = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    #userworks = orm.relationship('UserWork', back_populates='challenge')

    def __eq__(self, other):
        return self.id == other.id


class PromocodeOnModeration(Base):
    __tablename__ = 'promocode_status'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)

    promocode_id = sqlalchemy.Column(sqlalchemy.Integer)

    user_id = sqlalchemy.Column(sqlalchemy.Integer)

    promocode_type = sqlalchemy.Column(sqlalchemy.String) # coins, boost


Base.metadata.create_all(engine)

PromocodeOnModeration.__table__.drop(engine)

challenges = __factory.query(Challenge).all()
for challenge in challenges:
    if challenge.video:
        challenges.preview = challenge.video
        challenge.preview_type = 'video'
    else:
        challenge.preview = challenge.image
        challenge.preview_type = 'image'


__factory.commit()

drop_column('challenges', 'video')
drop_column('challenges', 'image')

drop_table('challenges')
drop_table('userworks')