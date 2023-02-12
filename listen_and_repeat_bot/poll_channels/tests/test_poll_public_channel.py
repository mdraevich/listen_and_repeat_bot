from unittest.mock import Mock, patch

import pytest
from telethon import errors

from poll_public_channel import PollPublicChannel




def test_initial():
    assert True, "Initial test failed"


@pytest.mark.parametrize("connect_status,expected", [
    (True, (0,)), 
    (False, (1,)), 
    (RuntimeError(), (RuntimeError,))
])
def test_telegram_authentication(connect_status, expected, mocker):
    obj = PollPublicChannel()

    # mocking telegram client
    telegram_mocker = Mock()
    telegram_mocker.return_value = Mock()
    if isinstance(connect_status, Exception):
        telegram_mocker().connect.side_effect = connect_status
    else:
        telegram_mocker().is_user_authorized.return_value = connect_status
    mocker.patch("poll_public_channel.TelegramClient", telegram_mocker)

    try:
        auth_response = obj.authenticate(
                                        "listen_and_repeat.session",
                                        "api_id",
                                        "api_hash")
    except RuntimeError as exc:
        auth_response = (RuntimeError,)

    assert auth_response[0] == expected[0], "Failed"
