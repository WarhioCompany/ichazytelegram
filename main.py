from db_data.db_session import session_scope
from db_data.models import Challenge
from os import listdir
from os.path import isfile, join

from db_data import db_session
import datetime


# def temp(name):
#     with open(name, 'rb') as file:
#         array = file.read()
#     add_challenge(name, 'описание ' + name, 0, '20/02/2024', array, False, 'image', coins_prize=10)
#
#
# onlyfiles = [f for f in listdir('.') if isfile(join('.', f)) and (f.endswith('png') or f.endswith('jpg'))]
# for file in onlyfiles:
#     temp(file)

db_session.global_init('db/database.sqlite')
with session_scope() as sess:
# onlyfiles = [f for f in listdir('.') if isfile(join('.', f)) and (f.endswith('png') or f.endswith('jpg'))]
# for file in onlyfiles:
#     image = open(file, 'rb').read()
#     challenge = Challenge(
#         name=file,
#         description='описание',
#         image=image,
#         price=0,
#         date_to=datetime.date(2024, 4, 30),
#         work_type='image',
#         is_hard=False,
#         coins_prize=100
#     )
#     sess.add(challenge)
# sess.commit()

    image = open('data/pics/пицца.jpg', 'rb').read()
    challenge = Challenge(
        name='#пиццастудента',
        description='Сделай пиццу из подручных средств!',
        image=image,
        price=0,
        date_to=datetime.date(2024, 4, 30),
        work_type='image',
        is_hard=False,
        coins_prize=80
    )
    sess.add(challenge)
    image = open('data/pics/улыбака.jpg', 'rb').read()
    challenge = Challenge(
        name='#голливудскаяулыбка',
        description='Улыбнись и запечатли это на камеру',
        image=image,
        price=0,
        date_to=datetime.date(2024, 4, 30),
        work_type='image',
        is_hard=False,
        coins_prize=25
    )
    sess.add(challenge)
    image = open('data/pics/шаурмяу.jpg', 'rb').read()
    challenge = Challenge(
        name='#шаурмяу',
        description='Заверни кота в плед, словно в шаурму',
        image=image,
        price=0,
        date_to=datetime.date(2024, 4, 30),
        work_type='image',
        is_hard=False,
        coins_prize=95
    )
    sess.add(challenge)
    image = open('data/pics/пародия.jpg', 'rb').read()
    challenge = Challenge(
        name='#неповторимыйоригинал',
        description='Сделай фотку в стиле своего любимого мема! Покажи, где здесь жалкая пародия, а что неповторимый оригинал',
        image=image,
        price=0,
        date_to=datetime.date(2024, 4, 30),
        work_type='image',
        is_hard=False,
        coins_prize=95
    )
    sess.add(challenge)
    sess.commit()