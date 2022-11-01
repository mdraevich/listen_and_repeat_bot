import json
import hashlib
import logging

"""
question_db = {
    channel_id: {
        channel_name: str
        channel_description: str
        channel_message_limit: int
        channel_polling_interval: int
        channel_is_private: bool
        questions: {
            question_id: {
                question: value (str),
                answers: value (set),
                examples: value (list)
            }
        }
    }
}
"""

class QuestionDatabase():
    QUESTIONS_KEY = "questions"


    def __init__(self):
        self.question_db = {}
        self.logger = logging.getLogger(__name__)


    def create_channel(self, channel_id):
        """
        returns:
            True - if channel_id is created
            False - if channel_id has been already created
        """

        if channel_id in self.question_db:
            return False
        else:
            self.question_db[channel_id] = {
                self.QUESTIONS_KEY: {}
            }
            return True

    
    def remove_channel(self, channel_id):
        """
        returns:
            True - if channel_id is deleted
            False - if channel_id doesn't exist 
                    so it can't be deleted
        """

        if channel_id in self.question_db:
            self.question_db.pop(channel_id)
            return True
        else:
            return False


    def update_channel_posts(self, channel_id, posts):
        """
        args:
            channel_id
            posts - list of messages (str),
                    example: ["hello\nworld", "test"]

        returns:
            False - channel_id is not presented in database,
                    should create it first
            True - if posts were parsed and questions were updated
        """

        if channel_id not in self.question_db:
            self.logger.error(f"channel_id={channel_id} is not "
                              f"presented in database")
            return False

        for post in posts:
            question = post["question"]
            answers = post["answers"]
            examples = post["examples"]

            # generate id from question, so question can't be duplicated in db
            try:
                question_id = hashlib.sha1(
                                    question.encode("utf-8")).hexdigest()
            except Exception as e:
                self.logger.exception(f"Can't generate hash for "
                                      f"channel_id={channel_id} "
                                      f"question={question} due to {e}")
                continue

            self.question_db[channel_id]\
                            [self.QUESTIONS_KEY][question_id] = {**post}

        return True


    def get_question_ids(self, channel_id):
        return list(self.question_db[channel_id][self.QUESTIONS_KEY].keys())


    def get_question_by_id(self, channel_id, question_id):
        return self.question_db[channel_id][self.QUESTIONS_KEY][question_id]


    def set_channel_metadata(self, channel_id, key, value):
        self.question_db[channel_id][key] = value


    def get_channel_metadata(self, channel_id, key):
        if key in self.question_db[channel_id]:
            return self.question_db[channel_id][key]
        else:
            return None


    def list_all_channels(self):
        return list(self.question_db.keys())


    def export_to_json(self):
        return json.dumps(self.question_db, indent=4, ensure_ascii=False)


    def import_from_json(self):
        pass

