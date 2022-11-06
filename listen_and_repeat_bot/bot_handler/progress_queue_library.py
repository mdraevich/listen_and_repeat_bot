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
        """
        define required objects for class instance
        """
        self.progress = {}
        self.current_question_id = None  

    def reset(self):
        """
        should reset a progress for all questions
        """
        raise NotImplemented

    def update_questions(self, questions):
        """
        args:
            questions - list of question IDs (str) to 
                        add in progress queue object 
        """
        raise NotImplemented

    def next_question(self):
        """
        returns:
            question_id (str) - next question_id to ask a user
        """
        raise NotImplemented

    def current_question(self):
        """
        returns:
            question_id (str) - question_id of currently active question
        """
        return self.current_question_id

    def get_progress(self):
        """
        returns:
            question_progress (dict) - pairs of 
                                       <question_id> (str), <value> (int)
                                       where value is between 0-100 and
                                       represents how a user knows question
        """
        return self.progress

    def set_progress(self, progress):
        """
        args:
            question_progress (dict) - pairs of 
                                       <question_id> (str), <value> (int)
                                       where value is between 0-100 and
                                       represents how a user knows question
        """
        self.progress = progress

    def change_question_progress(self, question_id, change):
        """
        args:
            question_id (str) - question_id to change progress of
            change (float) - value between [-1, 1] that represents
                             how to change progress of question_id
                             set to -1 to decrease progress 
                             set to 1 to increase progress
        """

        raise NotImplemented


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

    def change_question_progress(self, question_id, change):
        pass

    def reset(self):
        for key in self.progress.keys():
            self.progress[key] = 0


class ProgressQueuePriorityRandom(ProgressQueueRandom):
    """
    """

    def next_question(self):
        choices = random.choices(
                       population=self.progress.keys(),
                       weights=self.progress.values(),
                       k=1)
        if choices:
            self.current_question_id = choices[0]
        else:
            self.current_question_id = None

        return self.current_question_id

    def change_question_progress(self, question_id, change):
        self.progress[question_id] += int(change * 10)
        self.progress = max(self.progress, 0)
        self.progress = min(self.progress, 100)
