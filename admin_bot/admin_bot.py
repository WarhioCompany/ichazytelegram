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

    def add_coins_to_user(telegram_id, coins_amount):
        with session_scope() as session:
            user = session.query(User).filter(User.telegram_id == telegram_id).one()
            user.coins += coins_amount
            session.commit()

    def clear_admin_buf(message):
        admins[message.from_user.id]['buf'] = {}
        admins[message.from_user.id]['waiting_for'] = ''

    @bot.message_handler(commands=['start', 'help'])
    def start_command(message):
        if is_admin_authorized(message.from_user.id):
            view_userworks(message)
        else:
            bot.send_message(message.from_user.id, 'Введите пароль')
            admins[message.from_user.id] = {'is_authorized': False, 'waiting_for': '', 'buf': {}}

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

    @bot.message_handler(commands=['add_currency_by_tg'])
    def add_currency_by_tg(message):
        bot.send_message(message.from_user.id, "Введите ник в телеграме или телефон, если ника нет")
        admins[message.from_user.id]['waiting_for'] = 'telegram_username'

    @bot.message_handler(commands=['add_currency_by_bot'])
    def add_currency_by_bot(message):
        bot.send_message(message.from_user.id, "Введите ник в боте")
        admins[message.from_user.id]['waiting_for'] = 'bot_username'

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

    @bot.message_handler(commands=['link_friend'])
    def link_friend(message):
        clear_admin_buf(message)

        bot.send_message(message.from_user.id, "Кто пригласил? (ник в боте)")
        admins[message.from_user.id]['waiting_for'] = 'link_friend_first_username'

    # CALL DATA
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

        userwork = admins[message.from_user.id]['userwork_viewer'].current_work
        notify.userwork_approved(userwork)

        # TODO: add coins to user who this one was invited by
        with session_scope() as session:
            invited_by = session.query(User).filter(User.telegram_id == userwork.user_id).one().invited_by

            if invited_by:
                amount = 50
                add_coins_to_user(invited_by, amount)
                notify.balance_update(invited_by, "referral_coins", amount)

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

    # WAIT FOR
    @bot.message_handler(func=lambda message: admins[message.from_user.id]['waiting_for'] == 'telegram_username')
    def get_telegram_username(message):
        with session_scope() as session:
            user = session.query(User).filter(User.telegram_username == message.text).all()
            if len(user) == 0:
                bot.send_message(message.from_user.id, f"Юзер с ником {message.text} не найден")
            else:
                user = user[0]
                bot.send_message(message.from_user.id, f"Ник в боте {user.name}\nБаланс {user.coins}\nTG: {user.telegram_username}")
                bot.send_message(message.from_user.id, "Сколько монет добавить (отрицательное, если убавить)")

                admins[message.from_user.id]['buf']['telegram_id'] = user.telegram_id
                admins[message.from_user.id]['waiting_for'] = 'new_balance'

    @bot.message_handler(func=lambda message: admins[message.from_user.id]['waiting_for'] == 'bot_username')
    def get_bot_username(message):
        with session_scope() as session:
            user = session.query(User).filter(User.name == message.text).all()
            if len(user) == 0:
                bot.send_message(message.from_user.id, f"Юзер с ником {message.text} не найден")
            else:
                user = user[0]
                bot.send_message(message.from_user.id, f"Ник в боте {user.name}\nБаланс {user.coins}\nTG: {user.telegram_username}")
                bot.send_message(message.from_user.id, "Сколько монет добавить (отрицательное, если убавить)")

                admins[message.from_user.id]['buf']['telegram_id'] = user.telegram_id
                admins[message.from_user.id]['waiting_for'] = 'new_balance'

    @bot.message_handler(func=lambda message: admins[message.from_user.id]['waiting_for'] == 'new_balance')
    def update_user_balance(message):
        if not message.text.replace('-', '', 1).isdigit():
            bot.send_message(message.from_user.id, 'Некорректный ввод')

        telegram_id = admins[message.from_user.id]['buf']['telegram_id']
        amount = int(message.text)

        add_coins_to_user(telegram_id, amount)
        notify.balance_update(telegram_id, ("added_coins" if int(message.text) > 0 else "discard_coins"), amount)

        with session_scope() as session:
            coins = session.query(User).filter(User.telegram_id == telegram_id).one().coins
            bot.send_message(message.from_user.id, f"Новый баланс {coins}")

        clear_admin_buf(message)

    @bot.message_handler(func=lambda message: admins[message.from_user.id]['waiting_for'] == 'link_friend_first_username')
    def link_friend_first_username(message):
        with session_scope() as session:
            user = session.query(User).filter(User.name == message.text).all()
            if len(user) == 0:
                bot.send_message(message.from_user.id, f"Юзер под ником '{message.text}' не найден\nПопробуйте еще раз")
                return

            user = user[0]
            bot.send_message(message.from_user.id, f"Ник в боте {user.name}\nБаланс {user.coins}\nTG: {user.telegram_username}")

            admins[message.from_user.id]['buf']['link_friend_id1'] = user.telegram_id
        bot.send_message(message.from_user.id, "Кого пригласил? (ник в боте)")
        admins[message.from_user.id]['waiting_for'] = 'link_friend_second_username'

    @bot.message_handler(func=lambda message: admins[message.from_user.id]['waiting_for'] == 'link_friend_second_username')
    def link_friend_second_username(message):
        with session_scope() as session:
            user = session.query(User).filter(User.name == message.text).all()
            if len(user) == 0:
                bot.send_message(message.from_user.id, f"Юзер под ником '{message.text}' не найден\nПопробуйте еще раз")
                return

            user = user[0]
            bot.send_message(message.from_user.id, f"Ник в боте {user.name}\nБаланс {user.coins}\nTG: {user.telegram_username}")

            invited_by = admins[message.from_user.id]['buf']['link_friend_id1']

            bot.send_message(message.from_user.id, f"{user.telegram_id} теперь привязан к {invited_by}")
            user.invited_by = invited_by
            session.commit()

    thread = threading.Thread(target=bot.infinity_polling)
    thread.start()