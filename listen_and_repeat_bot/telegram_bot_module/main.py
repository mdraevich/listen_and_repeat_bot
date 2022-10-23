import os
import time
import json
import random
import getpass
import logging
import urllib.request
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


progress_db = ProgressDatabase(queue_class=ProgressQueueRandom)
question_db = QuestionDatabase()


def update_question_db():
    contents = urllib.request.urlopen("http://localhost:8080/data").read()
    data = json.loads(contents)

    for channel in data["channels"]:
        channel_id = channel["channel_id"]

        question_db.create_channel(channel_id)

        question_db.set_channel_metadata(channel_id, 
                                        "channel_name", 
                                        channel["name"])
        question_db.parse_channel_posts(
            channel_id,
            posts = channel["data"]
        )


def get_similarity(user_answer, correct_answer):
    return SequenceMatcher(None, user_answer, correct_answer).ratio()


def start(update, context):
    user_id = update.message.from_user.id

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
    else:
        example = question

    return f"{example}\n\n🤔 ... <b>{question}</b>?"


def check_translation(update, context):
    user_id = update.message.from_user.id
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
    user_id = update.callback_query.from_user.id
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
