from datetime import datetime

from sqlalchemy import not_

import event_handler
from event_handler import EventType
from timer import Timer
from db_data import models
from db_data.db_session import session_scope
from db_data.models import UserWork, UnauthorizedPromocode
from messages_handler import messages
from telebot import types
import user_sub_checker


def is_good_time():
    morning = datetime(1, 1, 1, 9, 30).time()
    evening = datetime(1, 1, 1, 21, 00).time()
    return morning < datetime.now().time() < evening


class Notify:
    def __init__(self, bot):
        self.bot = bot
        self.subscription_notifier_timer = Timer(self.subscription_notifier, event_handler.hour())

    def userwork_approved(self, userwork):
        with session_scope() as session:
            userwork = session.query(UserWork).filter(UserWork.id == userwork.id).one()
            if userwork.challenge.is_hard:
                self.bot.send_photo(userwork.user_id, photo=userwork.data, caption=messages['userwork_approved_hard'])
            else:
                self.bot.send_photo(userwork.user_id, photo=userwork.data, caption=messages['userwork_approved'].format(coins=userwork.challenge.coins_prize))

    def userwork_disapproved(self, userwork, disapprove_option):
        reason = messages[f'disapprove_{disapprove_option}']
        self.bot.send_photo(userwork.user_id, photo=userwork.data,
                            caption=messages['userwork_disapproved'] + '\n' + reason)

    def balance_update(self, user_id, message, amount):
        self.bot.send_message(user_id, messages[message].format(amount=amount))

    def subscription_notifier(self):
        registration_events = event_handler.get_active_events(EventType.user_registered)
        for event in registration_events:
            user_status = user_sub_checker.user_status(event.user_id)
            print(user_status)
            if user_status == 'subscribed':
                event_handler.remove_event(event.user_id, EventType.user_registered)
                return

            if event.time_elapsed() > event_handler.week() and is_good_time():
                self.bot.send_message(event.user_id, messages['subscribe_to_the_channel'], parse_mode='MarkdownV2')
                event_handler.remove_event(event.user_id, EventType.user_registered)


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

    def user_used_promocode(self, user: types.User, promocode: models.Promocode):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Approve', callback_data=f'promo_confirmation approve {user.id} {promocode.id}'),
                   types.InlineKeyboardButton('Decline', callback_data=f'promo_confirmation decline'))
        self.send_everyone(f'@{user.username} использовал промокод: {promocode.promo}')

    def start_notifying(self):
        Timer(self.new_info_to_check, 5 * event_handler.hour())

    def new_info_to_check(self):
        with session_scope() as session:
            new_userworks = session.query(UserWork).filter(not_(UserWork.is_approved)).all()
            new_promocodes = session.query(UnauthorizedPromocode).all()
            if len(new_userworks) == 0 and len(new_promocodes) == 0:
                return
            if is_good_time():
                self.send_everyone(f'Новых работ: {len(new_userworks)}\nНовых промокодов: {len(new_promocodes)}')
            else:
                print(datetime.now().time(), 'is too late/early (9:30 to 21:00)')