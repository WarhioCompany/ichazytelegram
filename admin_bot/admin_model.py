from admin_bot.primitive_model_editor import BoostPromocodeViewer, CoinsPromocodeViewer, PrizeViewerAdmin
from page_viewer.user_work_viewer import AdminUserWorksPageViewer
from admin_bot.promocode_viewer import ModeratorPromocodeViewer
from page_viewer.challenge_viewer import ChallengePageViewerAdmin
from chainer import Chainer


class Admin:
    def __init__(self, admin_id, bot, notify):
        self.admin_id = admin_id
        self.bot = bot
        self.notify = notify
        self.chainer = Chainer(bot, admin_id, self)

        self.is_authorized = False

        self.userwork_viewer = AdminUserWorksPageViewer(bot, admin_id, notify)
        self.moderator_promocode_viewer = ModeratorPromocodeViewer(bot, admin_id, notify)
        self.challenge_viewer = ChallengePageViewerAdmin(bot, admin_id, self.chainer)
        self.coins_promocode_viewer = CoinsPromocodeViewer(bot, admin_id, self.chainer)
        self.boost_promocode_viewer = BoostPromocodeViewer(bot, admin_id, self.chainer)
        self.prize_viewer = PrizeViewerAdmin(bot, admin_id, self.chainer)

        self.waiting_for = ''
        self.buf = {}
