import telebot
from db_data.db_session import session_scope
from db_data.models import *
#from user_work_viewer import UserWorksPageViewer
import hashlib
import threading

from page_viewer.user_work_viewer import AdminUserWorksPageViewer


def get_token():
    with open('admin_bot/token.secret', 'r') as file:
        return file.readline()


def get_pass():
    with open('admin_bot/pass.secret', 'r') as file:
        return file.readline()


# id: is_authorized
admins = {}


def start_bot(notify):
    bot = telebot.TeleBot(get_token())

    @bot.message_handler(commands=['start', 'help'])
    def start_command(message):
        bot.send_message(message.from_user.id, 'Введите пароль')
        admins[message.from_user.id] = {'is_authorized': False}
        # admins[message.from_user.id]['userwork_viewer'] = AdminUserWorksPageViewer(bot, message.from_user.id)
        # admins[message.from_user.id]['userwork_viewer'].show_works()

    @bot.message_handler(func=lambda message: not admins[message.from_user.id]['is_authorized'])
    def auth(message):
        password = message.text
        md5_password = hashlib.md5(password.encode())

        if md5_password.hexdigest() == get_pass():
            admins[message.from_user.id]['is_authorized'] = True
            bot.send_message(message.from_user.id, 'Авторизован')
            admins[message.from_user.id]['userwork_viewer'] = AdminUserWorksPageViewer(bot, message.from_user.id)
            print(message.from_user.username, 'is authorized')
            view_userworks(message)
        else:
            bot.send_message(message.from_user.id, 'Неверный пароль')

    @bot.message_handler(commands=['view_challenges'])
    def view_userworks(message):
        admins[message.from_user.id]['userwork_viewer'].show_works()

    @bot.callback_query_handler(func=lambda call: call.data == 'prev_page userworks')
    def prev_challenge_page(message):
        admins[message.from_user.id]['userwork_viewer'].prev_page()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data == 'next_page userworks')
    def next_challenge_page(message):
        admins[message.from_user.id]['userwork_viewer'].next_page()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('approve_userwork'))
    def approve_userwork(message):
        # add coins to user, send notification, change status to approved
        admins[message.from_user.id]['userwork_viewer'].approve_userwork()
        notify.userwork_approved(admins[message.from_user.id]['userwork_viewer'].current_works[0])

        admins[message.from_user.id]['userwork_viewer'].next_page()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('disapprove_userwork'))
    def disapprove_userwork(message):
        # delete userwork from db or set the status to checked, send notification
        notify.userwork_disapproved(admins[message.from_user.id]['userwork_viewer'].current_works[0])
        admins[message.from_user.id]['userwork_viewer'].remove_userwork()

        admins[message.from_user.id]['userwork_viewer'].next_page()
        bot.answer_callback_query(message.id)

    thread = threading.Thread(target=bot.infinity_polling)
    thread.start()