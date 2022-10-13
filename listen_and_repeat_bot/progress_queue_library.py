import random



class ProgressQueue():
    """
        class contains all required
        methods for ProgressQueue successors
    """

    def reset(self):
        raise NotImplemented

    def update_questions(self, questions):
        raise NotImplemented

    def next_question(self):
        raise NotImplemented


class ProgressQueueRandom(ProgressQueue):
    """
        class can be used to generate question in
        a random manner without any tracking of learning progress
    """

    def __init__(self):
        self.questions = []


    def update_questions(self, questions):
        self.questions = questions


    def next_question(self):
        return random.choice(self.questions)

