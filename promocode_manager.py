from telebot.types import InputMediaPhoto

import promocode_tools
import user_sub_checker
from db_data.db_session import session_scope
from db_data.models import Promocode, PromocodeOnModeration, User, BoostPromocode, UserBoostPromocode
from sqlalchemy import and_

from messages_handler import messages
from userwrapper import UserData


class PromocodeManager:
    def __init__(self, notify, admin_notify):
        self.notify = notify
        self.admin_notify = admin_notify


    def enter_promocode(self, user: UserData, promocode_text):
        with session_scope() as session:
            promocodes = session.query(Promocode).filter(Promocode.promo == promocode_text).all()
            if len(promocodes): # Entered promocode is for coins
                self.enter_coins_promocode(promocodes[0], user)
            else:
                boost_promocodes = session.query(BoostPromocode).filter(BoostPromocode.promo == promocode_text).all()
                if len(boost_promocodes): # Entered promocode is boost
                    self.enter_boost_promocode(boost_promocodes[0], user)
                else: # Promocode not found
                    self.notify.send_message(user.user_id, messages['promocode_incorrect'])


    def send_status_message(self, user_id, status, **kwargs):
        if status == 'on_moderation':
            self.notify.send_message(user_id, messages['promocode_on_moderation'])
        elif status == 'expired':
            self.notify.send_message(user_id, messages['promocode_expired'])
        elif status == 'used':
            self.notify.send_message(user_id, messages['promocode_already_used'])
        elif status == 'sending_to_moderation':
            self.notify.send_message(user_id, messages['promocode_sending_to_moderation'])
        elif status == 'not_subscribed':
            self.notify.send_message(user_id, messages['promocode_not_subscribed'].format(**kwargs))

    def enter_coins_promocode(self, promocode, user):
        status = self.get_promocode_status(promocode, user.user_id)
        if status != 'new': # if promocode is either used, on_moderation or expired
            self.send_status_message(user.user_id, status, channel_id=promocode.required_channel_id)
        elif promocode.is_image_proof_required:
            def handle_image_proof(answers):
                if isinstance(answers[0], InputMediaPhoto):
                    self.send_promocode_to_moderation(promocode, user.user_id, 'coins', answers[0].media)
                else:
                    user.chainer.clear_chain()
                    user.chainer.chain([messages['promocode_send_proof']], [handle_image_proof])

            user.chainer.chain([messages['promocode_send_proof']], [handle_image_proof])
        elif promocode.need_confirmation: # promocode needs moder's approval, sending for moderation
            self.send_promocode_to_moderation(promocode, user.user_id, 'coins')
        else: # doesn't require approval, just use
            promocode_tools.use_promocode(promocode.id, user.user_id, self.notify)


    def enter_boost_promocode(self, boost_promocode, user):
        status = self.get_boost_promocode_status(boost_promocode, user.user_id)
        if status != 'new':
            self.send_status_message(user.user_id, status)
        elif boost_promocode.need_confirmation:
            self.send_promocode_to_moderation(boost_promocode, user.user_id, 'boost')
        else:
            promocode_tools.use_boost_promocode(boost_promocode.id, user.user_id, self.notify)

    def get_promocode_status(self, promocode, user_id):
        # expired - promo is expired
        # used - user has already used it
        # on_moderation - promo is waiting for moder's approval
        # new - nothing above

        if promocode.is_expired:
            return 'expired'

        if promocode.is_subscription_required and not user_sub_checker.is_subscribed(user_id, promocode.required_channel_id):
            return 'not_subscribed'

        with session_scope() as session:
            user = session.query(User).filter(User.telegram_id == user_id).one()
            if promocode in user.used_promocodes:
                return 'used'
            on_moderation = session.query(PromocodeOnModeration).filter(PromocodeOnModeration.promocode_id == promocode.id).all()
            if on_moderation:
                return 'on_moderation'
            return 'new'

    def get_boost_promocode_status(self, boost_promocode, user_id):
        # statuses are the same with get_promocode_status()

        if boost_promocode.is_expired:
            return 'expired'

        with session_scope() as session:
            user = session.query(User).filter(User.telegram_id == user_id).one()
            user_boost_promocode = session.query(UserBoostPromocode).filter(
                and_(UserBoostPromocode.boost_promocode_id == boost_promocode.id,
                     UserBoostPromocode.user_id == user_id)).all() # search for the boost promo bounded to the user

            if not user_boost_promocode:
                return 'new'

            user_boost_promocode = user_boost_promocode[0]

            if user_boost_promocode in user.used_boost_promocodes:
                return 'used'
            elif not user_boost_promocode.confirmed:
                return 'on_moderation'
            else:
                print('status error ')


    def send_promocode_to_moderation(self, promocode, user_id, promocode_type, image_proof=None):
        self.send_status_message(user_id, 'sending_to_moderation')
        with session_scope() as session:
            promocode_on_moderation = PromocodeOnModeration(
                user_id=user_id, # user that has used the promocode
                promocode_id = promocode.id, # original promocode's id
                promocode_type=promocode_type, # coins, boost
                image_proof=image_proof
            )
            session.add(promocode_on_moderation)
            session.commit()
        self.admin_notify.user_used_promocode(user_id, promocode) # notify admins that some user has used a promo

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

