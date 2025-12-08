from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from admin_bot.prize_barrier_checker import send_prize_barrier_message, send_actual_prizes_message
from db_data.db_session import session_scope
from db_data.models import User
from messages_handler import messages
from tools.referrals import count_referrals_of_user


# handles and sets up MenuPages
class MenuMessage:
    def __init__(self, bot, user):
        self.bot = bot
        self.user_id = user.user_id
        self.user = user

        self.pages = {}
        self.set_up_menu()

    def set_keys(self):
        for key in self.pages:
            self.pages[key].page_key = key

    def send(self):
        self.pages['main'].send()

    def handle(self, call):
        if call.data == 'menu_send':
            self.send()
            return

        _, page_key, button_id = call.data.split()
        self.pages[page_key].handle_button(call.message.message_id, button_id)

    def add_page(self, page_key, buttons_names, buttons_func, get_text_func):
        self.pages[page_key] = MenuPage(self.bot, self.user_id, page_key, buttons_names, buttons_func, get_text_func)

    def get_page(self, page_key): return self.pages[page_key]

    def send_message_command(self, message):
        return lambda: self.bot.send_message(self.user_id, messages[message])

    def set_up_menu(self):
        self.add_page('main', [
            ['⚡ Челленджи'],
            ['🎁✨ Актуальные подарки и ништячки'],
            ['💬 Связаться с нами', '👤 Мой профиль']
        ], [
            self.user.challenge_viewer.show_challenges,
            None,
            None,
            None
        ], self.get_menu_text)

        self.add_page('gifts', [
            ['🎉 Подарки в розыгрыше'],
            ['🔮 Будущие награды'],
            ['🎫 Ввести промокод'],
            ['😺 Хочу стикерпак'],
            ['🏠 Меню']
        ], [
            self.user.actual_prize_viewer.send,#lambda: send_actual_prizes_message(self.bot, self.user_id),
            self.user.future_prize_viewer.send,
            self.user.promocode_command,
            self.send_message_command('shop'),
            self.pages['main']
        ], self.get_menu_text)

        self.add_page('feedback', [
            ['🤝 Я блогер и хочу сотрудничать'],
            ['❗ У меня что-то сломалось'],
            ['🏠 Меню']
        ], [
            self.send_message_command('partnership'),
            self.send_message_command('support'),
            self.pages['main']
        ], self.get_menu_text)
        self.add_page('profile', [
            ['🌟 Мои работы'],
            ['🔗 Моя ссылка для приглашения в Чейзи'],
            ['🏠 Меню']
        ], [
            self.user.private_userworks_viewer.send_mode_picker,
            self.user.send_referral_link,
            self.pages['main']
        ], lambda x: self.get_menu_text(x).format(**self.get_profile_info()))

        self.pages['main'].buttons_func[1] = self.pages['gifts']
        self.pages['main'].buttons_func[2] = self.pages['feedback']
        self.pages['main'].buttons_func[3] = self.pages['profile']

    def get_menu_text(self, page_key):
        return messages[f'{page_key}_menu']

    def get_profile_info(self):
        with session_scope() as session:
            user_obj = session.query(User).filter(User.telegram_id == self.user_id).one()

            coins = user_obj.coins
            if 11 <= coins <= 19:
                lecoin_word = 'лекоинов'
            elif coins % 10 == 1:
                lecoin_word = 'лекоин'
            elif 2 <= coins % 10 <= 4:
                lecoin_word = 'лекоина'
            else:
                lecoin_word = 'лекоинов'

            referral_count = count_referrals_of_user(self.user_id)

            return {
                'name': user_obj.name,
                'coins': user_obj.coins,
                'lecoin_word': lecoin_word,
                'referral_count': referral_count
            }




class MenuPage:
    def __init__(self, bot, user_id, page_key, buttons_names, buttons_func, get_text_func):
        self.bot = bot
        self.user_id = user_id
        self.buttons_names = buttons_names
        self.buttons = self.make_linear(buttons_names)
        self.buttons_func = buttons_func #button_name: function/menupage
        self.get_text = get_text_func
        self.page_key = page_key

    def reply_markup(self):
        markup = InlineKeyboardMarkup()
        for button_row in self.buttons_names:
            row = []
            for button_name in button_row:
                row.append(InlineKeyboardButton(button_name, callback_data=f'menu {self.page_key} {self.get_button_id(button_name)}'))
            markup.add(*row)
        return markup

    def make_linear(self, arr2d):
        linear = []
        for row in arr2d:
            linear += row
        return linear

    def get_button_id(self, button_name):
        return self.buttons.index(button_name)

    def set_button_func(self, name, func):
        self.buttons_func[self.get_button_id(name)] = func

    def send(self):
        self.bot.send_message(self.user_id, self.get_text(self.page_key), reply_markup=self.reply_markup(), parse_mode='MarkdownV2')

    def edit(self, message_id):
        self.bot.edit_message_text(chat_id=self.user_id, message_id=message_id, text=self.get_text(self.page_key), reply_markup=self.reply_markup(), parse_mode='MarkdownV2')

    def handle_button(self, message_id, button_id):
        obj = self.buttons_func[int(button_id)]
        if isinstance(obj, MenuPage):
            obj.edit(message_id)
        elif obj:
            obj()
