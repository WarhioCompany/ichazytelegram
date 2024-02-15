from challenge_viewer import ChallengeViewer
from db_scripts.db import get_user_by_telegram_id, add_user


class User:
    id = None
    name = None
    coins = None
    prizes = None
    # Are you waiting for something? mewo
    waiting_for = None

    def __init__(self, telegram_id=None, name=None):
        self.challenge_viewer = ChallengeViewer()

        if name:
            add_user(name, telegram_id)
        self.get_from_db(telegram_id)

    def from_json(self, data):
        self.id = data['id']
        self.name = data['name']
        self.coins = data['coins']
        self.prizes = data['prizes']

    def get_from_db(self, telegram_id):
        data = get_user_by_telegram_id(telegram_id)
        if not data:
            print('No such user')
            return
        self.from_json(data[0])