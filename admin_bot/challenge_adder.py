from datetime import datetime

from db_data.db_session import session_scope
from db_data.models import Challenge, Prize, Promocode, Brand


class ChallengeAdder: #outdated
    def __init__(self, admin):
        self.admin = admin
        self.answers = []
        self.photo = None
        self.video = None

    def pass_media(self, photo, video):
        self.photo = photo
        self.video = video

    def challenge_survey(self):
        self.answers = []
        questions = [
            "Сложный челлендж (д)а/(н)ет",
            'Название челленджа',
            'Описание челленджа',
            "Цена челленджа",
            "Дата завершения челленджа ДД ММ ГГГГ",
            "Вид работы (в)идео/(к)артинка",
            "Лимит работ пользователя",
            "Лимит победителей",
            "Ссылка на пост"
        ]
        self.admin.chainer.chain(questions, [self.get_first_answers])

    def get_first_answers(self, survey_answers):
        self.answers = survey_answers
        if self.answers[0] == 'д':
            self.hard_challenge_survey()
            # челлендж сложный
            pass
        else:
            self.easy_challenge_survey()

    def easy_challenge_survey(self):
        self.admin.chainer.chain(['Приз в лекойнах'], [self.combine_answers_and_add_challenge])

    def hard_challenge_survey(self):
        # TODO: prize + promocodes + adding challenge
        self.prize_chain()

        pass

    def prize_chain(self):
        def get_answers(answers):
            self.answers += answers
            self.promocodes_chain()

        self.admin.chainer.chain(['Название приза', 'Описание приза'], [get_answers])

    def promocodes_chain(self):
        promocodes_left = 0

        def promocode_chain(prev_answers=None):
            global promocodes_left
            if prev_answers:
                self.answers[-1] += [prev_answers]

            if promocodes_left != 0:
                self.admin.chainer.chain(['Промо', 'контакт в тг (ник чела (@warhio))'], [promocode_chain])
                promocodes_left -= 1
            else:
                self.add_challenge()

        def promocode_chainer(answer):
            global promocodes_left
            promocodes_left = int(answer[0])
            self.answers.append([])
            promocode_chain()

        self.admin.chainer.chain(['Сколько всего промокодов'], [promocode_chainer])

    def combine_answers_and_add_challenge(self, answers):
        self.answers += answers
        self.add_challenge()

    def add_challenge(self):
        with session_scope() as session:
            print(self.answers)
            name = self.answers[1]
            desc = '\n' + self.answers[2]
            price = int(self.answers[3])
            date_to = datetime.strptime(self.answers[4], '%d %m %y')
            userwork_type = 'image' if self.answers[5] == 'к' else 'video'
            userwork_limit = int(self.answers[6])
            winner_limit = int(self.answers[7])
            post_link = self.answers[8]

            if self.answers[0] == 'д':
                # hard
                prize = Prize(
                    name=self.answers[9],
                    description=self.answers[10]
                )
                session.add(prize)

                brand = Brand(
                    name='no brand'
                )
                session.add(brand)

                promocodes = [Promocode(
                    brand=brand,
                    promo=data[0],
                    telegram_contact=data[1]
                ) for data in self.answers[11]]

                [session.add(promocode) for promocode in promocodes]

                challenge = Challenge(
                    name=name,
                    description=desc,
                    image=self.photo,
                    video=self.video,
                    price=price,
                    date_to=date_to,
                    work_type=userwork_type,
                    userwork_limit=userwork_limit,
                    winner_limit=winner_limit,
                    is_hard=True,
                    promocodes=promocodes,
                    prize=prize,
                    post_link=post_link
                )
            else:
                challenge = Challenge(
                    name=name,
                    description=desc,
                    image=self.photo,
                    video=self.video,
                    price=price,
                    date_to=date_to,
                    work_type=userwork_type,
                    userwork_limit=userwork_limit,
                    winner_limit=winner_limit,
                    coins_prize=int(self.answers[9]),
                    post_link=post_link
                )

            session.add(challenge)
            session.commit()