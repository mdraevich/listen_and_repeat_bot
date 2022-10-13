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
        
        function returns:
            True - user is authenticated using cache
            False - user has to confirm phone by submitting code
            None - exception raised during execution
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
                return True
            else:
                self.logger.info(f"Send confirmation code to {phone}")
                self.client.send_code_request(phone)
                return False

        except Exception as e:
            self.logger.exception(f"Exception={type(e)} is raised "
                                   "during authentication")

            if type(e) is errors.FloodWaitError:
                self.logger.exception(f"Too much requests, wait for "
                                      f"{e.seconds} second(s)!")

            return None


    def confirm_phone(self, phone, code):
        """
            function returns:
                True - code is correct and user is authorized
                False - Exception occurs, confirmation is failed
        """

        try:
            self.client.sign_in(phone, code)
            return True

        except Exception as e:
            self.logger.exception(f"Exception={type(e)} is raised "
                                  f"during authentication")

            if type(e) is errors.SessionPasswordNeededError:    
                self.logger.exception("Password is required to "
                                      "complete authorization, "
                                      "but 2FA is not supported now.")
            return False


    def poll_channel(self):
        try:
            self.messages = self.client.get_messages(
                                        self.channel_link,
                                        limit=self.message_limit)

            self.logger.info(f"Polling is done successfully, "
                             f"got {len(self.messages)} posts")

        except Exception as e:
            if type(e) is errors.FloodWaitError:
                self.logger.exception(f"Too much requests, wait for "
                                      f"{e.seconds} second(s)!")

            if type(e) is KeyboardInterrupt:
                self.logger.exception("Ctrl+C is fired, please wait for "
                                      "a while until the bot stops.")

            self.logger.warning(f"Cannot poll channel due to {type(e)}")



if __name__ == "__main__":

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

    phone = input("Enter phone: ")
    api_id = os.environ.get("API_ID", None)
    api_hash = os.environ.get("API_HASH", None)
    channel_link = os.environ.get("CHANNEL", None)

    poll_channel = PollPublicChannel(channel_link=channel_link)
    
    if not poll_channel.authenticate(
                                    phone=phone,
                                    api_id=api_id,
                                    api_hash=api_hash
                                    ):
        poll_channel.confirm_phone(phone, code=input("Enter code: "))

    poll_channel.poll_channel()