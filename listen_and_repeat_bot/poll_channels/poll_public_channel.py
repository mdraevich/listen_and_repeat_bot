import logging

from telethon.sync import TelegramClient
from telethon import errors



class PollPublicChannel():


    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.channels = {}
        self.client = None


    def authenticate(self, session_filename, api_id, api_hash):
        """
        function accepts args:
            session_filename - session filename for your account
            api_id           - see at https://core.telegram.org/api/obtaining_api_id
            api_hash         - see at https://core.telegram.org/api/obtaining_api_id

        function returns a tuple:
            (0)               - user is authenticated using cache
            (1)               - user has to confirm phone by submitting code
        """

        self.client = TelegramClient(session_filename, api_id, api_hash)
        self.client.connect()

        if self.client.is_user_authorized():
            self.logger.info("Successfully authenticated "
                             "using session file")
            return (0,)

        self.logger.info("Cannot sign in using provided session file")
        return (1,)




    def get_channel_posts(self, channel_id):
        """
        function returns:
            telethon.helpers.TotalList - messages for channel_id
            None                       - if no data is found for channel_id
        """

        if channel_id in self.channels:
            return self.channels[channel_id]
        else:
            return None


    async def poll_channel(self, channel_id, message_limit=100):
        """
        function returns a tuple:
            (0,) - polling is successfull
            (1,) - connection error during polling
            (5, seconds: int) - flood error, wait for <seconds>
        """
        try:
            self.channels[channel_id] = await self.client.get_messages(
                                        channel_id,
                                        limit=message_limit)

            self.logger.info("@%s has been polled "
                             "successfully, got "
                             "%s posts",
                             channel_id, len(self.channels[channel_id]))
            return (0,)

        except (ConnectionError, errors.FloodWaitError) as exc:

            if isinstance(exc, ConnectionError):
                self.logger.error("Network conntection Error, "
                                  "no messages received")
                return (1,)

            if isinstance(exc, errors.FloodWaitError):
                self.logger.exception("Too much requests, wait for "
                                      "%s second(s)!", exc.seconds)
                return (5, exc.seconds)
