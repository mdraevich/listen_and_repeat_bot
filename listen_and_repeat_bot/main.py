import os
import random
import logging
from difflib import SequenceMatcher

from telethon.tl.patched import Message 
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    Filters
)
from telegram import ParseMode

from progress_db import ProgressDatabase
from question_db import QuestionDatabase
from progress_queue_library import ProgressQueue, ProgressQueueRandom

from poll_public_channel import PollPublicChannel


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


progress_db = ProgressDatabase(queue_class=ProgressQueueRandom)
question_db = QuestionDatabase()




def is_similar_to(user_answer, correct_answer):
    return SequenceMatcher(None, user_answer, correct_answer).ratio() > 0.8


def start(update, context):
    user_id = update.message.from_user.id

    progress_db.create_user(user_id)
    progress_db.create_channel_progress(user_id, channel_link)

    update.message.reply_text(send_phrase_to_learn(user_id), 
                              parse_mode=ParseMode.HTML)

def send_phrase_to_learn(user_id):

    question_db.create_channel(channel_link)
    question_db.parse_channel_posts(
        channel_id = channel_link,
        posts = [ 
            post.message
            for post in poll_channel.messages 
            if isinstance(post, Message) 
        ]
    )

    queue_obj = progress_db.get_channel_progress(user_id, channel_link)

    queue_obj.update_questions(
        question_db.get_question_ids(channel_link)
    )

    question_id = queue_obj.next_question()
    question_obj = question_db.get_question_by_id(channel_link, question_id)
    
    question = question_obj["question"]
    if len(question_obj["examples"]) > 0:
        example = random.choice(question_obj["examples"])
    else:
        example = question

    return f"{example}\n\n🤔 ... <b>{question}</b>?"


def check_translation(update, context):
    user_id = update.message.from_user.id
    user_answer = update.message.text.lower()

    queue_obj = progress_db.get_channel_progress(user_id, channel_link)
    question_id = queue_obj.current_question()

    question = question_db.get_question_by_id(channel_link, question_id)
    answers = question["answers"]

    is_user_answer_correct = any([ 
        is_similar_to(user_answer, correct_answer)
        for correct_answer in answers
    ])

    formatted_answers = []
    for correct_answer in answers:
        if is_similar_to(user_answer, correct_answer):
            formatted_answers.append(f"<u><b>{correct_answer}</b></u>")
        else:
            formatted_answers.append(correct_answer)

    if is_user_answer_correct:
        update.message.reply_text(f"✅ {' / '.join(formatted_answers)}",
                                  parse_mode=ParseMode.HTML)
    else:
        update.message.reply_text(f"❌ {' / '.join(formatted_answers)}")

    update.message.reply_text(send_phrase_to_learn(user_id),
                              parse_mode=ParseMode.HTML)


def reset_learning_progress():
    pass


def set_learning_channel():
    pass


def show_learning_progress():
    pass



if __name__ == "__main__":

    phone = os.environ.get("PHONE", None)
    api_key = os.environ.get("BOT_API_KEY", None)
    api_id = os.environ.get("API_ID", None)
    api_hash = os.environ.get("API_HASH", None)
    channel_link = os.environ.get("CHANNEL", None)


    updater = Updater(api_key)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command,
                                          check_translation))

    updater.start_polling()

    poll_channel = PollPublicChannel(
                                    channel_link=channel_link,
                                    message_limit=100
                                    )

    if not poll_channel.authenticate(
                                    phone=phone,
                                    api_id=api_id,
                                    api_hash=api_hash
                                    ):
        poll_channel.confirm_phone(phone, code=input("Enter code: "))

    poll_channel.poll_channel()
    updater.idle()
