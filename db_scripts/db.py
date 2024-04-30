from db_scripts.db_tables import *
from db_scripts.sql import *


def add_user(name, telegram_id):
    add(USERS_DB, {
        'name': name,
        'coins': 0,
        'prizes': "",
        'telegram_id': str(telegram_id)
    })


def add_challenge(name, desc, price, date_to, photo_bytes, is_hard, work_type, coins_prize=None, prize_id=None):
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
        'work_type': work_type,
        'is_hard': is_hard
    })


def add_user_work(user_id, data, challenge_id, type, date):
    add(USERWORKS_DB, {
        'user_id': user_id,
        'data': data,
        'challenge_id': challenge_id,
        'date': date,
        'type': type,
        'like_count': 0,
        'is_approved': False
    })


def get_user_by_telegram_id(telegram_id):
    return get(USERS_DB, where={'telegram_id': str(telegram_id)})


def get_challenge_by_id(challenge_id):
    return get(CHALLENGES_DB, where={'id': challenge_id})


def get_user_work_by_id(work_id):
    return get(USERWORKS_DB, where={'id': work_id})


def get_user_works_ids_by_challenge_id(challenge_id):
    return get(USERWORKS_DB, select=['id'], where={'challenge_id': challenge_id})


def is_username_available(username):
    return not bool(get(USERS_DB, where={'name': username}))


def get_challenges_amount():
    return count(CHALLENGES_DB)


def get_user_works_amount(challenge_id):
    return count(USERWORKS_DB, where={'challenge_id': challenge_id})


def get_user_username(user_id):
    return get(USERS_DB, select=['name'], where={'id': user_id})[0]['name']


def update_like_count_userwork(userwork_id, like_count):
    return update(USERWORKS_DB, {'like_count': like_count}, {'id': userwork_id})


create_tables()
