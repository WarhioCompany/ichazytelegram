import re

from db_data import db_session
from db_data.db_session import session_scope
from db_data.models import UserWork
import os

db_session.global_init('db/database.sqlite')
with session_scope() as session:
    userworks = session.query(UserWork).all()

    for userwork in userworks:
        challenge_name = userwork.challenge.name if userwork.challenge else 'NONE'
        file_name = f'user_{userwork.user.name} challenge_{challenge_name}'
        file_name = re.sub(r'[^a-zA-Z0-9_/ а-яА-Я]', '', file_name)
        dir_path = os.path.join('data\\userworks', userwork.user.name)
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)
        if userwork.type == 'image':
            file_name += '.jpg'
        else:
            file_name += '.mp4'

        fp = os.path.join(dir_path, file_name)
        if os.path.isfile(fp):
            os.remove(fp)
        with open(fp, 'xb') as file:
            file.write(userwork.data)

