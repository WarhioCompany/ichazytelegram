from db_data.db_session import session_scope
from db_data.models import Challenge
from os import listdir
from os.path import isfile, join

from db_data import db_session
import datetime
from db_data.models import *

db_session.global_init('../db/database.sqlite')

with session_scope() as session:
    try:
        username = input("Username: ")
        user = session.query(User).filter(User.name == username).one()
        print(f'Current balance: {user.coins}')
        new_balance = int(input("New balance: "))
        user.coins = new_balance
        session.commit()
    except Exception as e:
        print(e)