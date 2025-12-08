from datetime import datetime

from db_data.db_session import session_scope
from db_data.models import Promocode, User, BoostPromocode, UserBoostPromocode
from messages_handler import messages


def use_promocode(promocode_id, user_id, notify):
    with session_scope() as session:
        user = session.query(User).filter(User.telegram_id == user_id).one()
        promocode = session.query(Promocode).filter(Promocode.id == promocode_id).one()

        user.used_promocodes.append(promocode)

        if promocode.coins != 0:
            user.coins += promocode.coins
            notify.balance_update(user_id, "promocode_add_coins", promocode.coins)
        else:
            notify.send_message(user_id, messages["promocode_without_coins"])
        session.commit()


def use_boost_promocode(boost_promocode_id, user_id, notify):
    with session_scope() as session:
        user = session.query(User).filter(User.telegram_id == user_id).one()
        boost_promocode = session.query(BoostPromocode).filter(BoostPromocode.id == boost_promocode_id).one()

        user_boost_promocode = UserBoostPromocode(boost_promocode, user)
        user.used_boost_promocodes.append(user_boost_promocode)

        session.commit()

        notify.send_message(user_id, messages['boost_promocode_correct'].format(coefficient=boost_promocode.coefficient))


def delete_inactive_promocodes(user_id):
    with session_scope() as session:
        user = session.query(User).filter(User.telegram_id == user_id).one()

        current_boost_promocode = None
        for boost_promocode in user.used_boost_promocodes:
            # check whether boost promocode is used up
            if (
                    boost_promocode.boost_promocode.promocode_type == 'date' and datetime.now().timestamp() > boost_promocode.value
                    or boost_promocode.boost_promocode.promocode_type == 'count' and boost_promocode.value <= 0):
                session.delete(boost_promocode)
            else:
                # improbable
                if current_boost_promocode:
                    print(
                        f'USER {user_id} has more than one boost promocode {[promocode.id for promocode in user.used_boost_promocodes]}')

                current_boost_promocode = boost_promocode

        session.commit()
    return current_boost_promocode


def get_active_boost_promocode(user_id):
    with session_scope() as session:
        user = session.query(User).filter(User.telegram_id == user_id).one()
        if len(user.used_boost_promocodes) != 0:
            return user.used_boost_promocodes[0]
        else:
            return None


def get_user_coefficient(user_id):
    promo = get_active_boost_promocode(user_id)
    if promo:
        return promo.boost_promocode.coefficient
    return 1


def get_coefficient_and_use(user_id):
    with session_scope() as session:
        buf = get_active_boost_promocode(user_id)
        if not buf:
            return 1

        promocode = session.query(UserBoostPromocode).filter(UserBoostPromocode.id == buf.id).one()
        print(promocode.boost_promocode.promocode_type)
        if promocode.boost_promocode.promocode_type == 'count':
            promocode.value -= 1
            session.commit()

        coefficient = promocode.boost_promocode.coefficient
        delete_inactive_promocodes(user_id)
        return coefficient

