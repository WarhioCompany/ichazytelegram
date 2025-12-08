from admin_bot.primitive_model_editor import PrizeViewerAdmin
from chainer import Chainer
from db_data.db_session import session_scope
from db_data.models import User
from menu_message import MenuMessage
from messages_handler import messages
from page_viewer.challenge_viewer import ChallengePageViewerUser
from page_viewer.prize_viewer import ActualPrizeViewer, FuturePrizeViewer
from page_viewer.user_work_viewer import UserWorksPageViewer, PrivateUserWorksPageViewer


class UserData:
    def __init__(self, bot, telegram_id, promocode_manager, name=None, invited_by=''):
        self.waiting_for = ''
        self.user_id = telegram_id

        self.bot = bot

        self.invited_by = invited_by

        if name:
            self.create_user(name, invited_by)

        self.challenge_viewer = ChallengePageViewerUser(bot, self)
        self.userworks_viewer = UserWorksPageViewer(bot, telegram_id)
        self.private_userworks_viewer = PrivateUserWorksPageViewer(bot, telegram_id)
        self.chainer = Chainer(bot, telegram_id, self)
        self.promocode_manager = promocode_manager # needs to be set when user is created
        self.actual_prize_viewer = ActualPrizeViewer(bot, telegram_id)
        self.future_prize_viewer = FuturePrizeViewer(bot, telegram_id)
        self.menu = MenuMessage(bot, self)

    def __bool__(self):
        return bool(self.user_id)

    def user(self):
        with session_scope() as session:
            user = session.query(User).filter(User.telegram_id == self.user_id).first()
            return user

    def create_user(self, name, invited_by):
        user = User(
            telegram_id=self.user_id,
            name=name,
            invited_by=invited_by
        )
        with session_scope() as session:
            session.add(user)
            session.commit()

    def promocode_command(self):
        def enter_promocode(answer):
            self.promocode_manager.enter_promocode(self, answer[0])
        self.chainer.chain([messages["enter_promocode"]], [enter_promocode])

    def send_referral_link(self):
        self.bot.send_message(self.user_id, messages['get_my_link'].format(link=f'https://t.me/chazychannelbot?start={self.user_id}'))