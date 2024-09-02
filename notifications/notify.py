from db_data import models
from messages_handler import messages
from telebot import types


class Notify:
    def __init__(self, bot):
        self.bot = bot

    def userwork_approved(self, userwork):
        if userwork.challenge.is_hard:
            self.bot.send_photo(userwork.user_id, photo=userwork.data, caption=messages['userwork_approved_hard'])
        else:
            self.bot.send_photo(userwork.user_id, photo=userwork.data, caption=messages['userwork_approved'])

    def userwork_disapproved(self, userwork):
        self.bot.send_photo(userwork.user_id, photo=userwork.data, caption=messages['userwork_disapproved'])


class AdminNotify:
    def __init__(self):
        self.bot = None
        self.admin_ids = set()

    def set_bot(self, bot):
        self.bot = bot

    def add_admin(self, admin_id):
        self.admin_ids.add(admin_id)

    def user_used_promocode(self, user: types.User, promocode: models.Promocode):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Approve', callback_data=f'promo_confirmation approve {user.id} {promocode.id}'),
                   types.InlineKeyboardButton('Decline', callback_data=f'promo_confirmation decline'))

        for admin_id in self.admin_ids:
            self.bot.send_message(
                admin_id,
                f'@{user.username} использовал промокод: {promocode.promo}',
                # reply_markup=markup
            )

