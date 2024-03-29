import os
import sys
import time
import json
import random
import getpass
import logging

import yaml
from urllib import request, error
from difflib import SequenceMatcher

from jinja2 import Environment, BaseLoader
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
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)

from progress_db import ProgressDatabase
from question_db import QuestionDatabase
from progress_queue_library import (
    ProgressQueue, 
    ProgressQueueRandom,
    ProgressQueuePriorityRandom,
    ProgressQueuePriorityRandomLimited,
    ProgressQueueLearnModesAndSubsets
)
from parsers import parsers
from event_handlers import callback_handler


QUESTIONS_DB_FILE = os.environ.get("QUESTIONS_DB_FILE", 
                                   "./data/questions.db.json")
USERS_DB_FILE = os.environ.get("USERS_DB_FILE",
                               "./data/users.db.json")
SIMILARITY_REQUIRED = 0.8


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.getLevelName(os.environ.get("LOGLEVEL", "WARNING"))
)
logger = logging.getLogger(__name__)


progress_db = ProgressDatabase(
                queue_class=ProgressQueueLearnModesAndSubsets)
question_db = QuestionDatabase()
bonus_db = {}

db_list = [
    (question_db, QUESTIONS_DB_FILE),
    (progress_db, USERS_DB_FILE)]



def parse_answers_file(filename):
    try:
        with open(filename, "r") as file:
            return yaml.safe_load(file)
    except (yaml.YAMLError, OSError) as exc:
        if isinstance(exc, OSError):
            print("Cannot read configuration file, "
                  "check path and permissions")
        if isinstance(exc, yaml.YAMLError):
            print("Config file has incorrect format, "
                  "cannot parse config options")
        return None


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


def random_answer(channel_id):
    random_question = random.choice(question_db.get_question_ids(channel_id))
    question_obj = question_db.get_question_by_id(channel_id, random_question)
    return random.choice(question_obj["answers"])


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

        formatted_data = []
        for entry in channel["posts"]:
            formatted_entry = parsers.run(channel["tags"]["parser"])(entry["data"])
            if formatted_entry is not None:
                formatted_data.append(formatted_entry)
        
        question_db.update_channel_posts(
            channel_id,
            formatted_data)
    save_data()
    return (True, len(data["channels"]))


def get_similarity(user_answer, correct_answer):
    return SequenceMatcher(None, user_answer, correct_answer).ratio()


def help_handler(update, context):
    user_id = str(update.message.from_user.id)
    lang_code = str(update.message.from_user.language_code)
    update.message.reply_text(answers["help"][lang_code],
                              parse_mode=ParseMode.HTML)

def start(update, context):
    user_id = str(update.message.from_user.id)
    lang_code = str(update.message.from_user.language_code)
    answer = answers["hello"][lang_code]

    if progress_db.create_user(user_id):
        update.message.reply_text(answer, 
                                  parse_mode=ParseMode.HTML)
        logger.info(f"new user has been created, user_id={user_id}")
    else:
        send_phrase_to_learn(update, context)


def send_phrase_to_learn(update, context, from_callback=False):
    # temporary solution
    update_question_db()

    if from_callback:
        user_id = str(update.callback_query.from_user.id)
        lang_code = str(update.callback_query.from_user.language_code)
    else:
        user_id = str(update.message.from_user.id)
        lang_code = str(update.message.from_user.language_code)

    exit_code, channel_id = progress_db.get_current_channel_of_user(user_id)
    if exit_code != 0:
        return answers["error"][lang_code]
    if channel_id is None:
        return answers["hello"][lang_code]

    exit_code, queue_obj = progress_db.get_channel_progress(
                           user_id, channel_id)

    if exit_code != 0:
        return answers["error"][lang_code]

    queue_obj.update_questions(
        question_db.get_question_ids(channel_id)
    )

    question_id = queue_obj.next_question()
    question_obj = question_db.get_question_by_id(channel_id, question_id)
    reply_with = f"🤔 ... <b>{question_obj['question']}</b>?"

    buttons = []
    buttons.append([KeyboardButton(text=random.choice(question_obj["answers"]))])
    for item in [ random_answer(channel_id) for i in range(3) ]:
        buttons.append([KeyboardButton(text=item)])

    random.shuffle(buttons)
    buttons.append([KeyboardButton(text=answers["no_user_answer"][lang_code])])

    keyboard = ReplyKeyboardMarkup(buttons)

    if from_callback:
        update.callback_query.message.reply_text(
            reply_with, 
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard)
    else:
        update.message.reply_text(reply_with, parse_mode=ParseMode.HTML,
                                  reply_markup=keyboard)



def check_translation(update, context):
    user_id = str(update.message.from_user.id)
    lang_code = str(update.message.from_user.language_code)
    user_answer = update.message.text.lower()

    exit_code, channel_id = progress_db.get_current_channel_of_user(user_id)
    if exit_code != 0:
        return answers["error"][lang_code]
    if channel_id is None:
        return answers["hello"][lang_code]

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

    answer_template = Environment(loader=BaseLoader()).from_string(
                                answers["user_answer_feedback"][lang_code])
    answer_render = answer_template.render({
        "is_answer_correct": is_user_answer_correct,
        "answers": correct_answers[:3],
        "example": random.choice(question["examples"]) \
                            if len(question["examples"]) else "",
        "tags": ["think-of-an-example"]

    })

    if user_id not in bonus_db:
        bonus_db[user_id] = {}

    if question_id not in bonus_db[user_id]:
        bonus_db[user_id][question_id] = 0

    if is_user_answer_correct:
        # answer is correct
        queue_obj.change_question_progress(question_id, 15 + bonus_db[user_id][question_id])
        logger.debug("Change question=%s/%s/%s progress by value=%s", 
                     user_id, channel_id, question_id, 15 + bonus_db[user_id][question_id])
        
        bonus_db[user_id][question_id] += max(3, bonus_db[user_id][question_id] // 3)
        update.message.reply_text(answer_render, parse_mode=ParseMode.HTML)
    else:
        # answer is incorrect
        queue_obj.change_question_progress(question_id, -35)
        logger.debug("Change question=%s/%s/%s progress by value=%s", 
                     user_id, channel_id, question_id, -35)
        
        bonus_db[user_id][question_id] = 0
        update.message.reply_text(answer_render, parse_mode=ParseMode.HTML)

    send_phrase_to_learn(update, context)



def reset_learning_progress(update, context):
    user_id = str(update.message.from_user.id)
    lang_code = str(update.message.from_user.language_code)

    exit_code, channel_id = progress_db.get_current_channel_of_user(user_id)
    if exit_code != 0:
        return answers["error"][lang_code]
    if channel_id is None:
        return answers["hello"][lang_code]

    progress_db.delete_channel_progress(user_id, channel_id)
    progress_db.create_channel_progress(user_id, channel_id)

    update.message.reply_text(
        answers["reset_progress_info"][lang_code].format(channel_id))



def set_channel_to_learn(update, context):
    # temporary solution
    update_question_db()

    lang_code = str(update.message.from_user.language_code)
    answer = answers["select_channel"][lang_code]


    buttons = [
        [InlineKeyboardButton(
            text=question_db.get_channel_metadata(channel_id, "channel_name"), 
            callback_data=f"0,{channel_id}")]
        for channel_id in question_db.list_all_channels()
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    update.message.reply_text(answer, reply_markup=keyboard)


@callback_handler.callback_routing.register(0)
def select_channel_to_learn(update, context, channel_id):
    user_id = str(update.callback_query.from_user.id)
    lang_code = str(update.callback_query.from_user.language_code)

    answer = answers["channel_selected"][lang_code]
    
    progress_db.create_channel_progress(user_id, channel_id)
    if progress_db.set_current_channel_of_user(user_id, channel_id):
        update.callback_query.edit_message_text(text=answer)
    else:
        update.callback_query.edit_message_text(
                              text=answers["error"][lang_code])
    send_phrase_to_learn(update, context, from_callback=True)


@callback_handler.callback_routing.register(1)
def ignore_question(update, context, question_id):
    user_id = str(update.callback_query.from_user.id)
    lang_code = str(update.callback_query.from_user.language_code)
    answer = answers["ignore_question_success"][lang_code]
    
    exit_code, channel_id = progress_db.get_current_channel_of_user(user_id)
    exit_code, queue_obj = progress_db.get_channel_progress(
                               user_id, channel_id)
    queue_obj.change_question_progress(question_id, 200)
    update.callback_query.delete_message()
    send_phrase_to_learn(update, context, from_callback=True)


def show_learning_progress(update, context):
    user_id = str(update.message.from_user.id)
    lang_code = str(update.message.from_user.language_code)

    exit_code, channel_id = progress_db.get_current_channel_of_user(user_id)
    if exit_code != 0:
        update.message.reply_text(answers["error"][lang_code],
                  parse_mode=ParseMode.HTML)
    if channel_id is None:
        update.message.reply_text(answers["hello"][lang_code],
                          parse_mode=ParseMode.HTML)

    exit_code, queue_obj = progress_db.get_channel_progress(
                           user_id, channel_id)

    good_amount = medium_amount = low_amount = ignored_amount = 0
    for value in queue_obj.get_progress().values():
        if value <= 20:
            low_amount += 1
        if 20 <= value <= 60:
            medium_amount += 1
        if 60 <= value:
            good_amount += 1
    progress_answer = answers["show_progress"][lang_code].format(
            question_db.get_channel_metadata(channel_id, "channel_name"),
            good_amount, medium_amount,
            low_amount, ignored_amount)
    update.message.reply_text(progress_answer,
                              parse_mode=ParseMode.HTML)


def show_version_info(update, context):
    git_version = os.environ.get("GIT_VERSION", "unknown-version")
    update.message.reply_text(git_version, parse_mode=ParseMode.HTML)     


if __name__ == "__main__":

    api_key = os.environ.get("BOT_API_KEY", None)
    poll_channel_url = os.environ.get("POLL_CHANNELS_URL", None)
    answers_file = os.environ.get("ANSWERS_FILE", None)

    if answers_file is None:
        print("specify ANSWERS_FILE variable")
        sys.exit(1)

    if api_key is None:
        print("specify BOT_API_KEY variable")
        sys.exit(1)

    if poll_channel_url is None:
        print("specify POLL_CHANNELS_URL variable")
        sys.exit(1)

    answers = parse_answers_file(answers_file)["answers"]

    restore_data()
    update_question_db()

    updater = Updater(api_key)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(
        CallbackQueryHandler(callback_handler.callback_routing.handle)
    )
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_handler))
    dispatcher.add_handler(CommandHandler("progress", show_learning_progress))
    dispatcher.add_handler(CommandHandler("learn", set_channel_to_learn))
    dispatcher.add_handler(CommandHandler("reset", reset_learning_progress))
    dispatcher.add_handler(CommandHandler("version", show_version_info))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command,
                                          check_translation))
    updater.start_polling()
    updater.idle()
