from db_data.db_session import session_scope
from db_data.models import User
from page_viewer.challenge_viewer import ChallengePageViewer
from page_viewer.user_work_viewer import UserWorksPageViewer, PrivateUserWorksPageViewer


class UserData:
    def __init__(self, bot, telegram_id, name=None):
        self.waiting_for = ''
        self.user_id = telegram_id
        if name:
            self.create_user(name)

        self.challenge_viewer = ChallengePageViewer(bot, telegram_id)
        self.userworks_viewer = UserWorksPageViewer(bot, telegram_id)
        self.private_userworks_viewer = PrivateUserWorksPageViewer(bot, telegram_id)

    def user(self):
        with session_scope() as session:
            user = session.query(User).filter(User.telegram_id == self.user_id).first()
            return user

    def create_user(self, name):
        user = User(
            telegram_id=self.user_id,
            name=name
        )
        with session_scope() as session:
            session.add(user)
            session.commit()