from db_scripts.db import get_user_work_by_id, add_user_work, update_like_count_userwork
from datetime import datetime


class UserWork:
    id = None
    user_id = None
    challenge_id = None
    data = None
    date = None
    type = None  # image, video
    like_count = None

    def __init__(self, work_id=None, user_id=None, challenge_id=None, data=None, type=None, like_count=None):
        if work_id:
            self.get_from_db(work_id)
        else:
            self.user_id = user_id
            self.challenge_id = challenge_id
            self.data = data
            self.date = datetime.now().strftime('%d/%m/%y')
            self.type = type
            self.like_count = like_count

    def add_to_db(self):
        add_user_work(self.user_id, self.data, self.challenge_id, self.type, self.date)

    def update_db(self):
        update_like_count_userwork(self.id, self.like_count)

    def from_json(self, data):
        self.id = data['id']
        self.user_id = data['user_id']
        self.challenge_id = data['challenge_id']
        self.data = data['data']
        self.date = datetime.strptime(data['date'], '%d/%m/%y')
        self.type = data['type']
        self.like_count = data['like_count']

    def get_from_db(self, work_id):
        data = get_user_work_by_id(work_id)
        if not data:
            print('No such work')
            return
        self.from_json(data[0])
