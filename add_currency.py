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
        print('Telegram username / Bot username')
        is_telegram = input("Is this username telegram's (y/n): ").lower().strip() == 'y'
        if is_telegram:
            telegram_username = input("Telegram username: ")
            user = session.query(User).filter(User.telegram_username == telegram_username).one()
        else:
            bot_username = input("Bot username: ")
            user = session.query(User).filter(User.name == bot_username).one()
        print(f'Username: {user.name}\nTelegram: {user.telegram_username}\nCurrent balance: {user.coins}')
        new_balance = int(input("New balance: "))
        user.coins = new_balance
        session.commit()
    except Exception as e:
        print(e)