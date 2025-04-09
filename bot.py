import logging
import sys

import telebot
from telebot import types
from commands_manager.commands import set_commands

from messages_handler import messages
from promocode_manager import PromocodeManager

from userwrapper import UserData
from db_data.models import User, Promocode

from db_data import db_session
from db_data.db_session import session_scope

from notifications.notify import Notify, AdminNotify
import admin_bot.admin_bot as admin_bot

import traceback
from logger import bot_logger as log
from backuper import backuper
import event_handler
from event_handler import EventType

from exception_handler import ExceptionHandler

users = {}


def get_token():
    return input('Bot token: ')

def start_bot(token, admin_token, db_path):
    db_session.global_init(db_path)
    bot = telebot.TeleBot(token, exception_handler=ExceptionHandler())

    notify = Notify(bot)
    admin_notify = AdminNotify()

    promocode_manager = PromocodeManager(notify, admin_notify)

    admin_bot.start_bot(admin_token, notify, admin_notify)

    # FUNCTIONS:
    def send_message(user_message=None, message_id=None, user_id=None, text=None, markup=None, parse_mode=None,
                     **kwargs):
        if not user_id:
            if not user_message:
                raise Exception('Have to provide either user_id or user_message')
            user_id = user_message.from_user.id
        if not text:
            if not message_id:
                raise Exception('No text provided')
            text = messages[message_id]
        text = text.format(**kwargs)

        def escape(msg):
            return msg.translate(str.maketrans({"!": r"\!",
                                                "^": r"\^",
                                                "#": r"\#",
                                                ".": r"\.",
                                                "-": r"\-",
                                                "(": r"\(",
                                                ")": r"\)",
                                                "[": r'\[',
                                                "]": r'\]'})).replace(r'\\', '')

        if text.startswith('~'):
            text = escape(text[1:])
            parse_mode = 'MarkdownV2'

        bot.send_message(
            user_id,
            text,
            reply_markup=markup,
            parse_mode=parse_mode,
            disable_web_page_preview=True,
        )

    def get_user(message):
        if message.from_user.id in users:
            return users[message.from_user.id]
        else:
            # it's for waiting_for checkers
            return UserData(bot, '')

    def send_challenge_page(message):
        viewer = get_user(message).challenge_viewer
        can_send_page = check_is_username_the_same(message)

        if can_send_page:
            viewer.show_challenges()

    def greeting(message):
        with session_scope() as session:
            user = session.query(User).filter(User.telegram_id == message.from_user.id).first()
            send_message(message, "user_info", coins=user.coins)
        send_challenge_page(message)

    def check_is_username_the_same(message):
        with session_scope() as session:
            telegram_id = message.from_user.id
            user = session.query(User).filter(User.telegram_id == telegram_id).one()
            if message.from_user.username:
                if message.from_user.username != user.telegram_username:
                    user.telegram_username = message.from_user.username
            else:
                # doesn't have a username, will be using user's phone
                if user.telegram_username == '':
                    get_phone_number_message(message)
                    return False
            user.telegram_name = message.from_user.full_name
            session.commit()
        return True

    def get_phone_number_message(message):
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
        button_phone = types.KeyboardButton(text='Поделиться номером', request_contact=True)
        keyboard.add(button_phone)  # Add this button
        # bot.send_message(message.chat.id, messages['send_phone_number'], reply_markup=keyboard)
        send_message(user_id=message.chat.id, message_id='send_phone_number', markup=keyboard)

    @bot.message_handler(content_types=['contact'])
    def phone_number(message):
        if message.contact is not None:
            with session_scope() as session:
                telegram_id = message.from_user.id
                user = session.query(User).filter(User.telegram_id == telegram_id).one()
                user.telegram_username = message.contact.phone_number
                session.commit()
            # bot.send_message(message.chat.id, messages['got_phone_number'], reply_markup=types.ReplyKeyboardRemove())
            send_message(user_id=message.chat.id, message_id='got_phone_number',
                         reply_markup=types.ReplyKeyboardRemove())
            send_challenge_page(message)
        else:
            log.warning_user_activity(message.from_user.id, 'has no phone number nor username')

    # COMMANDS:
    @bot.message_handler(commands=['start', 'help'])
    def start_command(message):
        set_commands(message, bot, 'commands_manager/commands_config.json')

        start_args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        invited_by = start_args[0] if start_args else ''

        log.log_message_sent(message)

        user = UserData(bot, message.from_user.id, invited_by=invited_by)
        users[message.from_user.id] = user

        if user.user():
            send_message(message, "welcome_username", username=user.user().name)
            greeting(message)
            user.bot = bot
        else:
            send_message(message, "new_user")
            send_message(message, "enter_nickname")
            user.waiting_for = 'name'

    @bot.callback_query_handler(func=lambda call: not get_user(call))
    def non_existent_user(call):
        log.log_user_activity(call.from_user.id, "did not start the bot")
        send_message(call, "start_error_message")
        bot.answer_callback_query(call.id)

    @bot.message_handler(func=lambda call: not get_user(call))
    def non_existent_user(message):
        log.log_user_activity(message.from_user.id, "did not start the bot")
        send_message(message, "start_error_message")

    @bot.message_handler(commands=['view_challenges'])
    def view_challenges(message):
        log.log_message_sent(message)
        send_challenge_page(message)

    @bot.message_handler(commands=['my_works'])
    def my_works(message):
        log.log_message_sent(message)
        get_user(message).private_userworks_viewer.send_mode_picker()

    @bot.message_handler(commands=['balance'])
    def balance(message):
        log.log_message_sent(message)
        send_message(message, "balance", coins=get_user(message).user().coins)

    @bot.message_handler(commands=['shop'])
    def shop(message):
        log.log_message_sent(message)
        send_message(message, "shop")

    @bot.message_handler(commands=['partnership'])
    def partnership(message):
        log.log_message_sent(message)
        send_message(message, "partnership")

    @bot.message_handler(commands=['promocode'])
    def promocode(message):
        log.log_message_sent(message)
        get_user(message).waiting_for = 'promocode'
        send_message(message, "enter_promocode")

    @bot.message_handler(commands=['support'])
    def support(message):
        log.log_message_sent(message)
        send_message(message, "support")

    @bot.message_handler(commands=['get_my_link'])
    def get_my_link(message):
        log.log_message_sent(message)
        send_message(message, "get_my_link", link=f'https://t.me/chazychannelbot?start={message.from_user.id}')

    # CALLBACKS:
    @bot.callback_query_handler(func=lambda call: call.data == 'participate')
    def participate(call):
        log.log_user_callback(call)
        user = get_user(call)

        error_message = user.challenge_viewer.can_submit()
        if error_message:
            # bot.send_message(call.from_user.id, error_message, parse_mode='MarkdownV2', disable_web_page_preview=True)
            send_message(call, text=error_message)
        else:
            user.waiting_for = 'work'
            send_message(call, "user_participation")
        bot.answer_callback_query(call.id)

    # @bot.callback_query_handler(func=lambda call: call.data.startswith('challenge_card'))
    # def picking_challenge(call):
    #     # call: 'challenge_card {id}'
    #     user = get_user(call)
    #     challenge_id = int(call.data.split()[1])
    #
    #     bot.answer_callback_query(call.id)
    #     user.challenge_viewer.send_challenge(challenge_id)
    #     if user.userworks_viewer.does_exist():
    #         user.userworks_viewer.show_works(user.challenge_viewer.challenge_card.current_challenge.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('prev_page'))
    def prev_page(message):
        log.log_user_callback(message)
        user = get_user(message)

        identifier = message.data.split()[-1]

        if identifier == 'challenges':
            user.challenge_viewer.prev_page()

            # ОБНУЛЯЕМ КНОПКУ "Участвовать"
            user.waiting_for = ''
        elif identifier == 'userworks':
            user.userworks_viewer.prev_page()
        elif identifier == 'private_userworks':
            user.private_userworks_viewer.prev_page()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('next_page'))
    def next_page(message):
        log.log_user_callback(message)
        user = get_user(message)
        identifier = message.data.split()[-1]

        if identifier == 'challenges':
            user.challenge_viewer.next_page()

            # ОБНУЛЯЕМ КНОПКУ "Участвовать"
            user.waiting_for = ''
        elif identifier == 'userworks':
            user.userworks_viewer.next_page()
        elif identifier == 'private_userworks':
            user.private_userworks_viewer.next_page()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data == 'user_works')
    def show_user_works(message):
        log.log_user_callback(message)
        user = get_user(message)

        user.userworks_viewer.show_works(user.challenge_viewer.current_challenge.id)
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('userwork_like'))
    def like_userwork(message):
        log.log_user_callback(message)
        user = get_user(message)

        data = message.data.split()
        work_id = int(data[-1])
        identifier = data[1]
        if identifier == 'userworks':
            user.userworks_viewer.like_userwork(work_id)
        elif identifier == 'private_userworks':
            user.private_userworks_viewer.like_userwork(work_id)
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('delete_private_userwork '))
    def delete_private_userwork(message):
        log.log_user_callback(message)
        work_id = int(message.data.split()[-1])

        get_user(message).private_userworks_viewer.send_delete_confirmation(work_id)
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data == 'delete_private_userwork_confirm')
    def delete_private_userwork_confirm(message):
        log.log_user_callback(message)
        get_user(message).private_userworks_viewer.delete_userwork()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data == 'delete_private_userwork_decline')
    def delete_private_userwork_decline(message):
        log.log_user_callback(message)
        get_user(message).private_userworks_viewer.delete_confirmation_message()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('my_works '))
    def my_works_mode(message):
        log.log_user_callback(message)
        get_user(message).private_userworks_viewer.show_works('disapproved' not in message.data)
        bot.answer_callback_query(message.id)

    # User manipulation:
    @bot.message_handler(func=lambda message: get_user(message).waiting_for == 'name')
    def new_user(message):
        log.log_user_activity(message.from_user.id, f'registration end, bot name: {message.text}')

        user = users[message.from_user.id]
        user = UserData(bot, message.from_user.id, name=message.text, invited_by=user.invited_by)
        users[message.from_user.id] = user

        if user.invited_by:
            event_handler.add_event(message.from_user.id, EventType.user_was_invited)

        event_handler.add_event(message.from_user.id, EventType.user_registered)
        send_message(message, 'registration_end')
        greeting(message)

    @bot.message_handler(func=lambda message: get_user(message).waiting_for == 'promocode')
    def enter_promocode(message):
        promocode_manager.enter_promocode(message.from_user.id, message.text)

    # USERWORK SUBMISSION
    @bot.message_handler(content_types=['video'])
    def upload_work_video(message):
        user = get_user(message)
        if user.waiting_for != 'work':
            log.log_user_activity(message.from_user.id, 'tried to send VIDEO but did not select the challenge')
            send_message(message, "pick_challenge")
            return

        challenge_name = user.challenge_viewer.current_challenge.name
        log.log_user_activity(message.from_user.id, f'submitted VIDEO userwork for {challenge_name}')

        file_info = bot.get_file(message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        user.challenge_viewer.submit_userwork(downloaded_file, 'video')
        # I'm kinda paranoid that it can cause some problems in the future, so just keep in mind it's here
        user.waiting_for = ''

    @bot.message_handler(content_types=['photo'])
    def upload_work_photo(message):
        # ФУНКЦИЯ ВЫПОЛНЯЕТСЯ АСИНХРОННО, ПОЭТОМУ МОЖНО УСПЕТЬ ОТПРАВИТЬ ДВЕ РАБОТЫ, ПРИ МЕДЛЕННОМ ИНТЕРНЕТЕ СЕРВА
        user = get_user(message)
        if user.waiting_for != 'work':
            log.log_user_activity(message.from_user.id, 'tried to send IMAGE but did not select the challenge')
            send_message(message, "pick_challenge")
            return

        challenge_name = user.challenge_viewer.current_challenge.name
        log.log_user_activity(message.from_user.id, f'submitted IMAGE userwork for {challenge_name}')

        image_size = 2  # 0 -> 2
        file_info = bot.get_file(message.photo[min(len(message.photo) - 1, image_size)].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        user.challenge_viewer.submit_userwork(downloaded_file, 'image')
        # I'm kinda paranoid that it can cause some problems in the future, so just keep in mind it's here
        user.waiting_for = ''

    bot.infinity_polling(logger_level=logging.INFO)
