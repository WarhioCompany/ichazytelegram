import telebot
from telebot import types
from commands import *

from messages_handler import messages
from db_scripts import db
from user import User
from user_work import UserWork

users = {}


def get_token():
    with open('token.secret', 'r') as file:
        return file.readline()


def start_bot():
    bot = telebot.TeleBot(get_token())

    def send_message(message, message_id, markup=None, **kwargs):
        bot.send_message(message.from_user.id, messages[message_id].format(**kwargs), reply_markup=markup)

    def get_user(message):
        if message.from_user.id in users:
            return users[message.from_user.id]

    def send_challenge_page(message):
        viewer = get_user(message).challenge_viewer

        viewer.show_challenges()

    def greeting(message):
        user = get_user(message)
        send_message(message, "welcome_username", username=user.name)
        send_message(message, "user_info", coins=user.coins) 
        send_challenge_page(message)

    @bot.callback_query_handler(func=lambda call: call.data == 'participate')
    def participate(call):
        challenge_id = get_user(call).challenge_viewer.challenge_card.current_challenge.id
        get_user(call).waiting_for = 'work'
        send_message(call, "user_participation")

    @bot.callback_query_handler(func=lambda call: call.data.startswith('challenge_card'))
    def picking_challenge(call):
        # call: 'challenge_card {id}'
        challenge_viewer = get_user(call).challenge_viewer
        challenge_id = int(call.data.split()[1])

        bot.answer_callback_query(call.id)
        challenge_viewer.send_challenge(challenge_id)

    @bot.callback_query_handler(func=lambda call: call.data == 'prev_page_challenges')
    def prev_challenge_page(message):
        get_user(message).challenge_viewer.prev_page()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data == 'next_page_challenges')
    def next_challenge_page(message):
        get_user(message).challenge_viewer.next_page()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data == 'prev_page_userworks')
    def prev_challenge_page(message):
        get_user(message).user_works_viewer.prev_page()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data == 'next_page_userworks')
    def next_challenge_page(message):
        get_user(message).user_works_viewer.next_page()
        bot.answer_callback_query(message.id)

    @bot.callback_query_handler(func=lambda call: call.data == 'user_works')
    def show_user_works(message):
        bot.answer_callback_query(message.id)
        user = get_user(message)
        user.user_works_viewer.show_works(user.challenge_viewer.challenge_card.current_challenge.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('userwork_like'))
    def like_userwork(message):
        print('like', message.data.split()[-1])
        work_id = int(message.data.split()[-1])
        get_user(message).user_works_viewer.like_userwork(work_id)


    @bot.message_handler(commands=['start', 'help'])
    def start_command(message):
        set_commands(message, bot)

        user = User(telegram_id=message.from_user.id, bot=bot)
        users[message.from_user.id] = user

        if not user.name:
            send_message(message, "new_user")
            send_message(message, "enter_nickname")
            user.waiting_for = 'name'
        else:
            greeting(message)

    @bot.message_handler(func=lambda message: get_user(message).waiting_for == 'name')
    def new_user(message):
        users[message.from_user.id] = User(telegram_id=message.from_user.id, name=message.text, bot=bot)
        greeting(message)

    @bot.message_handler(content_types=['video']) 
    def upload_work_video(message):
        if get_user(message).waiting_for != 'work':
            print('зачем мне это')
            return

        file_info = bot.get_file(message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        upload_work(message, downloaded_file, 'video')

    @bot.message_handler(content_types=['photo'])
    def upload_work_photo(message):
        if get_user(message).waiting_for != 'work':
            print('зачем мне это')
            return

        image_size = 2  # 0 -> 2
        file_info = bot.get_file(message.photo[image_size].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        upload_work(message, downloaded_file, 'image')

    def upload_work(message, downloaded_file, type):
        user = get_user(message)
        work = UserWork(
            user_id=user.id,
            challenge_id=user.challenge_viewer.challenge_card.current_challenge.id,
            data=downloaded_file,
            type=type
        )
        send_message(message, "user_send_work")
        work.add_to_db()
        # I'm kinda paranoid that it can cause some problems in the future, so just keep in mind it's here
        user.waiting_for = ''

    @bot.message_handler(commands=['view_challenges'])
    def view_challenges(message):
        send_challenge_page(message)

    @bot.message_handler(content_types=['text'])
    def get_text_messages(message):
        pass

    bot.infinity_polling()


start_bot()