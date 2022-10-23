import json
import hashlib
import logging

"""
question_db = {
    channel_id: {
        question_id: {
            question: value (str),
            answers: value (set),
            examples: value (list)
        }
    }
}
"""

class QuestionDatabase():

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
            self.question_db[channel_id] = {}
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


    def parse_channel_posts(self, channel_id, posts):
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
            message_parts = [ line.strip() for line in post.split("\n") ]
            
            if len(message_parts) < 2:
                self.logger.warning(f"Message is ignored due to incorrect "
                                    f"format, {channel_id}: {post[:20]}")
                continue

            question = message_parts[0].lower()
            answers = [ 
                        answer.strip().lower()
                        for answer in message_parts[1].split("/") 
                      ]
            examples = [
                            example.strip()
                            for example in message_parts[2:]
                       ]

            # generate id from question, so question can't be duplicated in db
            try:
                question_id = hashlib.sha1(
                                    question.encode("utf-8")).hexdigest()
            except Exception as e:
                self.logger.exception(f"Can't generate hash for "
                                      f"channel_id={channel_id} "
                                      f"question={question} due to {e}")
                continue

            self.question_db[channel_id][question_id] = {
                "question": question,
                "answers": answers,
                "examples": examples
            }

        return True


    def get_question_ids(self, channel_id):
        return list(self.question_db[channel_id].keys())


    def get_question_by_id(self, channel_id, question_id):
        return self.question_db[channel_id][question_id]


    def export_to_json(self):
        return json.dumps(self.question_db, indent=4, ensure_ascii=False)


    def import_from_json(self):
        pass

