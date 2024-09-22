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
        image=open('data/pics/Лицомклицу.jpg', 'rb').read(),
        name='#лицомклицу',
        description='Жарю яичницу. Смотрю, а она мне улыбается. То ли шучу смешно, то ли готовлю хорошо, так сразу и не поймешь.\nНаверняка ведь и ты замечал нерукотворные лица, которые глядели тебе в душу. \n\nНе упускай момент запечатлеть их и показать нам',
        price=0,
        date_to=datetime.date(2024, 12, 22),
        work_type='image',
        userwork_limit=1,
        winner_limit=1000,
        coins_prize=1000,
        is_hard=False,
    )
    session.add(challenge)
    challenge = Challenge(
        image=open('data/pics/Кактебетакоегравитация.jpg', 'rb').read(),
        name='#кактебетакоегравитация',
        description='Вам не надоело передвигаться по земле? Кто вообще сказал, что мы должны ходить? Мы никому ничего не должны! Предлагаю всем срочно начать жить над землей. Мы выше этого! Пора передвигаться по воздуху!\n\nА, да, сфоткать не забудь, как проходить жизнь без гравитации. ',
        price=0,
        date_to=datetime.date(2024, 12, 22),
        work_type='image',
        userwork_limit=1,
        winner_limit=1000,
        coins_prize=4000,
        is_hard=False,
    )
    session.add(challenge)
    prize = Prize(
        name='Стикерпак',
        description='Стикерпак\nОбклей все ленью! Покажи свою истинную натуру'
    )
    challenge = Challenge(
        image=open('data/pics/Леньнедвигательпрогресса.jpg', 'rb').read(),
        name='#леньнедвигательпрогресса',
        description="Кто мы?\n-Люди!\n-Что мы любим больше всего?\n-Лень!\n\nЗамути коллаж своих самых ярких лентяйских моментов. Не больше 4 фото в коллаж! Рассматривать больше, боюсь, будет лень…😵‍💫",
        price=5000,
        date_to=datetime.date(2024, 12, 22),
        work_type='image',
        userwork_limit=1,
        winner_limit=15,
        is_hard=True,
        prize=prize,
        post_link='https://t.me/ichazytelegram/',
        promocodes=[]
    )
    session.add(prize)
    session.add(challenge)
    session.commit()