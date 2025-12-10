import random
from email.policy import default

from sqlalchemy import and_, not_, desc
from telebot import types
from telebot.types import InputMediaPhoto

from db_data import models, db_tools
from db_data.db_session import session_scope
from db_data.models import Promocode, PromocodeOnModeration, User, Brand, BoostPromocode, Prize
from telebot.apihelper import ApiTelegramException


def bool_to_text(value):
    return 'ДА' if value else 'НЕТ'


TEMP_NAME = 'TemporaryName'
NOTHING_FOUND_TEXT = "Ничего нет"

# edit_key, edit_name, edit_desc
class ModelEditor:
    def __init__(self, bot, admin_id, chainer, object_class, object_default_args, edit_data, callback_name, child_class):
        self.bot = bot
        self.admin_id = admin_id
        self.chainer = chainer

        self.message_id = None
        self.message_has_media = False
        self.edit_message_id = None

        self.child = child_class
        self.current_object = None

        self.current_page = 0
        self.edit_data = edit_data # {edit_key: [edit_name, edit_desc]}

        self.object_class = object_class
        self.object_default_args = object_default_args

        self.cb_data = f'model_editor {callback_name} '

    def create_object_class(self):
        return self.object_class(**self.object_default_args)

    def update_obj_and_get_text_and_markup_and_media(self):
        self.current_object = self.get_object()
        if self.current_object:
            return self.text(), self.get_markup(), self.child.get_current_media()
        else:
            return NOTHING_FOUND_TEXT, self.get_create_only_markup(), None

    def send_media(self, text, markup, media):
        self.message_has_media = True
        if isinstance(media, types.InputMediaPhoto):
            self.message_id = self.bot.send_photo(self.admin_id, photo=media.media, caption=text, reply_markup=markup).message_id
        elif isinstance(media, types.InputMediaVideo):
            self.message_id = self.bot.send_video(self.admin_id, video=media.media, caption=text, reply_markup=markup).message_id
        else:
            raise Exception(f'Incorrect media type ({media.__class__})')

    def update_media(self, text, markup, media):
        media.caption = text
        if self.message_has_media:
            self.bot.edit_message_media(chat_id=self.admin_id, message_id=self.message_id, media=media, reply_markup=markup)
        else:
            self.bot.delete_message(self.admin_id, self.message_id)
            self.send_media(text, markup, media)

    def send_page(self):
        text, markup, media = self.update_obj_and_get_text_and_markup_and_media()
        if media:
            self.send_media(text, markup, media)
        else:
            self.message_has_media = False
            self.message_id = self.bot.send_message(self.admin_id, text, reply_markup=markup).message_id

    def update_page(self):
        text, markup, media = self.update_obj_and_get_text_and_markup_and_media()
        try:
            if media:
                self.update_media(text, markup, media)
            else:
                self.message_has_media = False
                self.bot.edit_message_text(chat_id=self.admin_id, message_id=self.message_id, text=text, reply_markup=markup)
        except ApiTelegramException as e:
            print(e)

    def next_page(self):
        self.current_page += 1
        self.update_page()

    def prev_page(self):
        self.current_page -= 1
        self.update_page()


    def get_object(self):
        with session_scope() as db_sess:
            objects = db_sess.query(self.object_class).all()

            if not objects:
                obj = None
            else:
                obj = objects[-(self.current_page % len(objects)) - 1]
        return obj


    def get_create_only_markup(self):
        markup = types.InlineKeyboardMarkup()
        create_button = types.InlineKeyboardButton('Создать', callback_data=self.cb_data + 'create')
        markup.add(create_button)
        return markup

    def get_markup(self):
        markup = types.InlineKeyboardMarkup()
        create_button = types.InlineKeyboardButton('Создать', callback_data=self.cb_data + 'create')

        if not self.current_object:
            markup.add(create_button)
            return markup

        markup.add(types.InlineKeyboardButton('Изменить', callback_data=self.cb_data + 'edit'))

        markup.add(types.InlineKeyboardButton('←', callback_data=self.cb_data + 'prev_page'),
                   types.InlineKeyboardButton('→', callback_data=self.cb_data + 'next_page'))
        markup.add(create_button)

        return markup


    def edit_message_markup(self):
        markup = types.InlineKeyboardMarkup()
        for key, edit_data in self.edit_data.items():
            markup.add(types.InlineKeyboardButton(edit_data[0], callback_data=self.cb_data + f'edit_{key}'))
        markup.add(types.InlineKeyboardButton('Удалить', callback_data=self.cb_data + f'edit_delete'))
        markup.add(types.InlineKeyboardButton('Отмена', callback_data=self.cb_data + f'edit_cancel'))
        return markup

    def handle_callback(self, call):
        option = call.data.split()[2]
        if option.startswith('edit_'):
            self.edit(option)
        elif option == 'next_page':
            self.next_page()
        elif option == 'prev_page':
            self.prev_page()
        elif option == 'edit':
            self.send_edit_message()
        elif option == 'create':
            self.create_object()


    def send_edit_message(self):
        self.edit_message_id = self.bot.send_message(self.admin_id, 'Что изменить?',
                                                     reply_markup=self.edit_message_markup()).message_id


    def delete_edit_message(self):
        if self.edit_message_id:
            self.bot.delete_message(chat_id=self.admin_id, message_id=self.edit_message_id)
            self.edit_message_id = None


    def get_question_for_edit_key(self, edit_key):
        if self.edit_data[edit_key][1]:
            return [self.edit_data[edit_key][1]]
        return []


    def edit(self, option):
        self.delete_edit_message()

        edit_key = '_'.join(option.split('_')[1:])

        if edit_key == 'cancel':
            return
        elif edit_key == 'delete':
            self.delete_current_object()
        else:
            edit_func = lambda ans: self.child.edit_field(edit_key, ans[0] if ans else None)
            self.chainer.chain(self.get_question_for_edit_key(edit_key), [edit_func])


    def delete_current_object(self):
        with session_scope() as session:
            session.query(self.object_class).filter(self.object_class.id == self.current_object.id).delete()
            session.commit()
        self.update_page()

    def is_object_template(self, obj):
        for arg in self.object_default_args:
            if getattr(obj, arg) != self.object_default_args[arg]:
                return False
        return True

    def delete_not_used_object(self): # does not work because of promocode comparison
        with session_scope() as session:
            last_added_obj = session.query(self.object_class).order_by(desc(self.object_class.id)).first()
            if self.is_object_template(last_added_obj):
                session.delete(last_added_obj)
                session.commit()

    def create_object(self):
        with session_scope() as session:
            # self.delete_not_used_object()
            session.add(self.create_object_class())
            session.commit()
        self.current_page = 0
        self.update_page()


    def flip_bool_field(self, field):
        with session_scope() as session:
            obj = session.query(self.object_class).filter(self.object_class.id == self.current_object.id).one()
            setattr(obj, field, not getattr(obj, field))
            session.commit()
        self.update_page()


    def text(self):
        return self.child.get_text() + f'\n\nid: {self.current_object.id}'


    def get_current_media(self):
        return None

# View and edit available coins promocodes
class CoinsPromocodeViewer(ModelEditor):
    def __init__(self, bot, admin_id, chainer):
        super().__init__(bot, admin_id, chainer, Promocode, {'promo': TEMP_NAME}, {
            'promo': ['Название промокода', 'Введи название промокода (что будет вводить юзер)'],
            'coins': ['Монетки', 'Сколько монет получит пользователь после использования промокода'],
            'profit': ['Профит', 'Сколько получаем $$$ за один промик'],
            'is_expired': ['Активность', ''],
            'need_confirmation': ['Подтверждение модером', ''],
            'is_subscription_required': ['Подписка на блогера', ''],
            'channel_id': ['Канал блогера', 'На какой канал оформить подписку'],
            'is_image_proof_required': ['Пруф картинкой', ''],
        }, 'promocode_viewer', self)


    def edit_field(self, edit_key, value):
        with session_scope() as session:
            promocode = session.query(Promocode).filter(Promocode.id == self.current_object.id).one()
            if edit_key == 'promo':
                promocode.promo = value
            elif edit_key == 'coins':
                promocode.coins = int(value)
            elif edit_key == 'contact':
                promocode.telegram_contact = value
            elif edit_key == 'profit':
                promocode.profit = float(value.replace(',', '.'))
            elif edit_key == 'channel_id':
                promocode.required_channel_id = value
            elif edit_key in ['is_expired', 'need_confirmation', 'is_subscription_required', 'is_image_proof_required']:
                self.flip_bool_field(edit_key)
            session.commit()
        self.chainer.clear_chain()
        self.update_page()


    def get_text(self):
        required_subscription_text = f"Нужна подписка на {self.current_object.required_channel_id}\n" if self.current_object.is_subscription_required else 'Нужна подписка? НЕТ\n'

        if self.current_object:
            return (f"{self.current_object.promo}\n"
                    f"Монетки: {self.current_object.coins}\n"
                    f"Профит с промика: {self.current_object.profit}\n"
                    f"Надо подтверждать? {bool_to_text(self.current_object.need_confirmation)}\n"
                    f"Нужен пруф? {bool_to_text(self.current_object.is_image_proof_required)}\n"
                    + required_subscription_text +
                    f"Просрочен? {bool_to_text(self.current_object.is_expired)}\n"
                    f"Профит со всех промокодов: {self.calculate_profit()}")
        else:
            return 'Нет промокодов'

    def calculate_profit(self):
        with session_scope() as session:
            promocode = session.query(Promocode).filter(Promocode.id == self.current_object.id).one()
            return promocode.profit * len(promocode.users_used)



class BoostPromocodeViewer(ModelEditor):
    def __init__(self, bot, admin_id, chainer):
        super().__init__(bot, admin_id, chainer, BoostPromocode, {'promo': TEMP_NAME}, {
            'promo': ['Название промокода', 'Введи название промокода (что будет вводить юзер)'],
            'coefficient': ['Коэффициент', 'На что будет умножаться доход юзера'],
            'value': ['Кол-во дней/челленджей', 'В зависимости от типа промокода введи или кол-во дней, или кол-во челледжей'],
            'is_expired': ['Активность', ''],
            'need_confirmation': ['Подтверждение модером', ''],
            'type': ['Изменить тип промокода дни<->челленджи', '']
        }, 'boost_promocode_viewer', self)


    def edit_field(self, edit_key, value):
        with session_scope() as session:
            promocode = session.query(BoostPromocode).filter(BoostPromocode.id == self.current_object.id).one()
            if edit_key == 'promo':
                promocode.promo = value
            elif edit_key == 'coefficient':
                promocode.coefficient = float(value.replace(',', '.'))
            elif edit_key == 'value':
                promocode.absolute_value = value
            elif edit_key == 'type':
                promocode.promocode_type = 'count' if promocode.promocode_type == 'date' else 'date'
            elif edit_key in ['need_confirmation', 'is_expired']:
                self.flip_bool_field(edit_key)
            session.commit()
        self.chainer.clear_chain()
        self.update_page()

    def type_text(self):
        return 'Количество дней' if self.current_object.promocode_type == 'date' else "Количество челленджей"


    def get_text(self):
        if self.current_object:
            return (f"{self.current_object.promo}\n"
                    f"{self.type_text()}: {self.current_object.absolute_value}\n"
                    f"Коэффициент: {self.current_object.coefficient}\n"
                    f"Надо подтверждать? {bool_to_text(self.current_object.need_confirmation)}\n"
                    f"Просрочен? {bool_to_text(self.current_object.is_expired)}\n")
        else:
            return 'Нет промокодов'


class PrizeViewerAdmin(ModelEditor):
    def __init__(self, bot, admin_id, chainer):
        super().__init__(bot, admin_id, chainer, Prize, {"name": TEMP_NAME}, {
            'name': ['Название', 'Введи название приза'],
            'description': ['Описание', 'Введи описание приза'],
            'barrier_type': ['Тип барьера (нет->рефералы->подписчики->промокоды)', ''],
            'barrier_value': ['Значение барьера', 'Сколько подписчиков/рефералов/промокодов нужно, чтобы приз появился'],
            'preview': ['Картинка приза', 'Кидай картинку']
        }, 'prize_viewer', self)


    def edit_field(self, edit_key, value):
        with session_scope() as session:
            prize = session.query(Prize).filter(Prize.id == self.current_object.id).one()
            if edit_key == 'name':
                prize.name = value
            elif edit_key == 'description':
                prize.description = value
            elif edit_key == 'barrier_type':
                prize.barrier_type = self.get_next_barrier_type()
            elif edit_key == 'barrier_value':
                prize.barrier_value = int(value)
            elif edit_key == 'preview':
                prize.preview = value.media
            session.commit()
        self.chainer.clear_chain()
        self.update_page()


    def get_next_barrier_type(self):
        barrier_types = [None, 'referrals', 'subscribers', 'promocodes']
        return barrier_types[(barrier_types.index(self.current_object.barrier_type) + 1) % len(barrier_types)]

    def get_current_media(self):
        if self.current_object.preview:
            return types.InputMediaPhoto(self.current_object.preview)
        else:
            return types.InputMediaPhoto(db_tools.get_empty_image())

    def text_barrier_type(self):
        if self.current_object.barrier_type == 'referrals':
            return 'По количеству рефералов'
        elif self.current_object.barrier_type == 'subscribers':
            return 'По количеству подписчиков на канале'
        elif self.current_object.barrier_type == 'promocodes':
            return 'По количеству отоваренных промокодов привязанных к челленджу(ам)'

    def get_text(self):
        if self.current_object:
            return (f"{self.current_object.name}\n"
                    f"{self.current_object.description}\n\n"
                    f"Тип барьера: {self.text_barrier_type()}\n"
                    f"Значение барьера: {self.current_object.barrier_value}\n")
        else:
            return 'Нет промокодов'