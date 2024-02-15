import telebot
from telebot import types
from commands import *

from messages_handler import messages
from db_scripts import db
from user import User


users = {}


def get_token():
    with open('token.secret', 'r') as file:
        return file.readline()


def start_bot():
    bot = telebot.TeleBot(get_token())

    def send_message(message, message_id, markup=None, **kwargs):
        bot.send_message(message.from_user.id, messages[message_id].format(**kwargs), reply_markup=markup)

    def send_media(message, media):
        bot.send_media_group(message.from_user.id, media=media)

    def send_challenge_page(message, user):
        viewer = user.challenge_viewer

        challenges = viewer.get_challenges_objects()
        media = viewer.get_media_group(challenges)

        send_media(message, media)
        send_message(message, "challenge_page", markup=viewer.get_buttons(len(media)))

    def greeting(message):
        user = users[message.from_user.id]
        send_message(message, "welcome_username", username=user.name)
        send_message(message, "user_info", coins=user.coins)
        send_challenge_page(message, user)

    @bot.message_handler(commands=['start', 'help'])
    def start_command(message):
        set_commands(message, bot)

        user = User(message.from_user.id)
        users[message.from_user.id] = user

        if not user.name:
            send_message(message, "new_user")
            send_message(message, "enter_nickname")
            user.waiting_for = 'name'
        else:
            greeting(message)

    @bot.message_handler(func=lambda message: users[message.from_user.id].waiting_for == 'name')
    def new_user(message):
        users[message.from_user.id] = User(telegram_id=message.from_user.id, name=message.text)
        greeting(message)

    @bot.message_handler(commands=['view_challenges'])
    def view_challenges(message):
        pass

    @bot.message_handler(content_types=['text'])
    def get_text_messages(message):
        pass

    bot.infinity_polling()


start_bot()