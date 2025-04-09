import promocode_tools
from db_data.db_session import session_scope
from db_data.models import Promocode, PromocodeOnModeration, User, BoostPromocode, UserBoostPromocode
from sqlalchemy import and_

from messages_handler import messages


class PromocodeManager:
    def __init__(self, notify, admin_notify):
        self.notify = notify
        self.admin_notify = admin_notify


    def enter_promocode(self, user_id, promocode_text):
        with session_scope() as session:
            promocodes = session.query(Promocode).filter(Promocode.promo == promocode_text).all()
            if len(promocodes):
                self.enter_coins_promocode(promocodes[0], user_id)
            else:
                boost_promocodes = session.query(BoostPromocode).filter(BoostPromocode.promo == promocode_text).all()
                if len(boost_promocodes):
                    self.enter_boost_promocode(boost_promocodes[0], user_id)
                else:
                    self.notify.send_message(user_id, messages['promocode_incorrect'])


    def send_status_message(self, user_id, status):
        if status == 'on_moderation':
            self.notify.send_message(user_id, messages['promocode_on_moderation'])
        elif status == 'expired':
            self.notify.send_message(user_id, messages['promocode_expired'])
        elif status == 'used':
            self.notify.send_message(user_id, messages['promocode_already_used'])

    def enter_coins_promocode(self, promocode, user_id):
        status = self.get_promocode_status(promocode, user_id)
        if status != 'new':
            self.send_status_message(user_id, status)
        elif promocode.need_confirmation:
            self.notify.send_message(user_id, messages['promocode_correct'])
            self.send_promocode_to_moderation(promocode, user_id, 'coins')
        else:
            promocode_tools.use_promocode(promocode.id, user_id, self.notify)

    def enter_boost_promocode(self, boost_promocode, user_id):
        status = self.get_boost_promocode_status(boost_promocode, user_id)
        if status != 'new':
            self.send_status_message(user_id, status)
        elif boost_promocode.need_confirmation:
            self.notify.send_message(user_id, messages['promocode_correct'])
            self.send_promocode_to_moderation(boost_promocode, user_id, 'boost')
        else:
            promocode_tools.use_boost_promocode(boost_promocode.id, user_id, self.notify)

    def get_promocode_status(self, promocode, user_id):
        if promocode.is_expired:
            return 'expired'

        with session_scope() as session:
            user = session.query(User).filter(User.telegram_id == user_id).one()
            if promocode in user.used_promocodes:
                return 'used'
            on_moderation = session.query(PromocodeOnModeration).filter(PromocodeOnModeration.promocode_id == promocode.id).all()
            if on_moderation:
                return 'on_moderation'
            return 'new'

    def get_boost_promocode_status(self, boost_promocode, user_id):
        if boost_promocode.is_expired:
            return 'expired'

        with session_scope() as session:
            user = session.query(User).filter(User.telegram_id == user_id).one()
            user_boost_promocode = session.query(UserBoostPromocode).filter(
                and_(UserBoostPromocode.boost_promocode_id == boost_promocode.id,
                     UserBoostPromocode.user_id == user_id)).all()

            if not user_boost_promocode:
                return 'new'

            user_boost_promocode = user_boost_promocode[0]

            if user_boost_promocode in user.used_boost_promocodes:
                return 'used'
            elif not user_boost_promocode.confirmed:
                return 'on_moderation'
            else:
                print('status error ')


    def send_promocode_to_moderation(self, promocode, user_id, promocode_type):
        with session_scope() as session:
            promocode_on_moderation = PromocodeOnModeration(
                user_id=user_id,
                promocode_id = promocode.id,
                promocode_type=promocode_type
            )
            session.add(promocode_on_moderation)
            session.commit()
        self.admin_notify.user_used_promocode(user_id, promocode)

    def use_promocode(self, promocode, user_id):
        with session_scope() as session:
            user = session.query(User).filter(User.telegram_id == user_id).one()
            promocode = session.query(Promocode).filter(Promocode.id == promocode.id).one()

            user.used_promocodes.append(promocode)

            if promocode.coins != 0:
                user.coins += promocode.coins
                self.notify.balance_update(user_id, "promocode_add_coins", promocode.coins)
            else:
                self.notify.send_message(user_id, "Похоже, что этот промокод ничего не делает...")
            session.commit()

