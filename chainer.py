from telebot import types

from tools import media_downloader


class Chainer:
    def __init__(self, bot, user_id, user_obj):
        self.bot = bot
        self.user_id = user_id
        self.user_obj = user_obj

        self.questions_queue = []
        self.answers = []

        self.messages_id = []

        self.end_actions = None

    def chain(self, questions, end_actions):
        self.answers = []
        self.messages_id = []

        self.user_obj.waiting_for = 'chainer'
        self.questions_queue = questions
        self.end_actions = end_actions
        self.send_next_question()

    def send_next_question(self):
        if self.questions_queue:
            self.messages_id.append(self.bot.send_message(self.user_id, self.questions_queue.pop(0)).message_id)
        else:
            self.user_obj.waiting_for = ''
            self.call_actions()


    def message_handler(self, message):
        if message.photo:
            answer = types.InputMediaPhoto(media_downloader.download_photo(self.bot, message))
        elif message.video:
            answer = types.InputMediaVideo(media_downloader.download_video(self.bot, message))
        elif message.text:
            answer = message.text
        else:
            # not text, image or video
            # waiting for another message
            return

        self.answers.append(answer)
        self.messages_id.append(message.message_id)

        self.send_next_question()

    def call_actions(self):
        for action in self.end_actions:
            action(self.answers)

    def clear_chain(self):
        for message_id in self.messages_id:
            self.bot.delete_message(self.user_id, message_id)
        self.messages_id.clear()