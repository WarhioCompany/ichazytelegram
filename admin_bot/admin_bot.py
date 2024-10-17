import telebot

from admin_bot.promocode_viewer import PromocodeViewer
from db_data.db_session import session_scope
from db_data.models import *
#from user_work_viewer import UserWorksPageViewer
import hashlib
import threading

from page_viewer.user_work_viewer import AdminUserWorksPageViewer
from commands_manager.commands import set_commands


def get_token():
    return input('Admin token: ')


def get_pass():
    with open('admin_bot/pass.secret', 'r') as file:
        return file.readline()


# id: is_authorized
admins = {}


def start_bot(admin_token, notify, admin_notify):
    bot = telebot.TeleBot(admin_token)
    admin_notify.set_bot(bot)

    def is_admin_authorized(admin_id):
        return admins.get(admin_id, {'is_authorized': False})['is_authorized']

    @bot.message_handler(commands=['start', 'help'])
    def start_command(message):
        if is_admin_authorized(message.from_user.id):
            view_userworks(message)
        else:
            bot.send_message(message.from_user.id, 'Введите пароль')
            admins[message.from_user.id] = {'is_authorized': False}

    @bot.message_handler(func=lambda message: not admins[message.from_user.id]['is_authorized'])
    def auth(message):
        password = message.text
        md5_password = hashlib.md5(password.encode())

        if md5_password.hexdigest() == get_pass():
            admins[message.from_user.id]['is_authorized'] = True
            bot.send_message(message.from_user.id, 'Авторизован')

            set_commands(message, bot, 'commands_manager/admin_commands_config.json')

            admins[message.from_user.id]['userwork_viewer'] = AdminUserWorksPageViewer(bot, message.from_user.id)
            admins[message.from_user.id]['promocodes_viewer'] = PromocodeViewer(bot, message.from_user.id)
            print(message.from_user.username, 'is authorized')

            view_userworks(message)
            admin_notify.add_admin(message.from_user.id)
        else:
            bot.send_message(message.from_user.id, 'Неверный пароль')

    @bot.message_handler(commands=['view_challenges'])
    def view_userworks(message):
        if is_admin_authorized(message.from_user.id):
            admins[message.from_user.id]['userwork_viewer'].show_works()
        else:
            bot.send_message(message.from_user.id, 'Не авторизован')

    @bot.message_handler(commands=['view_promocodes'])
    def view_promocodes(message):
        if is_admin_authorized(message.from_user.id):
            admins[message.from_user.id]['promocodes_viewer'].send_promocodes()
        else:
            bot.send_message(message.from_user.id, 'Не авторизован')

    @bot.callback_query_handler(func=lambda call: call.data == 'prev_page userworks')
    def prev_challenge_page(message):
        admins[message.from_user.id]['userwork_viewer'].prev_page()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data == 'next_page userworks')
    def next_challenge_page(message):
        admins[message.from_user.id]['userwork_viewer'].next_page()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data == 'prev_page promocodes')
    def prev_promocodes_page(message):
        admins[message.from_user.id]['promocodes_viewer'].prev_page()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data == 'next_page promocodes')
    def next_promocodes_page(message):
        admins[message.from_user.id]['promocodes_viewer'].next_page()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('approve_userwork'))
    def approve_userwork(message):
        # add coins to user, send notification, change status to approved
        admins[message.from_user.id]['userwork_viewer'].approve_userwork()
        notify.userwork_approved(admins[message.from_user.id]['userwork_viewer'].current_work)

        admins[message.from_user.id]['userwork_viewer'].next_page()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('disapprove_userwork'))
    def disapprove_userwork(message):
        # delete userwork from db or set the status to checked, send notification
        notify.userwork_disapproved(admins[message.from_user.id]['userwork_viewer'].current_work)
        admins[message.from_user.id]['userwork_viewer'].remove_userwork()

        admins[message.from_user.id]['userwork_viewer'].next_page()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('promo_confirmation'))
    def promocode_confirmation(call):
        data = call.data.split()[1]
        if data == 'approve':
            admins[call.from_user.id]['promocodes_viewer'].approve()
        elif data == 'decline':
            admins[call.from_user.id]['promocodes_viewer'].disapprove()
        # data = call.data.split()
        # if data[1] == 'approve':
        #     user_id = data[2]
        #     promocode_id = int(data[3])
        #     with session_scope() as session:
        #         user = session.query(User).filter(User.telegram_id == user_id).one()
        #         promocode = session.query(Promocode).filter(Promocode.id == promocode_id).one()
        #         user.used_promocodes.append(promocode)
        #         session.commit()
        # bot.delete_message(call.from_user.id, call.message.id)

    thread = threading.Thread(target=bot.infinity_polling)
    thread.start()