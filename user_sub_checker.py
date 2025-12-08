import json
import logging

from telebot.apihelper import ApiTelegramException
from timer import Timer
import event_handler
from event_handler import EventType
from logger import bot_logger


bot_instance = None
MAIN_CHANNEL_ID = "@chazychannel"
logger = logging.getLogger(__name__)

def get_chat_member_status(user_id, chat_id):
    try:
        response = bot_instance.get_chat_member(chat_id, user_id)
        status = response.status
    except ApiTelegramException as e:
        logger.error(f'{chat_id}(title: "{bot_instance.get_chat(chat_id).title}") {e.result_json["description"]} (user_id: {user_id})')
        status = 'error'
    return status


def get_chat_member_count(chat_id=MAIN_CHANNEL_ID):
    return bot_instance.get_chat_member_count(chat_id)

def user_status(user_id, chat_id=MAIN_CHANNEL_ID):
    # breaks down user status to either subscribed, left or error
    if not bot_instance:
        print('UserSubChecker was not initialized')
        return

    status = get_chat_member_status(user_id, chat_id)

    if status in ['member', 'administrator', 'creator']:
        return 'subscribed'
    elif status in ['restricted', 'kicked', 'left']: # fsr status 'left' is also for members, that have never been subscribed to the channel
        return 'left'
    elif status == 'error':
        return 'error'
    raise Exception(f'unknown status: {status}')


def is_subscribed(user_id, chat_id=MAIN_CHANNEL_ID):
    return user_status(user_id, chat_id) == 'subscribed'

class UserSubChecker:
    def __init__(self, bot, user_subbed_func, seconds_delay):
        global bot_instance
        bot_instance = bot

        self.bot = bot

        self.user_subbed_func = user_subbed_func

        self.timer = Timer(self.reward_users_with_good_referrals, seconds_delay)

    def reward_users_with_good_referrals(self):
        self.check_whether_invited_users_have_subscribed()
        self.check_status_of_subscribed_users()


    def check_whether_invited_users_have_subscribed(self):
        invited_users = event_handler.get_active_events(EventType.user_was_invited)
        for invited_user in invited_users:
            if is_subscribed(invited_user.user_id):
                bot_logger.debug_log(f'invited user {invited_user.user_id} subscribed to the channel')
                event_handler.add_event(invited_user.user_id, EventType.user_subscribed)
                event_handler.remove_event(invited_user.user_id, EventType.user_was_invited)


    def check_status_of_subscribed_users(self):
        subscribed_users = event_handler.get_active_events(EventType.user_subscribed)
        for subscribed_user in subscribed_users:
            status = user_status(subscribed_user.user_id)
            if status == 'error':
                continue

            if status == 'left':
                bot_logger.debug_log(
                    f'invited user {subscribed_user.user_id} left the channel, so inviter will not receive coins')
                event_handler.remove_event(subscribed_user.user_id, EventType.user_subscribed)
            elif status == 'subscribed' and subscribed_user.time_elapsed() > 3 * event_handler.day():
                bot_logger.debug_log(
                    f'invited user {subscribed_user.user_id} stayed subbed for three days, rewarding user')
                self.user_subbed_func(subscribed_user.user_id)
                event_handler.remove_event(subscribed_user.user_id, EventType.user_subscribed)