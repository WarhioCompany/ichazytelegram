from telebot import types

from admin_bot.prize_barrier_checker import get_barrier_type_text
from db_data import db_tools
from db_data.db_session import session_scope
from db_data.models import Prize
from messages_handler import messages
from page_viewer.page_viewer import PageViewer
from tools import text_escaper


class ActualPrizeViewer(PageViewer):
    def __init__(self, bot, user_id):
        super().__init__(bot, user_id, 'actual_prize', parse_mode='MarkdownV2')

        self.current_prize = None


    def get_current_prize(self):
        with session_scope() as session:
            prizes = session.query(Prize).all()
            actual_prizes = [prize for prize in prizes if prize.challenges]
            if actual_prizes:
                cnt = len(actual_prizes)#db_tools.get_table_count(session, Prize)
                self.current_page %= cnt
                element_id = (cnt - self.current_page - 1) % cnt
                self.current_prize = actual_prizes[element_id]

                #self.current_prize = db_tools.get_element_by_id(session, Prize, element_id, Prize.challenges.is_not([]))
            else:
                self.current_page = 0
                self.current_prize = None

    def refresh(self):
        self.get_current_prize()
        self.update_page(self.get_media(), [])

    def get_media(self):
        preview = self.current_prize.preview if self.current_prize.preview else db_tools.get_empty_image()
        media = types.InputMediaPhoto(preview)
        text = self.get_text()
        media.caption = text
        return media

    def view_prize(self, prize_id):
        if prize_id == -1: return
        with session_scope() as session:
            self.current_prize = session.get(Prize, prize_id)
        self.send_page(self.get_media(), [])

    def get_text(self):
        with session_scope() as session:
            challenge_name = session.query(Prize).filter(Prize.id == self.current_prize.id).one().challenges[0].name
        return messages['actual_prize_page'].format(
            name=self.current_prize.name,
            challenge=challenge_name,
            desc=self.current_prize.description,
        )


    def send(self):
        self.get_current_prize()
        if self.current_prize:
            self.send_page(self.get_media(), [])
        else:
            self.send_message(messages['no_actual_prizes'])


    def next_page(self):
        self.current_page += 1
        self.refresh()

    def prev_page(self):
        self.current_page -= 1
        self.refresh()


class FuturePrizeViewer(PageViewer):
    def __init__(self, bot, user_id):
        super().__init__(bot, user_id, 'future_prize', parse_mode='MarkdownV2')

        self.current_prize = None


    def get_current_prize(self):
        with session_scope() as session:
            prizes = session.query(Prize).all()
            future_prizes = [prize for prize in prizes if not prize.challenges]
            if future_prizes:
                cnt = len(future_prizes)#db_tools.get_table_count(session, Prize)
                self.current_page %= cnt
                element_id = (cnt - self.current_page - 1) % cnt
                self.current_prize = future_prizes[element_id]

                #self.current_prize = db_tools.get_element_by_id(session, Prize, element_id, Prize.challenges.is_not([]))
            else:
                self.current_page = 0
                self.current_prize = None

    def refresh(self):
        self.get_current_prize()
        self.update_page(self.get_media(), [])

    def get_media(self):
        preview = self.current_prize.preview if self.current_prize.preview else db_tools.get_empty_image()
        media = types.InputMediaPhoto(preview)
        text = self.get_text()
        media.caption = text
        return media


    def get_text(self):
        barrier_text = ""
        if self.current_prize.barrier_type:
            barrier_text = text_escaper.escape(get_barrier_type_text(self.current_prize.barrier_type).format(
                barrier_value=self.current_prize.barrier_value
            ))
        return messages['future_prize_page'].format(
            name=self.current_prize.name,
            desc=self.current_prize.description,
            type_explanation=barrier_text,
        )


    def send(self):
        self.get_current_prize()
        if self.current_prize:
            self.send_page(self.get_media(), [])
        else:
            self.send_message(messages['no_future_prizes'])


    def next_page(self):
        self.current_page += 1
        self.refresh()

    def prev_page(self):
        self.current_page -= 1
        self.refresh()


