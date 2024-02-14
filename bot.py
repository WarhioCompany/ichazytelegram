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

    def send_message(message, message_id, **kwargs):
        bot.send_message(message.from_user.id, messages[message_id].format(**kwargs))

    @bot.message_handler(commands=['start', 'help'])
    def start_command(message):
        set_commands(message, bot)

        user = User(message.from_user.id)

        if not user.name:
            send_message(message, "new_user")
            send_message(message, "enter_nickname")
            user.waiting_for = 'name'
        else:
            send_message(message, "welcome_username", username=user.name)
        users[message.from_user.id] = user

    @bot.message_handler(func=lambda message: users[message.from_user.id].waiting_for == 'name')
    def new_user(message):
        users[message.from_user.id] = User(telegram_id=message.from_user.id, name=message.text)
        send_message(message, "welcome_username", username=users[message.from_user.id].name)

    @bot.message_handler(commands=['view_challenges'])
    def view_challenges(message):
        pass

    @bot.message_handler(content_types=['text'])
    def get_text_messages(message):
        pass

    bot.infinity_polling()


start_bot()