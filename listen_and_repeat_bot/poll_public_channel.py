import os
import time
import logging


from telethon.sync import TelegramClient
from telethon import errors



class PollPublicChannel():


    def __init__(self, channel_link, message_limit=10):
        self.logger = logging.getLogger(__name__)

        self.channel_link = channel_link
        self.message_limit = message_limit
        self.messages = []
        self.client = None


    @property
    def channel_link(self):
        return self._channel_link


    @channel_link.setter
    def channel_link(self, value):
        if isinstance(value, str):
            self._channel_link = value
        else:
            raise ValueError


    @property
    def message_limit(self):
        return self._message_limit


    @message_limit.setter
    def message_limit(self, value):
        if isinstance(value, int) and value > 0:
            self._message_limit = value
        else:
            raise ValueError


    @property
    def messages(self):
        return self._messages


    @messages.setter
    def messages(self, value):
        if isinstance(value, list):
            self._messages = value
        else:
            raise ValueError


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

        if isinstance(self.client, TelegramClient) and\
                      self.client.is_connected():
           self.client.disconnect()

        self.client = TelegramClient(phone, api_id, api_hash)

        try:
            self.client.connect()
            
            if self.client.is_user_authorized():
                self.logger.info(f"User {phone} is authenticated using "
                                 f"cache: @{self.client.get_me().username}")
                return (0,)
            else:
                self.logger.info(f"Send confirmation code to {phone}")
                self.client.send_code_request(phone)
                return (1,)

        except errors.FloodWaitError as e:
            self.logger.exception(f"Too much requests, wait for "
                                  f"{e.seconds} second(s)!")
            return (5, e.seconds)


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
            self.logger.info(f"Successfully signed in using phone={phone}")
            return (0,)

        except (errors.SessionPasswordNeededError,
                errors.PhoneNumberUnoccupiedError) as e:
            if isinstance(e, errors.SessionPasswordNeededError):
                self.logger.info("Password is required to "
                                 "complete authorization")
                return (1,)

            if isinstance(e, errors.PhoneNumberUnoccupiedError):
                self.logger.exception(f"Cannot sign in using phone={phone}, "
                                      f"phone number is not registered")
                return (10,)


    def confirm_cloud_password(self, password):
        self.client.sign_in(password=password)
        self.logger.info(f"Successfully signed in")
        return 0


    def poll_channel(self):
        """
        function returns a tuple:
            (0,) - polling is successfull
            (1,) - connection error during polling
            (5, seconds: int) - flood error, wait for <seconds>
        """
        try:
            self.messages = self.client.get_messages(
                                        self.channel_link,
                                        limit=self.message_limit)

            self.logger.info(f"Polling is done successfully, "
                             f"got {len(self.messages)} posts")
            return (0,)

        except (ConnectionError, errors.FloodWaitError) as e:
            
            if isinstance(e, ConnectionError):
                self.logger.error("Network conntection Error, "
                                  "no messages received")
                return (1,)

            if isinstance(e, errors.FloodWaitError):
                self.logger.exception(f"Too much requests, wait for "
                                      f"{e.seconds} second(s)!")
                return (5, e.seconds)


# if __name__ == "__main__":

#     logger = logging.getLogger(__name__)
#     logger.setLevel(logging.DEBUG)
#     logger.addHandler(logging.StreamHandler())

#     phone = input("Enter phone: ")
#     api_id = os.environ.get("API_ID", None)
#     api_hash = os.environ.get("API_HASH", None)
#     channel_link = os.environ.get("CHANNEL", None)

#     poll_channel = PollPublicChannel(channel_link=channel_link)
    
#     if not poll_channel.authenticate(
#                                     phone=phone,
#                                     api_id=api_id,
#                                     api_hash=api_hash
#                                     ):
#         poll_channel.confirm_phone(phone, code=input("Enter code: "))

#     poll_channel.poll_channel()