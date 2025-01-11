class Chainer:
    def __init__(self, bot, user_id, user_obj):
        self.bot = bot
        self.user_id = user_id
        self.user_obj = user_obj

        self.questions_queue = []
        self.answers = []

        self.end_action = None

    def chain(self, questions, end_action):
        self.user_obj.waiting_for = 'chainer'
        self.questions_queue = questions
        self.end_action = end_action
        self.send_question()

    def send_question(self):
        self.bot.send_message(self.user_id, self.questions_queue.pop(0))

    def message_handler(self, message):
        self.answers.append(message.text)

        if len(self.questions_queue) == 0:
            self.user_obj.waiting_for = ''
            self.end_action(self.answers)
            self.answers = []
            print('end')
            return

        self.send_question()
