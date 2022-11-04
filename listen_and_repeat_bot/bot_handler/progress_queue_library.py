import json
import random



class ProgressQueue(dict):
    """
        class contains all required
        methods for ProgressQueue successors

        self.current_question_id - current question_id user
                                   have to provide an answer 
        self.progress - dict of <question_id>: <progress_value>
                        <progress_value> should be between 0-100
                        0 - user knows nothing; 100 - user knows excellent
    """

    def __init__(self):
        # must have objects
        self.progress = {}
        self.current_question_id = None  

    def reset(self):
        raise NotImplemented

    def update_questions(self, questions):
        """
        args:
            questions - list of question IDs to 
                        add in progress object 
        """

        raise NotImplemented

    def next_question(self):
        raise NotImplemented

    def current_question(self):
        raise NotImplemented

    def get_progress(self):
        return self.progress

    def set_progress(self, progress):
        self.progress = progress



class ProgressQueueRandom(ProgressQueue):
    """
        class can be used to generate question in
        a random manner without any tracking of learning progress
    """

    def update_questions(self, questions):
        for question_id in questions:
            if question_id not in self.progress:
                self.progress[question_id] = 0

    def next_question(self):
        self.current_question_id = random.choice(
                                   list(self.progress.keys()))
        return self.current_question_id

    def current_question(self):
        return self.current_question_id

