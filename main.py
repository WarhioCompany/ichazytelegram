from db_data.db_session import session_scope
from db_data.models import Challenge
from os import listdir
from os.path import isfile, join

from db_data import db_session
import datetime
from db_data.models import *

db_session.global_init('db/database.sqlite')

with session_scope() as session:
    challenge = Challenge(
        image=open('data/pics/cat1.webp', 'rb').read(),
        name='тест1',
        description='Загрузи любое фото',
        price=0,
        date_to=datetime.date(2024, 8, 25),
        work_type='image',
        userwork_limit=1,
        winner_limit=100,
        coins_prize=1000,
        is_hard=False,
    )
    session.add(challenge)
    challenge = Challenge(
        video=open('data/videos/cat1.mp4', 'rb').read(),
        name='тест2',
        description='Загрузи любое видео',
        price=0,
        date_to=datetime.date(2024, 8, 25),
        work_type='video',
        userwork_limit=1,
        winner_limit=100,
        coins_prize=1000,
        is_hard=False,
    )
    session.add(challenge)
    challenge = Challenge(
        image=open('data/pics/cat2.jpg', 'rb').read(),
        name='тест3',
        description='Загрузи 3 любых фото',
        price=0,
        date_to=datetime.date(2024, 8, 25),
        work_type='image',
        userwork_limit=3,
        winner_limit=100,
        coins_prize=2000,
        is_hard=False,
    )
    session.add(challenge)
    challenge = Challenge(
        video=open('data/videos/cat2.mp4', 'rb').read(),
        name='тест4',
        description='Загрузи 3 любых видео',
        price=0,
        date_to=datetime.date(2024, 8, 25),
        work_type='video',
        userwork_limit=3,
        winner_limit=100,
        coins_prize=2000,
        is_hard=False,
    )
    session.add(challenge)
    challenge = Challenge(
        image=open('data/pics/cat3.jpg', 'rb').read(),
        name='тест5',
        description='Загрузи 4 любых фото',
        price=0,
        date_to=datetime.date(2024, 8, 25),
        work_type='image',
        userwork_limit=4,
        winner_limit=100,
        coins_prize=3000,
        is_hard=False,
    )
    session.add(challenge)
    challenge = Challenge(
        image=open('data/pics/cat4.jpg', 'rb').read(),
        name='тест6',
        description='Загрузи любое фото, затем отмени заявку и загрузи снова любое фото',
        price=0,
        date_to=datetime.date(2024, 8, 25),
        work_type='image',
        userwork_limit=1,
        winner_limit=100,
        coins_prize=3000,
        is_hard=False,
    )
    session.add(challenge)
    challenge = Challenge(
        video=open('data/videos/cat4.mp4', 'rb').read(),
        name='тест7',
        description='Загрузи любое видео, дождись отклонения работы от админа и снова загрузи любое видео',
        price=0,
        date_to=datetime.date(2024, 8, 25),
        work_type='video',
        userwork_limit=1,
        winner_limit=100,
        coins_prize=3000,
        is_hard=False,
    )
    session.add(challenge)
    prize = Prize(
        name='Аплодисменты',
        description='Аплодисменты хлоп-хлоп'
    )
    brand = Brand(
        name='brand_test'
    )
    promo1 = Promocode(
        brand=brand,
        promo='promocode1',
        telegram_contact='mikeept',
    )
    promo2 = Promocode(
        brand=brand,
        promo='promocode2',
        telegram_contact='mikeept',
    )
    challenge = Challenge(
        video=open('data/videos/cat5.mp4', 'rb').read(),
        name='тест8',
        description='Накопи монеты, примени промокодики и отправь работу',
        price=9999,
        date_to=datetime.date(2024, 8, 25),
        work_type='video',
        userwork_limit=1,
        winner_limit=10,
        is_hard=True,
        prize=prize,
        post_link='https://t.me/ichazytelegram/30',
        promocodes=[promo1, promo2]
    )
    session.add(prize)
    session.add(brand)
    session.add(promo1)
    session.add(promo2)
    session.add(challenge)

    session.commit()

exit()
with session_scope() as session:
    image = open('data/pics/сложнасложна.png', 'rb').read()
    prize = Prize(
        name='Корзинка',
        description='Корзинка для тебя'
    )
    brand = Brand(
        name='БрэндРандом'
    )
    promo1 = Promocode(
        brand=brand,
        promo='promocode1',
        telegram_contact='warhio'
    )
    promo2 = Promocode(
        brand=brand,
        promo='promocode2',
        telegram_contact='warhio'
    )
    challenge = Challenge(
        name='#сложныйчеллендж',
        description='непростой челлендж',
        image=image,
        price=100,
        date_to=datetime.date(2024, 8, 15),
        work_type='image',
        userwork_limit=1,
        winner_limit=5,
        is_hard=True,
        prize=prize,
        post_link="https://t.me/ichazytelegram/30",
        promocodes=[promo1, promo2]
    )
    session.add(prize)
    session.add(brand)
    session.add(promo1)
    session.add(promo2)
    session.add(challenge)
    session.commit()

with session_scope() as session:
    brand = Brand(
        name='ichazy'
    )
    promo = Promocode(
        promo='IchazyPromocode',
        brand=brand,
        telegram_contact='mikeept'
    )
    session.add(brand)
    session.add(promo)
    session.commit()

with session_scope() as sess:
    image = open('data/pics/пицца.jpg', 'rb').read()
    challenge = Challenge(
        name='#пиццастудента',
        description='Сделай пиццу из подручных средств!',
        image=image,
        price=0,
        date_to=datetime.date(2024, 4, 30),
        work_type='image',
        is_hard=False,
        coins_prize=80,
        userwork_limit=1,
        winner_limit=5
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
        coins_prize=25,
        userwork_limit=1,
        winner_limit=8
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
        coins_prize=95,
        userwork_limit=2,
        winner_limit=10
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
        coins_prize=95,
        userwork_limit=3,
        winner_limit=3
    )
    sess.add(challenge)
    sess.commit()