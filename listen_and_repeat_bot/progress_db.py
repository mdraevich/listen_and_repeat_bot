import logging

"""
progress_db = {
    user_id: {
        current_channel: channel_id
        channel_id: value (QuestionQueue)
        channel_id: value (QuestionQueue)
    }
}
"""



class ProgressDatabase():
    
    CUR_CHANNEL_KEY = "current_channel_id"

    def __init__(self, queue_class):
        self.logger = logging.getLogger(__name__)

        self.queue_class = queue_class
        self.progress_db = {}


    def create_user(self, user_id):
        """
        returns:
            True - if user_id was created
            False - if user_id is already presented in database
        """

        if user_id in self.progress_db:
            return False
        else:
            self.progress_db[user_id] = {
                CUR_CHANNEL_KEY: None
            }
            self.logger.info(f"{user_id} was created in database")
            return True


    def delete_user(self, user_id):
        """
        returns:
            True - if user_id was deleted
            False - if user_id is not presented in database
        """

        if user_id in self.progress_db:
            self.progress_db.pop(user_id)
            self.logger.info(f"{user_id} was deleted from database")
            return True
        else:
            return False


    def create_channel_progress(self, user_id, channel_id):
        """
        function returns:
            False - user_id:channel_id is already presented in database
            True - user_id:channel_id was created in database
        """

        self.create_user(user_id)

        if channel_id in self.progress_db[user_id]:
            return False

        self.progress_db[user_id][channel_id] = self.queue_class()
        self.logger.info(f"{user_id}:{channel_id} was created in database")
        return True


    def delete_channel_progress(self, user_id, channel_id):
        """
        function returns:
            False - user_id:channel_id is not presented in database
            False - user_id:channel_id was deleted from database
        """

        if user_id not in self.progress_db:
            return False

        if channel_id not in self.progress_db[user_id]:
            return False

        self.progress_db[user_id].pop(channel_id)
        self.logger.info(f"{user_id}:{channel_id} was deleted from database")
        return True


    def get_current_channel_of_user(self, user_id):
        """
        function returns a tuple:
            (0, value) - channel_id value for user_id, 
                         value is None (if user has no channel_id)
                         otherwise type(value) is str
            (-1, None) - user_id is absent in database
        """

        if user_id in self.progress_db:
            return (0, self.progress_db[user_id][self.CUR_CHANNEL_KEY])
        else:
            return (-1, None)


    def set_current_channel_of_user(self, user_id, channel_id):
        """
        function returns:
            True - channel_id is saved for user_id
            False - user_id is absent in database, cannot save channel_id
        """

        if user_id in self.progress_db:
            self.progress_db[user_id][self.CUR_CHANNEL_KEY] = channel_id
            return True
        else: 
            return False 


    def get_channel_progress(self, user_id, channel_id):
        """
        function returns a tuple of:
            (0, value) - successful query, type(value) is ProgressQueue obj
            (1, None) - user_id is absent in database
            (2, None) - channel_id for user_id is absent in database 
        """

        if user_id not in self.progress_db:
            return (1, None)

        if channel_id not in self.progress_db[user_id]:
            return (2, None)

        return (0, self.progress_db[user_id][channel_id])


    def export_to_json(self):
        pass


    def import_from_json(self):
        pass

