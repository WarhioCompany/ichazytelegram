from db_data.db_session import session_scope
from db_data.models import Promocode, PromocodeOnModeration, User
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
                # TODO: try boost type promocodes
                self.notify.send_message(user_id, messages['promocode_incorrect'])


    def enter_coins_promocode(self, promocode, user_id):
        status = self.get_status(promocode, user_id)
        if status == 'on_moderation':
            self.notify.send_message(user_id, messages['promocode_on_moderation'])
        elif promocode.is_expired:
            self.notify.send_message(user_id, messages['promocode_expired'])
        elif status == 'used':
            self.notify.send_message(user_id, messages['promocode_already_used'])
        else:
            if promocode.need_confirmation:
                self.notify.send_message(user_id, messages['promocode_correct'])
                self.send_promocode_to_moderation(promocode, user_id)
            else:
                self.use_promocode(promocode, user_id)


    def get_status(self, promocode, user_id):
        with session_scope() as session:
            user = session.query(User).filter(User.telegram_id == user_id).one()
            if promocode in user.used_promocodes:
                return 'used'
            on_moderation = session.query(PromocodeOnModeration).filter(PromocodeOnModeration.promocode_id == promocode.id).all()
            if on_moderation:
                return 'on_moderation'
            return 'new'


    def send_promocode_to_moderation(self, promocode, user_id):
        with session_scope() as session:
            promocode_on_moderation = PromocodeOnModeration(
                user_id=user_id,
                promocode_id = promocode.id
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



class BoostPromocodeManager:
    def __init__(self):
        pass