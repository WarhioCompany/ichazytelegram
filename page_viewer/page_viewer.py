class PageViewer:
    def __init__(self, bot, user_id):
        self.current_page = 0
        self.images_ids = []
        self.picker_id = None

        self.bot = bot
        self.user_id = user_id

    def reset(self):
        self.current_page = 0
        self.delete_all()

    def send_page(self, media_group):
        self.reset()
        messages_data = self.bot.send_media_group(self.user_id, media=media_group)
        self.images_ids = [message.message_id for message in messages_data]

    def send_picker(self, text, buttons=None):
        self.picker_id = self.bot.send_message(self.user_id, text, reply_markup=buttons).id

    def update_page(self, media_group):
        for i in range(len(self.images_ids)):
            try:
                self.bot.edit_message_media(chat_id=self.user_id, message_id=self.images_ids[i], media=media_group[i])
            except:
                print('Page is identical')

    def update_picker(self, text, buttons):
        try:
            self.bot.edit_message_text(chat_id=self.user_id, message_id=self.picker_id,
                                       reply_markup=buttons, text=text)
        except:
            print('Picker is identical')

    def delete_all(self):
        self.delete_picker()
        self.delete_page()

    def delete_page(self):
        for message in self.images_ids:
            self.bot.delete_message(self.user_id, message)
        self.images_ids.clear()

    def delete_picker(self):
        if self.picker_id:
            self.bot.delete_message(self.user_id, self.picker_id)
