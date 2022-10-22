import os
import time
import random
import getpass
import logging
from difflib import SequenceMatcher

from telethon.tl.patched import Message 
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

from poll_public_channel import PollPublicChannel


SIMILARITY_REQUIRED = 0.8
ERROR_MESSAGE = "⚠️ Internal error happened"
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


progress_db = ProgressDatabase(queue_class=ProgressQueueRandom)
question_db = QuestionDatabase()



def get_similarity(user_answer, correct_answer):
    return SequenceMatcher(None, user_answer, correct_answer).ratio()


def start(update, context):
    user_id = update.message.from_user.id

    progress_db.create_user(user_id)
    update.message.reply_text(send_phrase_to_learn(user_id), 
                              parse_mode=ParseMode.HTML)


def send_phrase_to_learn(user_id):
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
        question_db.get_question_ids(channel_link)
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

    question = question_db.get_question_by_id(channel_link, question_id)
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
        [InlineKeyboardButton(text=channel["name"], 
                              callback_data=channel["channel_id"])]
        for channel in get_channels() 
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

def get_channels():
    return [
        {
            "name": "Listen & Repeat | Phrases",
            "channel_id": "https://t.me/listen_repeat_phrases",
            "polling_interval": "120",
            "message_limit": "100"
        },
        {
            "name": "Listen & Repeat | Test",
            "channel_id": "https://t.me/listen_repeat_phrases",
            "polling_interval": "120",
            "message_limit": "100"
        }
    ]



if __name__ == "__main__":

    phone = os.environ.get("PHONE", None)
    api_key = os.environ.get("BOT_API_KEY", None)
    api_id = os.environ.get("API_ID", None)
    api_hash = os.environ.get("API_HASH", None)
    channel_link = get_channels()[0]["channel_id"]


    updater = Updater(api_key)

    dispatcher = updater.dispatcher
    updater.dispatcher.add_handler(CallbackQueryHandler(inline_callbacks))
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("learn", set_channel_to_learn))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command,
                                          check_translation))
    updater.start_polling()


    poll_channel = PollPublicChannel()

    # perform authentication
    auth_response = poll_channel.authenticate(
                        phone=phone,api_id=api_id, api_hash=api_hash)
    auth_code = auth_response[0]

    if auth_code == 0:  # already authenticated 
        pass

    elif auth_code == 1:  # phone confirmation is needed
        phone_auth_response = poll_channel.confirm_phone(
                                    phone, code=input("Enter code: "))
        phone_auth_code = phone_auth_response[0]

        if phone_auth_code == 0:  # authenticated, success
            pass
        
        elif phone_auth_code == 1:  # cloud password is needed
            poll_channel.confirm_cloud_password(
                password=getpass.getpass("Enter 2FA password: "))
        
        elif phone_auth_code == 10:  # phone is not registered
            exit()

    elif auth_code == 5:  # flood error
        exit()

    poll_channel.poll_channel(
        channel_id=channel_link, 
        message_limit=100
    )
    question_db.create_channel(channel_link)
    question_db.parse_channel_posts(
        channel_link,
        posts = [ 
            post.message
            for post in poll_channel.get_channel_posts(channel_link) 
            if isinstance(post, Message) 
        ]
    )

    updater.idle()
