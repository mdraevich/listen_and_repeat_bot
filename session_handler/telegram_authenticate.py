"""
describes a class that acts like a wrapper for telethon library
"""

import logging

from telethon.sync import TelegramClient
from telethon import errors



class TelegramAuthenticate():
    """
        class is a wrapper for telethon library to generate
        session file

        self.authenticate()         - inits an authentication process
        self.confirm_phone()        - performs code confirmation
        self.confirm_cloud_password - performs 2FA confirmation
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None


    def authenticate(self, phone, api_id, api_hash, **kwargs):
        """
        function accepts args:
            phone        - phone number for your account
            api_id       - see at https://core.telegram.org/api/obtaining_api_id
            api_hash     - see at https://core.telegram.org/api/obtaining_api_id
            kwargs       - dict for additional parameters
                filename: str       - filename to save current session
                session_name: str   - alias for a session in active sessions tab

        function returns a tuple:
            (0)               - user is authenticated using cache
            (1)               - user has to confirm phone by submitting code
            (5, seconds: int) - user has to wait for <seconds>
                                before sending a new request
        """

        self.client = TelegramClient(
            kwargs["filename"], api_id, api_hash,
            device_model=kwargs["session_name"])

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
                (0)  - code is correct and user is authorized
                (1)  - 2FA authorization is enabled, provide cloud password
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
        """
            function returns a tuple:
                (0)  - sign in is successful
        """

        self.client.sign_in(password=password)
        self.logger.info("Successfully signed in")
        return (0,)
