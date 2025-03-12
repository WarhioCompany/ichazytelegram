from page_viewer.user_work_viewer import AdminUserWorksPageViewer
from admin_bot.promocode_viewer import PromocodeViewer
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
        self.promocode_viewer = PromocodeViewer(bot, admin_id)
        self.challenge_viewer = ChallengePageViewerAdmin(bot, admin_id, self.chainer)

        self.waiting_for = ''
        self.buf = {}
