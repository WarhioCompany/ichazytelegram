from db_data.db_session import session_scope
from db_data.models import User
from page_viewer.challenge_viewer import ChallengePageViewer
from page_viewer.user_work_viewer import UserWorksPageViewer, PrivateUserWorksPageViewer


class UserData:
    def __init__(self, bot, telegram_id, name=None, invited_by=''):
        self.waiting_for = ''
        self.user_id = telegram_id

        self.invited_by = invited_by

        if name:
            self.create_user(name, invited_by)

        self.challenge_viewer = ChallengePageViewer(bot, telegram_id)
        self.userworks_viewer = UserWorksPageViewer(bot, telegram_id)
        self.private_userworks_viewer = PrivateUserWorksPageViewer(bot, telegram_id)

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