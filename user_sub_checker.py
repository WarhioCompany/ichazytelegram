import json

from telebot.apihelper import ApiTelegramException
from timer import Timer
import event_handler
from event_handler import EventType
from logger import bot_logger


bot_instance = None


def user_status(user_id):
    if not bot_instance:
        print('UserSubChecker was not initialized')
        return
    status = ''
    try:
        response = bot_instance.get_chat_member("@ChazyChannel", user_id)
        status = response.status
    except ApiTelegramException as e:
        if e.result_json['description'] in ['Bad Request: PARTICIPANT_ID_INVALID', 'Bad Request: member list is inaccessible']:
            pass
        else:
            print('ANOTHER TYPE OF ERROR IN USER STATUS: ', e.result_json['description'])
    if status in ['left', '']:
        return status
    else:
        if status not in ['member', 'administrator']:
            print('What is this status (user_status function): ', user_id, status)
        return 'subscribed'


class UserSubChecker:
    def __init__(self, bot, channel_id, user_subbed_func, seconds_delay=60):
        global bot_instance
        bot_instance = bot

        self.channel_id = channel_id
        self.bot = bot

        self.user_subbed_func = user_subbed_func

        self.timer = Timer(self.loop, seconds_delay)

    def loop(self):
        invited_users = event_handler.get_active_events(EventType.user_was_invited)
        for invited_user in invited_users:
            status = user_status(invited_user.user_id)
            if status == 'subscribed':
                bot_logger.debug_log(f'invited user {invited_user.user_id} subscribed to the channel')
                event_handler.add_event(invited_user.user_id, EventType.user_subscribed)
                event_handler.remove_event(invited_user.user_id, EventType.user_was_invited)

        subscribed_users = event_handler.get_active_events(EventType.user_subscribed)
        for subscribed_user in subscribed_users:
            status = user_status(subscribed_user.user_id)
            if status == 'left':
                bot_logger.debug_log(f'invited user {invited_user.user_id} left the channel, so inviter will not receive coins')
                event_handler.remove_event(subscribed_user.user_id, EventType.user_subscribed)
            elif subscribed_user.time_elapsed() > 3 * event_handler.day():
                bot_logger.debug_log(f'invited user {invited_user.user_id} stayed subbed for three days, rewarding user')
                self.user_subbed_func(subscribed_user.user_id)
                event_handler.remove_event(subscribed_user.user_id, EventType.user_subscribed)


