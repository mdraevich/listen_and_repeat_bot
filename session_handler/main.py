"""
creates a session file in ../secrets directory 
to let you mount the file to a docker container
"""

import os
import sys
import getpass

from telegram_authenticate import TelegramAuthenticate


def interactive_authentication():
    """
    provides an interactive way of telegram authentication
    """

    auth_handler = TelegramAuthenticate()

    # perform authentication
    return_code = auth_handler.authenticate(
                        phone=phone,
                        api_id=api_id,
                        api_hash=api_hash,
                        filename=session_filename,
                        session_name=session_name)

    if return_code[0] == 0:
        # already authenticated
        print("Already authenticated, exiting...")

    elif return_code[0] == 1:
        # phone confirmation is needed
        confirm_phone_code = auth_handler.confirm_phone(
                                    phone, code=input("Enter code: "))

        if confirm_phone_code[0] == 0:
            # authenticated, success
            print("Authenticated successfully, exiting...")

        elif confirm_phone_code[0] == 1:
            # cloud password is needed
            confirm_cloud_pass = auth_handler.confirm_cloud_password(
                                    getpass.getpass("Enter 2FA password: "))

            if confirm_cloud_pass[0] == 0:
                # authenticated with 2FA, success
                print("Authenticated successfully, exiting...")

            else:
                # 2FA pass authentication is failed
                print("Authentication failure, exiting...")

        elif confirm_phone_code[0] == 10:
            # phone is not registered
            print("The specified phone is not registered.")

    elif return_code[0] == 5:
        # flood error
        print(f"FloodWaitError exception is raised, "
              f"wait for {return_code[1]} seconds.")


if __name__ == '__main__':

    phone = os.environ.get("PHONE", None)
    api_id = os.environ.get("API_ID", None)
    api_hash = os.environ.get("API_HASH", None)
    session_name = os.environ.get("SESSION_NAME",
                                  "Listen & Repeat")
    session_filename = os.environ.get("SESSION_FILENAME",
                                      "secrets/listen_and_repeat.session")

    if None in (phone, api_id, api_hash):
        print("Not all required parameters are provided. "
              "Refer to README.md for more details.")
        sys.exit(0)

    interactive_authentication()
