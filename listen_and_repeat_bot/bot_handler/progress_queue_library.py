import json
import random
import logging
import os


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.getLevelName(os.environ.get("LOGLEVEL", "WARNING"))
)
logger = logging.getLogger(__name__)


class ProgressQueue(dict):
    """
    class contains all required
    methods for ProgressQueue successors

    self.current_question_id - current question_id user
                               have to provide an answer 
    self.progress - dict of <question_id>: <progress_value>
                    <progress_value> should be between 0-1000
                    0 - user knows nothing; 1000 - user knows excellent
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

    def ignore_question(self, question_id, ignore_ttl):
        """
        args:
            question_id (str) - question_id to ignore
            ignore_ttl (int) - number of questions to do not ask the question
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
                                       where value is between 0-1000 and
                                       represents how a user knows question
        """
        return self.progress

    def set_progress(self, progress):
        """
        args:
            question_progress (dict) - pairs of 
                                       <question_id> (str), <value> (int)
                                       where value is between 0-1000 and
                                       represents how a user knows question
        """
        self.progress = progress

    def change_question_progress(self, question_id, change):
        """
        args:
            question_id (str) - question_id to change progress of
            change (float) - value to add up to the question_id progress
        """
        self.progress[question_id] += int(change)
        self.progress[question_id] = max(self.progress[question_id], 0)
        self.progress[question_id] = min(self.progress[question_id], 1000)


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

    def reset(self):
        for key in self.progress.keys():
            self.progress[key] = 0


class ProgressQueuePriorityRandom(ProgressQueueRandom):
    """
        class can be used to generate next question to learn
        in a weighted random manner

        Weight is a value of learning progress (self.progress[])
        
        the more learning progress of specific question
        the less probability to return it
    """

    def next_question(self):
        choices = random.choices(
                       population=list(self.progress.keys()),
                       weights=[-el for el in self.progress.values()],
                       k=1)
        if choices:
            self.current_question_id = choices[0]
        else:
            self.current_question_id = None

        return self.current_question_id


class ProgressQueuePriorityRandomLimited(ProgressQueuePriorityRandom):
    """
        class can be used to generate next question to learn

        generation happens as follows:
        1) take a subset of questions with 
           similar learning progress (SUBSET_SIZE)
        2) for next SUBSET_TTL calls next_question() will generate
           questions from the selected subset only 
        3) return to step 1
    """

    SUBSET_SIZE = 10
    SUBSET_TTL = 14

    def __init__(self):
        self.selected_subset = None
        super().__init__()


    def _generate_subset(self):
        sorted_questions_progress = sorted(self.progress.items(),
                                           key=lambda item: item[1])
        sorted_question_ids = [el[0] for el in sorted_questions_progress]
        return sorted_question_ids[:self.SUBSET_SIZE]


    def next_question(self):
        if self.selected_subset is None:
            self.selected_subset = self._generate_subset()
            self.selected_subset_ttl = self.SUBSET_TTL

        if len(self.selected_subset):
            # random.choice arg should have len > 0
            previous_question_id = ""
            if self.current_question_id is not None:
                previous_question_id = self.current_question_id

            self.current_question_id = random.choice(self.selected_subset)

            if previous_question_id == self.current_question_id:
                # generate one more time if question_id is the same as before
                self.current_question_id = random.choice(self.selected_subset)

            self.selected_subset_ttl = self.selected_subset_ttl - 1
            if self.selected_subset_ttl <= 0:
                self.selected_subset = None
        else:
            self.current_question_id = None

        return self.current_question_id


class ProgressQueueLearnModesAndSubsets(ProgressQueuePriorityRandomLimited):
    """
        LEARNING_MODE:
            0 - add (learn) new words
            1 - learn words (moderate)
            2 - learn words (good)
            3 - repeat words (excellent)

        SUBSET_SIZE: amount of words to learn
        SUBSET_TTL: how much questions ask about the subset
    """

    LEARNING_MODE = 0
    SUBSET_SIZE = 8
    SUBSET_TTL = 12

    def _shuffle(self, array):
        random.shuffle(array)
        return array

    def _generate_subset(self):
        question_buffer = [
            self._shuffle([k for k,v in self.progress.items() if v == 0]),
            self._shuffle([k for k,v in self.progress.items() if 0   < v <= 400]),
            self._shuffle([k for k,v in self.progress.items() if 400 < v <= 800]),
            self._shuffle([k for k,v in self.progress.items() if 800 < v])
        ]

        logger.debug(f"Question buffers length are the following "
                     f"{[ len(i) for i in question_buffer]}")

        if len(question_buffer[1]) <= 2 * self.SUBSET_SIZE:
            self.LEARNING_MODE = 0
        else:
            self.LEARNING_MODE = random.choice([1, 1, 2, 2, 3])

        question_ids = []
        sorted_qb = sorted(range(4),
                           key=lambda item: abs(self.LEARNING_MODE - item))
        logger.debug(f"LEARNING_MODE is equal to {self.LEARNING_MODE}")
        logger.debug(f"Sorted question buffers are equal to {sorted_qb}")

        for qb_id in sorted_qb:
            question_ids += question_buffer[qb_id]

        return question_ids[:self.SUBSET_SIZE]
