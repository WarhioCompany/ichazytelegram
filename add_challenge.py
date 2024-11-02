from db_data.db_session import session_scope
from db_data.models import Challenge
from os import listdir
from os.path import isfile, join

from db_data import db_session
import datetime
from db_data.models import *

db_session.global_init('db/database.sqlite')


def add_challenge():
    try:
        with session_scope() as session:
            image, video = None, None
            if input('Preview type (img, vid): ').lower().strip() == 'img':
                image = open(input('Relative image path: '), 'rb').read()
            else:
                video = open(input('Relative video path: '), 'rb').read()
            name = input('Name: ')
            description = input('Description: ')
            price = int(input('Price (if free - 0): '))
            date_to = datetime.date(*map(int, input("Date YYYY MM DD: ").split()))
            work_type = input('Work type (image/video): ').lower()
            userwork_limit = int(input("Userwork limit: "))
            winner_limit = int(input("Winner limit: "))

            is_hard = input("Is hard (y/n): ").lower() == 'y'
            if not is_hard:
                coins_prize = int(input("Coins prize: "))
                challenge = Challenge(
                    image=image,
                    video=video,
                    name=name.strip(),
                    description=description.strip(),
                    price=price,
                    date_to=date_to,
                    work_type=work_type.strip(),
                    userwork_limit=userwork_limit,
                    winner_limit=winner_limit,
                    coins_prize=coins_prize,
                    is_hard=is_hard,
                )
            else:
                print('PRIZE')
                prize_name = input('Prize name: ')
                prize_description = input('Prize description')
                prize = Prize(
                    name=prize_name,
                    description=prize_description
                )
                session.add(prize)

                print('Promocodes')
                promocodes_count = int(input('Promocode amount: '))
                promocodes = []
                for _ in range(promocodes_count):
                    promocode_brand = Brand(name='temp brand')
                    promo = input('Promocode: ')
                    telegram_contact = input('telegram contact: ')
                    promocode = Promocode(
                        brand=promocode_brand,
                        promo=promo,
                        telegram_contact=telegram_contact
                    )
                    promocodes.append(promocode)
                    session.add(promocode)

                post_link = input("Post link: ")

                challenge = Challenge(
                    image=image,
                    video=video,
                    name=name.strip(),
                    description=description.strip(),
                    price=price,
                    date_to=date_to,
                    work_type=work_type.strip(),
                    userwork_limit=userwork_limit,
                    winner_limit=winner_limit,
                    is_hard=is_hard,
                    prize=prize,
                    post_link=post_link,
                    promocodes=promocodes
                )
            session.add(challenge)
            session.commit()
    except Exception as e:
        print(e)
        print('Invalid input')
        add_challenge()


add_challenge()