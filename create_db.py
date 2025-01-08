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
        description='Этот задорный взгляд, бездонные глаза, сногсшибательная улыбка, слюнки текут…стоп. Это же яичница! \nНаверняка ведь и ты замечал нерукотворные лица, которые глядели тебе в душу. \n\nНе упускай момент запечатлеть их и показать нам!',
        price=0,
        date_to=datetime.date(2024, 12, 22),
        work_type='image',
        userwork_limit=10,
        winner_limit=1000,
        coins_prize=200,
        is_hard=False,
    )
    session.add(challenge)
    challenge = Challenge(
        image=open('data/pics/Кактебетакоегравитация.jpg', 'rb').read(),
        name='#кактебетакоегравитация',
        description='Вам не надоело передвигаться по земле? Кто вообще сказал, что мы должны ходить? Мы никому ничего не должны! Предлагаю всем срочно начать жить над землей. Мы выше этого! Порхай, как бабочка, жаль, что g = 9,8…\n\nА, да, сфоткать не забудь, как проходит жизнь без гравитации.',
        price=0,
        date_to=datetime.date(2024, 12, 22),
        work_type='image',
        userwork_limit=2,
        winner_limit=1000,
        coins_prize=2000,
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
        description="- Кто мы?\n- Люди!\n- Что мы любим больше всего? \n- Лень!\n\nЗамути коллаж своих самых лентяйских моментов. Не больше 4 фото в коллаж! Рассматривать больше, боюсь, будет лень…😵‍💫",
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

    prize = Prize(
        name='СЕРТИФИКАТ М ВИДЕО',
        description='За успешный успех ты получишь:\nСЕРТИФИКАТ М ВИДЕО'
    )
    challenge = Challenge(
        image=open('data/pics/аловыкудазвоните.jpg', 'rb').read(),
        name='#аловыкудазвоните',
        description="""\nВот бы можно было звонить с чего угодно. Не надо было бы ждать выхода последнего айфона, расстраиваться, если телефон упал на пол, а если на улице подошли и попросили позвонить - спокойно отдать и не париться. Покажи, как ты звонишь с любого предмета, напоминающего телефон.

    ВНИМАНИЕ! Мы оценим:
    1. Высокое качество работы
    2. Креатив 
    Угодить модератору будет непросто, но ты не сдавайся, если сразу не получится. """,
        price=25000,
        date_to=datetime.date(2026, 3, 30),
        work_type='image',
        userwork_limit=1,
        winner_limit=1,
        is_hard=True,
        prize=prize,
        post_link='https://t.me/ChazyChannel/37',
        promocodes=[]
    )
    session.add(prize)
    session.add(challenge)

    prize = Prize(
        name='СЕРТИФИКАТ ЗОЛОТОЕ ЯБЛОКО',
        description='За успешный успех ты получишь:\nСЕРТИФИКАТ ЗОЛОТОЕ ЯБЛОКО'
    )
    challenge = Challenge(
        image=open('data/pics/какойтыцветок.jpg', 'rb').read(),
        name='#какойтыцветок',
        description="""\nНачнем цикл челленджей #какойты с цветов, растений и прочих деревьев. Сразу скажу, экспериментов с овощами с грядок пока не нужно, какой ты овощ мы еще успеем выяснить. А вот если ты считаешь, что можешь остановить кровь из ранки, то вполне зайдет подорожник. На этом с подсказками всё. 

    ВНИМАНИЕ! Мы оценим:
    1. Высокое качество работы
    2. Креатив 
    Угодить модератору будет непросто, но ты не сдавайся, если сразу не получится. """,
        price=25000,
        date_to=datetime.date(2026, 3, 30),
        work_type='image',
        userwork_limit=1,
        winner_limit=1,
        is_hard=True,
        prize=prize,
        post_link='https://t.me/ChazyChannel/37',
        promocodes=[]
    )
    session.add(prize)
    session.add(challenge)

    prize = Prize(
        name='СЕРТИФИКАТ OZON',
        description='За успешный успех ты получишь:\nСЕРТИФИКАТ OZON'
    )
    challenge = Challenge(
        image=open('data/pics/ктоя.jpg', 'rb').read(),
        name='#ктоя OZON',
        description="""\nТут все предельно просто. Сфотографируйся с тремя предметами, описывающими тебя без лишних слов. Вот тут, например, полицейский, который в свободное от взяток работы время поигрывает в футбол, да еще и фанатеет от Гарри Поттера. Стопудово ему больше всех нравится Филч, он же все-таки полицейский. Предметы должны быть максимально очевидными, если ты окажешься победителем, мы будем отгадывать, кто ты.

    ВНИМАНИЕ! Мы оценим:
    1. Высокое качество работы
    2. Креатив 
    Угодить модератору будет непросто, но ты не сдавайся, если сразу не получится. """,
        price=25000,
        date_to=datetime.date(2026, 3, 30),
        work_type='image',
        userwork_limit=1,
        winner_limit=1,
        is_hard=True,
        prize=prize,
        post_link='https://t.me/ChazyChannel/37',
        promocodes=[]
    )
    session.add(prize)
    session.add(challenge)

    prize = Prize(
        name='СЕРТИФИКАТ Wildberries',
        description='За успешный успех ты получишь:\nСЕРТИФИКАТ Wildberries'
    )

    challenge = Challenge(
        image=open('data/pics/ктоя.jpg', 'rb').read(),
        name='#ктоя Wildberries',
        description="""\nТут все предельно просто. Сфотографируйся с тремя предметами, описывающими тебя без лишних слов. Вот тут, например, полицейский, который в свободное от взяток работы время поигрывает в футбол, да еще и фанатеет от Гарри Поттера. Стопудово ему больше всех нравится Филч, он же все-таки полицейский. Предметы должны быть максимально очевидными, если ты окажешься победителем, мы будем отгадывать, кто ты.

    ВНИМАНИЕ! Мы оценим:
    1. Высокое качество работы
    2. Креатив 
    Угодить модератору будет непросто, но ты не сдавайся, если сразу не получится. """,
        price=25000,
        date_to=datetime.date(2026, 3, 30),
        work_type='image',
        userwork_limit=1,
        winner_limit=1,
        is_hard=True,
        prize=prize,
        post_link='https://t.me/ChazyChannel/37',
        promocodes=[]
    )
    session.add(challenge)
    session.add(prize)

    prize = Prize(
        name='СЕРТИФИКАТ ЭЛЬДОРАДО',
        description='За успешный успех ты получишь:\nСЕРТИФИКАТ ЭЛЬДОРАДО'
    )

    challenge = Challenge(
        image=open('data/pics/слюбимым.jpg', 'rb').read(),
        name='#слюбимым',
        description="""\nПокажи, как проводишь время с тем, кто всегда с тобой, без кого ты не можешь жить. Совместный просмотр сериала, пикник, поездка - что угодно. Чайник, тостер, пылесос, да хоть холодильник. Мы-то знаем, кто тебе по-настоящему дорог.

    ВНИМАНИЕ! Мы оценим:
    1. Высокое качество работы
    2. Креатив 
    Угодить модератору будет непросто, но ты не сдавайся, если сразу не получится. """,
        price=25000,
        date_to=datetime.date(2026, 3, 30),
        work_type='image',
        userwork_limit=1,
        winner_limit=1,
        is_hard=True,
        prize=prize,
        post_link='https://t.me/ChazyChannel/37',
        promocodes=[]
    )
    session.add(challenge)
    session.add(prize)

    session.commit()
