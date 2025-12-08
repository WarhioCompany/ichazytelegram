import logging
import signal
import time

import telebot
from telebot import apihelper
from telebot import types

from admin_bot import prize_barrier_checker
from admin_bot.admin_model import Admin
from admin_bot.challenge_adder import ChallengeAdder
from admin_bot.db_manager import DBManager
from admin_bot.promocode_viewer import ModeratorPromocodeViewer
from db_data.db_session import session_scope
from db_data.models import *
#from user_work_viewer import UserWorksPageViewer
import hashlib
import threading

from page_viewer.user_work_viewer import AdminUserWorksPageViewer
from commands_manager.commands import set_commands
from user_sub_checker import UserSubChecker

from exception_handler import ExceptionHandler
import event_handler

import admin_bot.prize_barrier_checker
import db_to_xlsx

def get_token():
    return input('Admin token: ')


def get_pass():
    with open('admin_bot/pass.secret', 'r') as file:
        return file.readline()


# id: is_authorized
admins = {}
sub_checker = None
logger = logging.getLogger(__name__)


def start_bot(admin_token, notify, admin_notify):
    global sub_checker
    bot = telebot.TeleBot(admin_token, exception_handler=ExceptionHandler())
    admin_notify.set_bot(bot)
    admin_notify.start_notifying()

    db_manager = DBManager()

    def user_subbed(user_id):
        with session_scope() as session:
            invited_by = session.query(User).filter(User.telegram_id == user_id).one().invited_by
        add_coins_to_user(invited_by, 1000)
        notify.balance_update(invited_by, 'referral_coins', 1000)
        logger.info(f'user {user_id} subbed to the channel, {invited_by} gets 1000')

    sub_checker = UserSubChecker(bot, user_subbed_func=user_subbed, seconds_delay=event_handler.day())
    prize_barrier_checker.start(admin_notify)

    def is_admin_authorized(admin_id):
        return admin_id in admins and admins[admin_id].is_authorized

    def add_coins_to_user(telegram_id, coins_amount):
        with session_scope() as session:
            user = session.query(User).filter(User.telegram_id == telegram_id).one()
            user.coins += coins_amount
            session.commit()

    def clear_admin_buf(message):
        admins[message.from_user.id].buf = {}
        admins[message.from_user.id].waiting_for = ''

    @bot.message_handler(commands=['start', 'help'])
    def start_command(message):
        if is_admin_authorized(message.from_user.id):
            view_userworks(message)
        else:
            bot.send_message(message.from_user.id, 'Введите пароль')
            admins[message.from_user.id] = Admin(message.from_user.id, bot, notify)

    @bot.callback_query_handler(func=lambda call: call.from_user.id not in admins)
    def non_existent_user(call):
        bot.send_message(call.from_user.id, "Запустите бота -> /start")
        bot.answer_callback_query(call.id)

    @bot.message_handler(func=lambda message: message.from_user.id not in admins)
    def non_existent_user(message):
        bot.send_message(message.from_user.id, "Запустите бота -> /start")

    @bot.message_handler(func=lambda message: not admins[message.from_user.id].is_authorized)
    def auth(message):
        password = message.text
        md5_password = hashlib.md5(password.encode())

        if md5_password.hexdigest() == get_pass():
            admins[message.from_user.id].is_authorized = True
            bot.send_message(message.from_user.id, 'Авторизован')
            
            set_commands(message, bot, 'commands_manager/admin_commands_config.json')
            
            logger.info(f'{message.from_user.username} is authorized')

            view_userworks(message)
            admin_notify.add_admin(message.from_user.id)
        else:
            bot.send_message(message.from_user.id, 'Неверный пароль')

    @bot.message_handler(commands=['add_currency_by_tg'])
    def add_currency_by_tg(message):
        bot.send_message(message.from_user.id, "Введите ник в телеграме или телефон, если ника нет")
        admins[message.from_user.id].waiting_for = 'telegram_username'

    @bot.message_handler(commands=['add_currency_by_bot'])
    def add_currency_by_bot(message):
        bot.send_message(message.from_user.id, "Введите ник в боте")
        admins[message.from_user.id].waiting_for = 'bot_username'

    @bot.message_handler(commands=['add_currency_by_name'])
    def add_currency_by_name(message):
        bot.send_message(message.from_user.id, "Введите имя в тг")
        admins[message.from_user.id].waiting_for = 'telegram_name'

    @bot.message_handler(commands=['add_currency_to_all'])
    def add_currency_to_all(message):
        bot.send_message(message.from_user.id, 'Введите количество монет')
        admins[message.from_user.id].waiting_for = 'add_coins_amount'

    @bot.message_handler(commands=['view_userworks'])
    def view_userworks(message):
        if is_admin_authorized(message.from_user.id):
            admins[message.from_user.id].userwork_viewer.show_works()
        else:
            bot.send_message(message.from_user.id, 'Не авторизован')

    @bot.message_handler(commands=['view_promocodes'])
    def view_promocodes(message):
        if is_admin_authorized(message.from_user.id):
            admins[message.from_user.id].coins_promocode_viewer.send_page()
        else:
            bot.send_message(message.from_user.id, 'Не авторизован')

    @bot.message_handler(commands=['view_boost_promocodes'])
    def view_boost_promocodes(message):
        if is_admin_authorized(message.from_user.id):
            admins[message.from_user.id].boost_promocode_viewer.send_page()
        else:
            bot.send_message(message.from_user.id, 'Не авторизован')

    @bot.message_handler(commands=['view_prizes'])
    def view_prizes(message):
        if is_admin_authorized(message.from_user.id):
            admins[message.from_user.id].prize_viewer.send_page()
        else:
            bot.send_message(message.from_user.id, 'Не авторизован')


    @bot.message_handler(commands=['moderate_promocodes'])
    def moderate_promocodes(message):
        if is_admin_authorized(message.from_user.id):
            admins[message.from_user.id].moderator_promocode_viewer.send_promocodes()
        else:
            bot.send_message(message.from_user.id, 'Не авторизован')

    @bot.message_handler(commands=['view_challenges'])
    def view_challenges(message):
        admins[message.from_user.id].challenge_viewer.show_challenges()

    @bot.message_handler(commands=['link_friend'])
    def link_friend(message):
        clear_admin_buf(message)

        bot.send_message(message.from_user.id, "Кто пригласил? (ник в боте)")
        admins[message.from_user.id].waiting_for = 'link_friend_first_username'

    @bot.message_handler(commands=['get_user'])
    def get_user(message):
        pass

    @bot.message_handler(commands=['get_db'])
    def get_db(message):
        bot.send_document(message.from_user.id, db_to_xlsx.convert_to_xlsx())

    @bot.message_handler(commands=['remove_challenge'])
    def remove_challenge(message):
        def remove(answer):
            with session_scope() as session:
                challenge = session.query(Challenge).filter(Challenge.name == answer[0]).all()
                if not challenge:
                    bot.send_message(message.from_user.id, f'Челлендж с именем "{answer[0]}" не найден')
                else:
                    db_manager.remove_element(Challenge, challenge[0].id)
                    bot.send_message(message.from_user.id, 'Челлендж удален')
        bot.send_message(message.from_user.id, 'ЭТО УДАЛИТ ЧЕЛЛЕНДЖ И ВСЕ РАБОТЫ, СВЯЗАННЫЕ С НИМ. ДЛЯ ОТМЕНЫ ОПЕРАЦИИ ВВЕДИТЕ БРЕД.')
        admins[message.from_user.id].chainer.chain(['Введите название челленджа (#лень)'], [remove])

    @bot.message_handler(commands=['remove_userwork'])
    def remove_userwork(message):
        admins[message.from_user.id].chainer.chain(['Пришлите id работы'], [lambda ans: bot.send_message(message.from_user.id, f'Работа юзера с id {ans[0]} удалена') if db_manager.remove_element(UserWork, int(ans[0])) else bot.send_message(message.from_user.id, 'Работа не найдена')])

    @bot.message_handler(commands=['disapprove_userwork'])
    def disapprove_userwork(message):
        def __disapprove_userwork(answer):
            userwork_id = int(answer[0])
            with session_scope() as session:
                u = session.query(UserWork).filter(UserWork.id == userwork_id).all()
                if len(u) == 0:
                    bot.send_message(message.from_user.id, 'Работа не найдена')
                else:
                    u[0].status = 'disapproved'
                    bot.send_message(message.from_user.id, 'Работа дизапрувнута')
                    session.commit()

        admins[message.from_user.id].chainer.chain(['Пришлите id работы'], [__disapprove_userwork])

    @bot.message_handler(commands=['send_message_to_all'])
    def send_message_to_all(message):
        def __send_message(data):
            msg = data[0]
            with session_scope() as session:
                users = session.query(User).all()
                for user in users:
                    notify.send_message(user.telegram_id, msg)
            bot.send_message(message.from_user.id, 'Сообщение отправлено')
        admins[message.from_user.id].chainer.chain(['Введите сообщение, которое увидят все пользователи'], [__send_message])


    # CALL DATA
    @bot.callback_query_handler(func=lambda call: call.data == 'prev_page userworks')
    def prev_challenge_page(message):
        admins[message.from_user.id].userwork_viewer.prev_page()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data == 'next_page userworks')
    def next_challenge_page(message):
        admins[message.from_user.id].userwork_viewer.next_page()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data == 'prev_page promocodes')
    def prev_promocodes_page(message):
        admins[message.from_user.id].moderator_promocode_viewer.prev_page()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data == 'next_page promocodes')
    def next_promocodes_page(message):
        admins[message.from_user.id].moderator_promocode_viewer.next_page()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data == 'approve_button')
    def approve_button(message):
        admins[message.from_user.id].userwork_viewer.approve_button()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data == 'disapprove_button')
    def disapprove_button(message):
        # markup = types.InlineKeyboardMarkup()
        #
        # for option_id in range(len(disapprove_options)):
        #     markup.add(types.InlineKeyboardButton(
        #         disapprove_options[option_id],
        #         callback_data=f'disapprove_option {option_id}'
        #     ))
        #
        # bot.send_message(message.from_user.id, 'Выберите опцию дизапрува:', reply_markup=markup)

        admins[message.from_user.id].userwork_viewer.disapprove_button()

        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('admin_userwork_sure'))
    def admin_userworks_page_confirmation(message):
        confirmed = message.data.split()[1] == '1'
        if confirmed:
            admins[message.from_user.id].userwork_viewer.sure_button()
        else:
            admins[message.from_user.id].userwork_viewer.cancel_button()

    @bot.callback_query_handler(func=lambda call: call.data.startswith('disapprove_option'))
    def disapprove_option(call):
        option_id = int(call.data.split()[1])
        admins[call.from_user.id].userwork_viewer.disapprove_userwork(option_id)

        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('promo_confirmation'))
    def promocode_confirmation(call):
        data = call.data.split()[1]
        if data == 'approve':
            admins[call.from_user.id].moderator_promocode_viewer.approve()
        elif data == 'decline':
            admins[call.from_user.id].moderator_promocode_viewer.disapprove()
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

    @bot.callback_query_handler(func=lambda call: call.data.startswith('next_page challenges'))
    def challenge_next_page(call):
        admins[call.from_user.id].challenge_viewer.next_page()
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('prev_page challenges'))
    def challenge_prev_page(call):
        admins[call.from_user.id].challenge_viewer.prev_page()
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('challenge_edit'))
    def challenge_edit(call):
        admins[call.from_user.id].challenge_viewer.handle_edit_challenge_callback(call)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('challenge_create'))
    def challenge_create(call):
        admins[call.from_user.id].challenge_viewer.handle_create_challenge_callback(call)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('model_editor'))
    def model_editor(call):
        match call.data.split()[1]:
            case 'promocode_viewer':
                admins[call.from_user.id].coins_promocode_viewer.handle_callback(call)
            case 'boost_promocode_viewer':
                admins[call.from_user.id].boost_promocode_viewer.handle_callback(call)
            case 'prize_viewer':
                admins[call.from_user.id].prize_viewer.handle_callback(call)
        bot.answer_callback_query(call.id)

    # WAIT FOR
    @bot.message_handler(func=lambda message: admins[message.from_user.id].waiting_for == 'chainer', content_types=['photo', 'video','text'])
    def chainer_message_handler(message):
        admins[message.from_user.id].chainer.message_handler(message)

    @bot.message_handler(func=lambda message: admins[message.from_user.id].waiting_for == 'challenge_to_remove')
    def remove_challenge(message):
        challenge_name = message.text
        with session_scope() as session:
            challenge = session.query(Challenge).filter(Challenge.name == challenge_name).all()
            if not challenge:
                bot.send_message(message.from_user.id, f'Челлендж с именем "{challenge_name}" не найден')
            else:
                session.delete(challenge[0])
                bot.send_message(message.from_user.id, 'Челлендж удален')
                session.commit()

    @bot.message_handler(func=lambda message: admins[message.from_user.id].waiting_for == 'challenge preview', content_types=['photo', 'video'])
    def get_challenge_preview(message):
        adder = ChallengeAdder(admins[message.from_user.id])

        file_info = bot.get_file(message.photo[-1].file_id if message.photo else message.video.file_id)
        file = bot.download_file(file_info.file_path)

        adder.pass_media(*([file, None] if message.photo else [None, file]))
        adder.challenge_survey()

    @bot.message_handler(func=lambda message: admins[message.from_user.id].waiting_for == 'telegram_username')
    def get_telegram_username(message):
        with session_scope() as session:
            user = session.query(User).filter(User.telegram_username == message.text).all()
            if len(user) == 0:
                bot.send_message(message.from_user.id, f"Юзер с ником {message.text} не найден")
            else:
                user = user[0]
                bot.send_message(message.from_user.id, f"Ник в боте {user.name}\nБаланс {user.coins}\nTG: {user.telegram_username}")
                bot.send_message(message.from_user.id, "Сколько монет добавить (отрицательное, если убавить)")

                admins[message.from_user.id].buf['telegram_id'] = user.telegram_id
                admins[message.from_user.id].waiting_for = 'new_balance'

    @bot.message_handler(func=lambda message: admins[message.from_user.id].waiting_for == 'telegram_name')
    def get_telegram_name(message):
        with session_scope() as session:
            user = session.query(User).filter(User.telegram_name == message.text).all()
            if len(user) == 0:
                bot.send_message(message.from_user.id, f"Юзер с ником {message.text} не найден")
            else:
                user = user[0]
                bot.send_message(message.from_user.id,
                                 f"Ник в боте {user.name}\nБаланс {user.coins}\nTG: {user.telegram_username}")
                bot.send_message(message.from_user.id, "Сколько монет добавить (отрицательное, если убавить)")

                admins[message.from_user.id].buf['telegram_id'] = user.telegram_id
                admins[message.from_user.id].waiting_for = 'new_balance'

    @bot.message_handler(func=lambda message: admins[message.from_user.id].waiting_for == 'bot_username')
    def get_bot_username(message):
        with session_scope() as session:
            user = session.query(User).filter(User.name == message.text).all()
            if len(user) == 0:
                bot.send_message(message.from_user.id, f"Юзер с ником {message.text} не найден")
            else:
                user = user[0]
                bot.send_message(message.from_user.id, f"Ник в боте {user.name}\nБаланс {user.coins}\nTG: {user.telegram_username}")
                bot.send_message(message.from_user.id, "Сколько монет добавить (отрицательное, если убавить)")

                admins[message.from_user.id].buf['telegram_id'] = user.telegram_id
                admins[message.from_user.id].waiting_for = 'new_balance'

    @bot.message_handler(func=lambda message: admins[message.from_user.id].waiting_for == 'new_balance')
    def update_user_balance(message):
        if not message.text.replace('-', '', 1).isdigit():
            bot.send_message(message.from_user.id, 'Некорректный ввод')
            return

        telegram_id = admins[message.from_user.id].buf['telegram_id']
        amount = int(message.text)

        add_coins_to_user(telegram_id, amount)
        notify.balance_update(telegram_id, ("added_coins" if int(message.text) > 0 else "discard_coins"), amount)

        with session_scope() as session:
            coins = session.query(User).filter(User.telegram_id == telegram_id).one().coins
            bot.send_message(message.from_user.id, f"Новый баланс {coins}")

        clear_admin_buf(message)

    @bot.message_handler(func=lambda message: admins[message.from_user.id].waiting_for == 'link_friend_first_username')
    def link_friend_first_username(message):
        with session_scope() as session:
            user = session.query(User).filter(User.name == message.text).all()
            if len(user) == 0:
                bot.send_message(message.from_user.id, f"Юзер под ником '{message.text}' не найден\nПопробуйте еще раз")
                return

            user = user[0]
            bot.send_message(message.from_user.id, f"Ник в боте {user.name}\nБаланс {user.coins}\nTG: {user.telegram_username}")

            admins[message.from_user.id].buf['link_friend_id1'] = user.telegram_id
        bot.send_message(message.from_user.id, "Кого пригласил? (ник в боте)")
        admins[message.from_user.id].waiting_for = 'link_friend_second_username'

    @bot.message_handler(func=lambda message: admins[message.from_user.id].waiting_for == 'link_friend_second_username')
    def link_friend_second_username(message):
        with session_scope() as session:
            user = session.query(User).filter(User.name == message.text).all()
            if len(user) == 0:
                bot.send_message(message.from_user.id, f"Юзер под ником '{message.text}' не найден\nПопробуйте еще раз")
                return

            user = user[0]
            bot.send_message(message.from_user.id, f"Ник в боте {user.name}\nБаланс {user.coins}\nTG: {user.telegram_username}")

            invited_by = admins[message.from_user.id].buf['link_friend_id1']

            bot.send_message(message.from_user.id, f"{user.telegram_id} теперь привязан к {invited_by}")
            user.invited_by = invited_by
            session.commit()

    @bot.message_handler(func=lambda message: admins[message.from_user.id].waiting_for == 'add_coins_amount')
    def add_coins_to_all_amount(message):
        if not message.text.replace('-', '', 1).isdigit():
            bot.send_message(message.from_user.id, 'Некорректный ввод')
            return

        admins[message.from_user.id].buf['coins_amount'] = int(message.text)
        admins[message.from_user.id].waiting_for = 'add_coins_condition'

        bot.send_message(message.from_user.id, 'Введите условие добавления монет (">100" больше 100, "<24" меньше 24')

    @bot.message_handler(func=lambda message: admins[message.from_user.id].waiting_for == 'add_coins_condition')
    def add_coins_to_all_condition(message):
        condition = message.text[0]
        amount = int(message.text[1:])
        coins_amount = admins[message.from_user.id].buf['coins_amount']
        with session_scope() as session:
            if condition == '>':
                users = session.query(User).filter(User.coins > amount).all()
            else:
                users = session.query(User).filter(User.coins < amount).all()
            for user in users:
                user.coins += coins_amount
                notify.balance_update(user.telegram_id, ("added_coins" if coins_amount > 0 else "discard_coins"), coins_amount)

            bot.send_message(message.from_user.id, f'Добавлено {coins_amount} монет {len(users)} юзерам')
            session.commit()
        clear_admin_buf(message)

    thread = threading.Thread(target=bot.infinity_polling)
    thread.start()