import json
import pytest
from question_db import QuestionDatabase


@pytest.fixture
def poll_channels_data():
    with open("tests/fixtures/poll_channels_data.json", "r") as file:
        data = json.loads(file.read())
    return data


def test_initial():
    assert True, "Initial test failed"


def test_question_db_update(poll_channels_data):
    question_db = QuestionDatabase()

    for channel in poll_channels_data["channels"]:
        channel_id = channel["channel_id"]
        channel_data = channel["data"]

        question_db.create_channel(channel_id)
        question_db.update_channel_posts(channel_id, channel_data)

        questions_in_channel = channel_data
        questions_in_db = question_db.get_question_ids(channel_id)

        assert len(questions_in_db) == len(questions_in_channel),\
               "Some questions are missed during importing"


def test_question_db_export_and_import(poll_channels_data):
    initial = QuestionDatabase()
    restored = QuestionDatabase()

    # create data to save
    for channel in poll_channels_data["channels"]:
        channel_id = channel["channel_id"]
        channel_data = channel["data"]

        initial.create_channel(channel_id)
        initial.update_channel_posts(channel_id, channel_data)

    restored.import_from_json(
        data=initial.export_to_json())

    # compare initial and restored
    assert initial.question_db == restored.question_db,\
           "Export & Import functions for QuestionDatabase do not work"