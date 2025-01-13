from telebot import types, apihelper


class PageViewer:
    def __init__(self, bot, user_id, page_type, parse_mode=None):
        self.current_page = 0
        self.media_id = None
        # self.picker_id = None

        self.bot = bot
        self.user_id = user_id
        self.page_type = page_type

        self.parse_mode = parse_mode

    def reset(self):
        self.current_page = 0
        self.delete()

    def send_page(self, media, button_rows):
        if type(media) == types.InputMediaPhoto:
            self.media_id = self.bot.send_photo(self.user_id, media.media, self.escape(media.caption),
                                                reply_markup=self.get_markup(button_rows),
                                                parse_mode=self.parse_mode).message_id
        else:
            self.media_id = self.bot.send_video(self.user_id, media.media, caption=self.escape(media.caption),
                                                reply_markup=self.get_markup(button_rows),
                                                parse_mode=self.parse_mode).message_id

    def escape(self, caption):
        if self.parse_mode:
            return caption.translate(str.maketrans({"!":  r"\!",
                                                    "^":  r"\^",
                                                    "#":  r"\#",
                                                    ".":  r"\.",
                                                    "-":  r"\-",
                                                    "(": r"\(",
                                                    ")": r"\)",
                                                    "[": r'\[',
                                                    "]": r'\]'})).replace(r'\\', '')
        else:
            return caption

    def send_message(self, message):
        self.media_id = self.bot.send_message(self.user_id, message).message_id

    def update_page(self, media, button_rows):
        try:
            self.bot.edit_message_media(chat_id=self.user_id, message_id=self.media_id, media=media,
                                        reply_markup=self.get_markup(button_rows))
            if self.parse_mode:
                self.bot.edit_message_caption(chat_id=self.user_id, message_id=self.media_id,
                                              caption=self.escape(media.caption), parse_mode=self.parse_mode,
                                              reply_markup=self.get_markup(button_rows))
        except Exception as e:
            # print(e)
            pass

    def delete(self):
        if self.media_id:
            self.delete_message_if_exists()
            self.media_id = None

    def delete_message_if_exists(self):
        try:
            self.bot.delete_message(self.user_id, self.media_id)
        except apihelper.ApiTelegramException as e:
            #self.bot.edit_message_caption(chat_id=self.user_id, message_id=self.media_id, caption='Удалено')
            pass

    def get_markup(self, button_rows):
        markup = types.InlineKeyboardMarkup()
        for row in button_rows:
            markup.add(*row)
        markup.add(*self.get_page_buttons())
        return markup

    def get_page_buttons(self):
        return [types.InlineKeyboardButton('←', callback_data=f'prev_page {self.page_type}'),
                types.InlineKeyboardButton('→', callback_data=f'next_page {self.page_type}')]
