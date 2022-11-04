import os
import sys
import time
import json
import random
import getpass
import logging

from urllib import request, error
from difflib import SequenceMatcher

from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    CallbackQueryHandler,
    Filters
)
from telegram import (
    ParseMode,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from progress_db import ProgressDatabase
from question_db import QuestionDatabase
from progress_queue_library import ProgressQueue, ProgressQueueRandom


QUESTIONS_DB_FILE = "./data/questions.db.json"
USERS_DB_FILE = "./data/users.db.json"

SIMILARITY_REQUIRED = 0.8
ERROR_MESSAGE = "⚠️ Server error, contact @mdraevich"
HELLO_MESSAGE = """
Hello ✌️
This bot can help you to improve your language vocabulary.
In order to begin, select a channel to learn phrases from.

You can also publish your own channel to read phrases from.
Feel free to contact me @mdraevich.

📦 <b>To select a channel</b>: /learn 
"""

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


progress_db = ProgressDatabase(queue_class=ProgressQueueRandom)
question_db = QuestionDatabase()

db_list = [
    (question_db, QUESTIONS_DB_FILE),
    (progress_db, USERS_DB_FILE)]


def save_data():
    for obj, filename in db_list:
        with open(filename, "w") as file:
            file.write(obj.export_to_json())
            logger.info("saved %s bytes to %s",
                        sys.getsizeof(obj), filename)


def restore_data():
    for obj, filename in db_list:
        try:
            with open(filename, "r") as file:
                obj.import_from_json(file.read())
                logger.info("restored %s bytes from %s",
                            sys.getsizeof(obj), filename)

        except FileNotFoundError as exc:
            logger.warning("Cannot find filename=%s to restore data",
                           filename)


def update_question_db():
    try:
        contents = request.urlopen(poll_channel_url).read()
        data = json.loads(contents)
    except (ConnectionError, error.URLError) as exc:
        return (False, 0)

    for channel in data["channels"]:
        channel_id = channel["channel_id"]
        question_db.create_channel(channel_id)

        question_db.set_channel_metadata(channel_id, 
                                        "channel_name", 
                                        channel["name"])
        question_db.update_channel_posts(
            channel_id,
            channel["data"])
    save_data()
    return (True, len(data["channels"]))


def get_similarity(user_answer, correct_answer):
    return SequenceMatcher(None, user_answer, correct_answer).ratio()


def start(update, context):
    user_id = str(update.message.from_user.id)

    if progress_db.create_user(user_id):
        update.message.reply_text(HELLO_MESSAGE, 
                                  parse_mode=ParseMode.HTML)
        logger.info(f"new user has been created, user_id={user_id}")
    else:
        update.message.reply_text(send_phrase_to_learn(user_id),
                                  parse_mode=ParseMode.HTML)


def send_phrase_to_learn(user_id):
    # temporary solution
    update_question_db()

    exit_code, channel_id = progress_db.get_current_channel_of_user(user_id)
    if exit_code != 0:
        return ERROR_MESSAGE
    if channel_id is None:
        return f"Please, select a channel by /learn"

    exit_code, queue_obj = progress_db.get_channel_progress(
                           user_id, channel_id)

    if exit_code != 0:
        return ERROR_MESSAGE

    queue_obj.update_questions(
        question_db.get_question_ids(channel_id)
    )

    question_id = queue_obj.next_question()
    question_obj = question_db.get_question_by_id(channel_id, question_id)
    
    question = question_obj["question"]
    if len(question_obj["examples"]) > 0:
        example = random.choice(question_obj["examples"])
        return f"{example}\n\n🤔 ... <b>{question}</b>?"
    else:
        return f"🤔 ... <b>{question}</b>?"



def check_translation(update, context):
    user_id = str(update.message.from_user.id)
    user_answer = update.message.text.lower()

    exit_code, channel_id = progress_db.get_current_channel_of_user(user_id)
    if exit_code != 0:
        return ERROR_MESSAGE
    if channel_id is None:
        return f"Please, select a channel by /learn"

    exit_code, queue_obj = progress_db.get_channel_progress(
                           user_id, channel_id)
    question_id = queue_obj.current_question()

    question = question_db.get_question_by_id(channel_id, question_id)
    correct_answers = question["answers"]


    answers_similarity = [ 
        (get_similarity(user_answer, answer), idx)
        for (idx, answer) in enumerate(correct_answers)
    ]
    max_similar_value, max_similar_idx = max(answers_similarity)
    is_user_answer_correct = max_similar_value > SIMILARITY_REQUIRED

    formatted_answers = []
    for (idx, answer) in enumerate(correct_answers):
        if is_user_answer_correct and idx == max_similar_idx:
            formatted_answers.append(f"<u><b>{answer}</b></u>")
        else:
            formatted_answers.append(answer)

    if is_user_answer_correct:
        # answer is correct
        update.message.reply_text(f"✅ {' / '.join(formatted_answers)}",
                                  parse_mode=ParseMode.HTML)
    else:
        # answer is incorrect
        update.message.reply_text(f"❌ {' / '.join(formatted_answers)}")

    update.message.reply_text(send_phrase_to_learn(user_id),
                              parse_mode=ParseMode.HTML)


def reset_learning_progress():
    pass


def set_channel_to_learn(update, context):
    # temporary solution
    update_question_db()

    buttons = [
        [InlineKeyboardButton(
            text=question_db.get_channel_metadata(channel_id, "channel_name"), 
            callback_data=channel_id)]
        for channel_id in question_db.list_all_channels()
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    update.message.reply_text("Select from the following", 
                              reply_markup=keyboard)


def inline_callbacks(update, context):
    user_id = str(update.callback_query.from_user.id)
    channel_id = update.callback_query.data

    update.callback_query.answer()
    
    progress_db.create_channel_progress(user_id, channel_id)
    if progress_db.set_current_channel_of_user(user_id, channel_id):
        update.callback_query.edit_message_text(
                              text="Your channel is updated.\n"
                                   "Run /start")
    else:
        update.callback_query.edit_message_text(
                              text=ERROR_MESSAGE)


def show_learning_progress():
    pass


if __name__ == "__main__":

    api_key = os.environ.get("BOT_API_KEY", None)
    poll_channel_url = os.environ.get("POLL_CHANNELS_URL", None)

    if api_key is None:
        print("specify BOT_API_KEY variable")
        sys.exit(1)

    if poll_channel_url is None:
        print("specify POLL_CHANNELS_URL variable")
        sys.exit(1)


    restore_data()
    update_question_db()

    updater = Updater(api_key)

    dispatcher = updater.dispatcher
    updater.dispatcher.add_handler(CallbackQueryHandler(inline_callbacks))
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("learn", set_channel_to_learn))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command,
                                          check_translation))
    updater.start_polling()
    updater.idle()
