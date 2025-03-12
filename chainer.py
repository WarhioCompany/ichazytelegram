class Chainer:
    def __init__(self, bot, user_id, user_obj):
        self.bot = bot
        self.user_id = user_id
        self.user_obj = user_obj

        self.questions_queue = []
        self.answers = []

        self.messages_id = []

        self.end_actions = None

    def chain(self, questions, end_actions):
        self.answers = []
        self.messages_id = []

        self.user_obj.waiting_for = 'chainer'
        self.questions_queue = questions
        self.end_actions = end_actions
        self.send_question()

    def send_question(self):
        self.messages_id.append(self.bot.send_message(self.user_id, self.questions_queue.pop(0)).message_id)

    def message_handler(self, message):
        self.answers.append(message.text)
        self.messages_id.append(message.message_id)

        if len(self.questions_queue) == 0:
            self.user_obj.waiting_for = ''
            self.call_actions()
            return

        self.send_question()

    def call_actions(self):
        for action in self.end_actions:
            action(self.answers)

    def clear_chain(self):
        for message_id in self.messages_id:
            self.bot.delete_message(self.user_id, message_id)
        self.messages_id.clear()