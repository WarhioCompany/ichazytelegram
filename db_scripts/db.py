from db_scripts.db_tables import *
from db_scripts.sql import *


def add_user(name, telegram_id):
    add(USERS_DB, {
        'name': name,
        'coins': 0,
        'prizes': "",
        'telegram_id': str(telegram_id)
    })


def add_challenge(name, desc, price, date_to, photo_bytes, is_hard, coins_prize=None, prize_id=None):
    if bool(coins_prize) == bool(prize_id):
        raise ValueError("Two values cannot be coexistent or non-existent simultaneously")

    add(CHALLENGES_DB, {
        'name': name,
        'desc': desc,
        'image': photo_bytes,
        'price': price,
        'coins_prize': coins_prize,
        'prize_id': prize_id,
        'date_to': date_to,
        'is_hard': is_hard
    })


def add_user_work(user_id, video_bytes, challenge_id, date, is_approved):
    add(USERWORKS_DB, {
        'user_id': user_id,
        'video': video_bytes,
        'challenge_id': challenge_id,
        'date': date,
        'is_approved': is_approved
    })


def get_user_by_telegram_id(telegram_id):
    return get(USERS_DB, where={'telegram_id': str(telegram_id)})


def get_challenge_by_id(id):
    return get(CHALLENGES_DB, where={'id': id})


def is_username_available(username):
    return not bool(get(USERS_DB, where={'name': username}))


create_tables()
