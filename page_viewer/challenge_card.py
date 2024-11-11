import io
from io import BytesIO
from telebot import types
from messages_handler import messages
from datetime import datetime


class ChallengeCard:
    def __init__(self, bot, user_id):
        self.current_challenge = None
        self.bot = bot
        self.user_id = user_id
        self.message_id = None

    def send(self, challenge):
        self.current_challenge = challenge
        f = BytesIO(self.current_challenge.image)
        self.message_id = self.bot.send_photo(self.user_id,
                                              photo=f,
                                              caption=self.get_text(),
                                              reply_markup=self.get_buttons()).message_id
        #media = self.get_media()
        #self.message_id = self.bot.send_media_group(self.user_id, media=[media])[0].message_id

    def edit(self, challenge):
        if self.current_challenge == challenge:
            print('Current challenge is identical to the previous one')
        self.current_challenge = challenge
        media = self.get_media()
        self.bot.edit_message_media(chat_id=self.user_id, message_id=self.message_id, media=media,
                                    reply_markup=self.get_buttons())

    def show_info(self, challenge):
        if self.message_id:
            self.edit(challenge)
        else:
            self.send(challenge)

    def delete(self):
        if not self.message_id:
            return
        self.bot.delete_message(self.user_id, self.message_id)
        self.message_id = None

    def get_text(self):
        return messages['challenge_card'].format(
            name=self.current_challenge.name,
            desc=self.current_challenge.description,
            price=self.current_challenge.price,
            coins=self.current_challenge.coins_prize,
            date_to=datetime.strftime(self.current_challenge.date_to, '%d/%m/%y')
        )

    def get_media(self):
        media = types.InputMediaPhoto(self.current_challenge.image)
        media.caption = self.get_text()
        return media

    def get_buttons(self):
        markup = types.InlineKeyboardMarkup()

        markup.add(types.InlineKeyboardButton('Посмотреть работы', callback_data='user_works'),
                   types.InlineKeyboardButton('Участвовать', callback_data=f'participate'))
        return markup

