from telebot import types
from db_data.models import UserWork


hard_userworks_to_message = []


def add_hard_userwork(userwork: UserWork):
    hard_userworks_to_message.append({
        'user_id': userwork.user_id,
        'username': userwork.user.name,
        'challenge_name': userwork.challenge.name,
        'userwork_type': userwork.type,
        'userwork_data': userwork.data,
        'prize_name': userwork.challenge.prize.name
    })


class HardUserworksMessager:
    def __init__(self, bot, admin_id):
        self.bot = bot
        self.admin_id = admin_id
        self.current_hard_userwork_id = 0
        self.message_id = None

    def reset(self):
        self.current_hard_userwork_id = 0

    def delete(self):
        if self.message_id:
            self.bot.delete_message(self.admin_id, self.message_id)
            self.message_id = None

    def send_hard_userworks(self):
        self.reset()
        hard_userwork = self.get_hard_userwork()
        if hard_userwork:
            media = self.get_media()
            if type(media) == types.InputMediaPhoto:
                self.message_id = self.bot.send_photo(hard_userwork['user_id'], media.media, media.caption,
                                                      reply_markup=self.get_markup()).message_id
            else:
                self.message_id = self.bot.send_video(hard_userwork['user_id'], media.media, media.caption,
                                                      reply_markup=self.get_markup()).message_id
            # self.message_id = self.bot.send_message(
            #     self.admin_id,
            #     f'Челлендж: {hard_userwork["challenge_name"]}\n'
            #     f'Юзер: {hard_userwork["username"]}\n'
            #     f'Приз: {hard_userwork["prize_name"]}',
            #     reply_markup=self.get_markup()
            # ).message_id
        else:
            self.message_id = self.bot.send_message(
                self.admin_id,
                'Работ нет!'
            ).message_id

    def update(self):
        hard_userwork = self.get_hard_userwork()
        try:
            if hard_userwork:
                self.bot.edit_message_media(chat_id=hard_userwork['user_id'], message_id=self.message_id,
                                            media=self.get_media(), reply_markup=self.get_markup())
            else:
                self.bot.edit_message_text(
                    chat_id=self.admin_id,
                    message_id=self.message_id,
                    text='Работ нет!',
                )
        except Exception as e:
            # print(e)
            pass

    def get_media(self):
        current_work = self.get_hard_userwork()
        if current_work['userwork_type'] == 'video':
            media = types.InputMediaVideo(current_work['userwork_data'])
        else:   # image
            media = types.InputMediaPhoto(current_work['userwork_data'])
        media.caption = self.get_text(current_work)
        return media

    def get_text(self, current_work):
        return f'Челлендж: {current_work["challenge_name"]}\n'\
               f'Юзер: {current_work["username"]}\n'\
               f'Приз: {current_work["prize_name"]}'

    def next_page(self):
        self.current_hard_userwork_id += 1
        self.update()

    def prev_page(self):
        self.current_hard_userwork_id -= 1
        self.update()

    def get_markup(self):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('←', callback_data=f'prev_page promocodes'),
                   types.InlineKeyboardButton('→', callback_data=f'next_page promocodes'))
        markup.add(
            types.InlineKeyboardButton(
                'Написать',
                url=f'tg://user?id={self.get_hard_userwork()["user_id"]}'
            ),
        )
        return markup

    def get_hard_userwork(self):
        if len(hard_userworks_to_message) == 0:
            return None
        return hard_userworks_to_message[self.current_hard_userwork_id % len(hard_userworks_to_message)]
