from db_data import db_session
from db_data.models import Challenge, Prize
from db_data.db_session import session_scope
import datetime

db_session.global_init('database/database.sqlite')
with session_scope() as session:
    c = session.query(Challenge).filter(Challenge.id == 6).one()
    c.name = "#ктоя OZON"

    session.commit()

    c = session.query(Challenge).filter(Challenge.id == 7).one()
    c.name = "#ктоя Wildberries"
    c.image = open('data/pics/ктоя.jpg', 'rb').read()
    session.commit()