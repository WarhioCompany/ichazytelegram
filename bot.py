import logging

import telebot
from commands_manager.commands import set_commands

from messages_handler import messages
# from user import User
from userwrapper import UserData
from db_data.models import User, Promocode, UnauthorizedPromocode

from db_data import db_session
from db_data.db_session import session_scope

from notifications.notify import Notify, AdminNotify
import admin_bot.admin_bot as admin_bot

users = {}


def get_token():
    return input('Bot token: ')


def start_bot(token, admin_token):
    db_session.global_init('db/database.sqlite')
    bot = telebot.TeleBot(token)

    notify = Notify(bot)
    admin_notify = AdminNotify()

    admin_bot.start_bot(admin_token, notify, admin_notify)

    # FUNCTIONS:
    def send_message(message, message_id, markup=None, parse_mode=None, **kwargs):
        bot.send_message(
            message.from_user.id,
            messages[message_id].format(**kwargs),
            reply_markup=markup,
            parse_mode=parse_mode
        )

    def get_user(message):
        if message.from_user.id in users:
            return users[message.from_user.id]

    def send_challenge_page(message):
        viewer = get_user(message).challenge_viewer

        viewer.show_challenges()

    def greeting(message):
        with session_scope() as session:
            user = session.query(User).filter(User.telegram_id == message.from_user.id).first()
            send_message(message, "user_info", coins=user.coins)
        send_challenge_page(message)

    @bot.message_handler(func=lambda call: not get_user(call))
    def non_existent_user(message):
        start_command(message)

    # COMMANDS:
    @bot.message_handler(commands=['start', 'help'])
    def start_command(message):
        set_commands(message, bot, 'commands_manager/commands_config.json')

        user = UserData(bot, message.from_user.id)
        users[message.from_user.id] = user

        if user.user():
            send_message(message, "welcome_username", username=user.user().name)
            greeting(message)
            user.bot = bot
        else:
            send_message(message, "new_user")
            send_message(message, "enter_nickname")
            user.waiting_for = 'name'

    @bot.message_handler(commands=['view_challenges'])
    def view_challenges(message):
        send_challenge_page(message)

    @bot.message_handler(commands=['my_works'])
    def my_works(message):
        get_user(message).private_userworks_viewer.send_mode_picker()

    @bot.message_handler(commands=['balance'])
    def balance(message):
        send_message(message, "balance", coins=get_user(message).user().coins)

    @bot.message_handler(commands=['shop'])
    def shop(message):
        send_message(message, "shop")

    @bot.message_handler(commands=['partnership'])
    def collaboration(message):
        send_message(message, "partnership")

    @bot.message_handler(commands=['promocode'])
    def collaboration(message):
        get_user(message).waiting_for = 'promocode'
        send_message(message, "enter_promocode")

    @bot.message_handler(commands=['support'])
    def collaboration(message):
        send_message(message, "support")

    # CALLBACKS:
    @bot.callback_query_handler(func=lambda call: call.data == 'participate')
    def participate(call):
        error_message = get_user(call).challenge_viewer.can_submit()
        if error_message:
            bot.send_message(call.from_user.id, error_message, parse_mode='MarkdownV2', disable_web_page_preview=True)
        else:
            get_user(call).waiting_for = 'work'
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
        identifier = message.data.split()[-1]

        if identifier == 'challenges':
            get_user(message).challenge_viewer.prev_page()
            # ОБНУЛЯЕМ КНОПКУ "Участвовать"
            get_user(message).waiting_for = ''
        elif identifier == 'userworks':
            get_user(message).userworks_viewer.prev_page()
        elif identifier == 'private_userworks':
            get_user(message).private_userworks_viewer.prev_page()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('next_page'))
    def next_page(message):
        identifier = message.data.split()[-1]

        if identifier == 'challenges':
            get_user(message).challenge_viewer.next_page()
            # ОБНУЛЯЕМ КНОПКУ "Участвовать"
            get_user(message).waiting_for = ''
        elif identifier == 'userworks':
            get_user(message).userworks_viewer.next_page()
        elif identifier == 'private_userworks':
            get_user(message).private_userworks_viewer.next_page()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data == 'user_works')
    def show_user_works(message):
        user = get_user(message)
        user.userworks_viewer.show_works(user.challenge_viewer.current_challenge.id)
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('userwork_like'))
    def like_userwork(message):
        data = message.data.split()
        work_id = int(data[-1])
        identifier = data[1]
        if identifier == 'userworks':
            get_user(message).userworks_viewer.like_userwork(work_id)
        elif identifier == 'private_userworks':
            get_user(message).private_userworks_viewer.like_userwork(work_id)
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('delete_private_userwork '))
    def delete_private_userwork(message):
        work_id = int(message.data.split()[-1])

        get_user(message).private_userworks_viewer.send_delete_confirmation(work_id)
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data == 'delete_private_userwork_confirm')
    def delete_private_userwork_confirm(message):
        get_user(message).private_userworks_viewer.delete_userwork()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data == 'delete_private_userwork_decline')
    def delete_private_userwork_decline(message):
        get_user(message).private_userworks_viewer.delete_confirmation_message()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('my_works '))
    def my_works_mode(message):
        get_user(message).private_userworks_viewer.show_works('disapproved' not in message.data)
        bot.answer_callback_query(message.id)

    # User manipulation:
    @bot.message_handler(func=lambda message: get_user(message).waiting_for == 'name')
    def new_user(message):
        user = UserData(bot, message.from_user.id, message.text)
        users[message.from_user.id] = user
        # users[message.from_user.id] = User(telegram_id=message.from_user.id, name=message.text, bot=bot)
        bot.send_message(
            message.from_user.id,
            messages['registration_end'].replace('.', r'\.').replace('-', r'\-').replace('!', r'\!'),
            parse_mode='MarkdownV2'
        )
        greeting(message)

    @bot.message_handler(func=lambda message: get_user(message).waiting_for == 'promocode')
    def enter_promocode(message):
        promocode_text = message.text
        with session_scope() as session:
            promocode = session.query(Promocode).filter(Promocode.promo == promocode_text).one()
            used_promocodes = session.query(User).filter(User.telegram_id == message.from_user.id).one().used_promocodes
            if promocode in used_promocodes:
                send_message(message, 'promocode_already_used')
            elif promocode:
                send_message(message, 'promocode_correct', contact=promocode.telegram_contact)
                unauthorized_promocode = UnauthorizedPromocode(
                    user_id=message.from_user.id,
                    promocode_id=promocode.id,
                    username=message.from_user.username
                )
                if unauthorized_promocode in session.query(UnauthorizedPromocode).all():
                    return
                session.add(unauthorized_promocode)
                session.commit()
                admin_notify.user_used_promocode(message.from_user, promocode)
            else:
                send_message(message, 'promocode_incorrect')

    # USERWORK SUBMISSION
    @bot.message_handler(content_types=['video'])
    def upload_work_video(message):
        user = get_user(message)
        if user.waiting_for != 'work':
            send_message(message, "pick_challenge")
            return

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
            send_message(message, "pick_challenge")
            return

        image_size = 2  # 0 -> 2
        file_info = bot.get_file(message.photo[min(len(message.photo) - 1, image_size)].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        user.challenge_viewer.submit_userwork(downloaded_file, 'image')
        # I'm kinda paranoid that it can cause some problems in the future, so just keep in mind it's here
        user.waiting_for = ''

    bot.infinity_polling(logger_level=logging.INFO)
