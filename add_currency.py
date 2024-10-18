from db_data.db_session import session_scope
from db_data.models import Challenge
from os import listdir
from os.path import isfile, join

from db_data import db_session
import datetime
from db_data.models import *
from db_data import db_session

db_session.global_init('db/database.sqlite')


with session_scope() as session:
    try:
        telegram_username = input("Username: ")
        user = session.query(User).filter(User.telegram_username == telegram_username).one()
        print(f'Username: {user.name}\nCurrent balance: {user.coins}')
        new_balance = int(input("New balance: "))
        user.coins = new_balance
        session.commit()
    except Exception as e:
        print(e)