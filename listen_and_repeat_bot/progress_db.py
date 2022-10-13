import logging

"""
progress_db = {
    user_id: {
        channel_id: value (QuestionQueue)
    }
}
"""



class ProgressDatabase():

    def __init__(self, queue_class):
        self.queue_class = queue_class
        self.progress_db = {}
        self.logger = logging.getLogger(__name__)


    def create_user(self, user_id):
        """
        returns:
            True - if user_id is created
            False - if user_id is already presented in database
        """

        if user_id in self.progress_db:
            return False
        else:
            self.progress_db[user_id] = {}
            return True


    def delete_user(self, user_id):
        """
        returns:
            True - if user_id was deleted
            False - if user_id is not presented in database
        """

        if user_id in self.progress_db:
            self.progress_db.pop(user_id)
            return True
        else:
            return False


    def create_channel_progress(self, user_id, channel_id):
        if user_id not in self.progress_db:
            self.logger.error(f"{user_id} is not presented in database")
            return False

        if channel_id in self.progress_db[user_id]:
            self.logger.error(f"{channel_id} is already presented in "
                              f"database, cannot create it")
            return False

        self.progress_db[user_id][channel_id] = self.queue_class()
        return True


    def delete_channel_progress(self, user_id, channel_id):
        if user_id not in self.progress_db:
            return False

        if channel_id not in self.progress_db[user_id]:
            return False

        self.progress_db[user_id].pop(channel_id)
        return True


    def get_channel_progress(self, user_id, channel_id):
        if user_id not in self.progress_db:
            return None

        if channel_id not in self.progress_db[user_id]:
            return None


        return self.progress_db[user_id][channel_id]


    def export_to_json(self):
        pass


    def import_from_json(self):
        pass

