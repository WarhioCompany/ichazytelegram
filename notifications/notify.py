from datetime import datetime

from sqlalchemy import not_
from telebot.apihelper import ApiTelegramException

import event_handler
from event_handler import EventType
from timer import Timer
from db_data import models
from db_data.db_session import session_scope
from db_data.models import UserWork, PromocodeOnModeration, User
from messages_handler import messages
from telebot import types
import user_sub_checker
import logging

from user_sub_checker import MAIN_CHANNEL_ID

logger = logging.getLogger(__name__)


def is_good_time():
    morning = datetime(1, 1, 1, 9, 30).time()
    evening = datetime(1, 1, 1, 21, 00).time()
    return morning < datetime.now().time() < evening


class Notify:
    def __init__(self, bot):
        self.bot = bot
        self.subscription_notifier_timer = Timer(self.subscription_notifier, event_handler.hour())

    def userwork_approved(self, userwork, coefficient):
        with session_scope() as session:
            userwork = session.query(UserWork).filter(UserWork.id == userwork.id).one()
            if userwork.challenge.is_hard:
                self.bot.send_photo(userwork.user_id, photo=userwork.data, caption=messages['userwork_approved_hard'])
            else:
                coins = int(userwork.challenge.coins_prize * coefficient)
                self.bot.send_photo(userwork.user_id, photo=userwork.data, caption=messages['userwork_approved'].format(coins=coins))

    def userwork_disapproved(self, userwork, disapprove_option):
        reason = messages[f'disapprove_{disapprove_option}']
        self.bot.send_photo(userwork.user_id, photo=userwork.data,
                            caption=messages['userwork_disapproved'] + '\n' + reason)

    def balance_update(self, user_id, message, amount):
        if amount == 0:
            return
        try:
            self.send_message(user_id, messages[message].format(amount=amount))
            logger.info(f'sending balance update to {user_id} ({amount})')
        except ApiTelegramException as e:
            logger.info(f"can't send balance update to {user_id} {e.description}")

    def subscription_notifier(self):
        registration_events = event_handler.get_active_events(EventType.user_registered)
        for event in registration_events:
            if user_sub_checker.is_subscribed(event.user_id):
                logger.info(f'{event.user_id} subscribed, removing event')
                event_handler.remove_event(event.user_id, EventType.user_registered)
                return

            logger.info(f'{event.user_id} registered {event.time_elapsed() / 60 / 60 / 24} days ago, but has not subscribed to the channel yet')

            if event.time_elapsed() > event_handler.week() and is_good_time():
                logger.info(f'sending subscription notifier to {event.user_id}')
                self.send_message(event.user_id, messages['subscribe_to_the_channel'], parse_mode='MarkdownV2')
                event_handler.remove_event(event.user_id, EventType.user_registered)

    def send_message(self, user_id, message, **kwargs):
        try:
            self.bot.send_message(user_id, message, **kwargs)
            logger.info(f'NOTIFY: {user_id} ({message[:10]}...)')
        except ApiTelegramException as e:
            logger.info(f"can't send message to {user_id} ({e.description})")

class AdminNotify:
    def __init__(self):
        self.bot = None
        self.admin_ids = set()

    def set_bot(self, bot):
        self.bot = bot

    def add_admin(self, admin_id):
        self.admin_ids.add(admin_id)

    def send_everyone(self, message, reply_markup=None):
        for admin_id in self.admin_ids:
            self.bot.send_message(admin_id, message, reply_markup=reply_markup)

    def user_used_promocode(self, user_id, promocode: models.Promocode):
        # here are buttons, but they are not applied fsr

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Approve', callback_data=f'promo_confirmation approve {user_id} {promocode.id}'),
                   types.InlineKeyboardButton('Decline', callback_data=f'promo_confirmation decline'))
        with session_scope() as session:
            user = session.query(User).filter(User.telegram_id == user_id).one()
            self.send_everyone(f'@{user.name} использовал промокод: {promocode.promo}')

    def start_notifying(self):
        Timer(self.new_info_to_check, 5 * event_handler.hour())

    def new_info_to_check(self):
        with session_scope() as session:
            new_userworks = session.query(UserWork).filter(UserWork.status == 'on_moderation').all()
            new_promocodes = session.query(PromocodeOnModeration).all()
            if len(new_userworks) == 0 and len(new_promocodes) == 0:
                return
            if is_good_time():
                self.send_everyone(f'Новых работ: {len(new_userworks)}\nНовых промокодов: {len(new_promocodes)}')
            else:
                print(datetime.now().time(), 'is too late/early (9:30 to 21:00)')

    def prize_barrier_suffice(self, prize):
        if is_good_time():
            self.send_everyone(f'Барьер приза "{prize.name}" ({prize.barrier_value} {prize.barrier_type}) преодолен!')