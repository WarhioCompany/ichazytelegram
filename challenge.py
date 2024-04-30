from datetime import datetime
from db_scripts.db import get_challenge_by_id


class Challenge:
    id = None
    name = None
    desc = None
    image = None
    price = None
    coins_prize = None
    prize_id = None
    date_to = None
    is_hard = None

    def __init__(self, challenge_id):
        self.get_from_db(challenge_id)

    def get_from_db(self, challenge_id):
        data = get_challenge_by_id(challenge_id)
        if not data:
            return
        self.from_json(data[0])

    def from_json(self, data):
        self.id = data['id']
        self.name = data['name']
        self.desc = data['desc']
        self.image = data['image']
        self.price = data['price']
        self.coins_prize = data['coins_prize']
        self.prize_id = data['prize_id']
        self.date_to = datetime.strptime(data['date_to'], '%d/%m/%Y')

    def __bool__(self):
        return bool(self.name)