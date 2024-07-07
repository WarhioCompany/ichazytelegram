from messages_handler import messages


class Notify:
    def __init__(self, bot):
        self.bot = bot

    def userwork_approved(self, userwork):
        self.bot.send_photo(userwork.user_id, photo=userwork.data, caption=messages['userwork_approved'])

    def userwork_disapproved(self, userwork):
        self.bot.send_photo(userwork.user_id, photo=userwork.data, caption=messages['userwork_disapproved'])