import logging

from telethon.sync import TelegramClient
from telethon import errors



class PollPublicChannel():


    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.channels = {}
        self.client = None


    def authenticate(self, phone, api_id, api_hash):
        """
        function accepts args:
            phone - id for your account
            api_id - see at https://core.telegram.org/api/obtaining_api_id
            api_hash - see at https://core.telegram.org/api/obtaining_api_id

        function returns a tuple:
            (0) - user is authenticated using cache
            (1) - user has to confirm phone by submitting code
            (5, seconds: int) - user has to wait for <seconds>
                                   before sending a new request
        """

        self.client = TelegramClient(phone, api_id, api_hash)

        try:
            self.client.connect()

            if self.client.is_user_authorized():
                self.logger.info("User %s is authenticated using "
                                 "cache: %s",
                                 phone, self.client.get_me().username)
                return (0,)

            self.logger.info("Send confirmation code to %s", phone)
            self.client.send_code_request(phone)
            return (1,)

        except errors.FloodWaitError as exc:
            self.logger.exception("Too much requests, wait for "
                                  "%s second(s)!", exc.seconds)
            return (5, exc.seconds)


    def confirm_phone(self, phone, code):
        """
            function returns a tuple:
                (0) - code is correct and user is authorized
                (1) - 2FA authorization is enabled, provide password
                        via PollPublicChannel.confirm_cloud_password method
                (10) - cannot sign in using specified phone number
        """

        try:
            self.client.sign_in(phone, code)
            self.logger.info("Successfully signed in using phone=%s", phone)
            return (0,)

        except (errors.SessionPasswordNeededError,
                errors.PhoneNumberUnoccupiedError) as exc:
            if isinstance(exc, errors.SessionPasswordNeededError):
                self.logger.info("Password is required to "
                                 "complete authorization")
                return (1,)

            if isinstance(exc, errors.PhoneNumberUnoccupiedError):
                self.logger.exception("Cannot sign in using phone=%s, "
                                      "phone number is not registered", phone)
                return (10,)

        return (None,)


    def confirm_cloud_password(self, password):
        self.client.sign_in(password=password)
        self.logger.info("Successfully signed in")
        return (0,)


    def get_channel_posts(self, channel_id):
        """
        function returns:
            telethon.helpers.TotalList - messages for channel_id
            None - if no data is found for channel_id
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
