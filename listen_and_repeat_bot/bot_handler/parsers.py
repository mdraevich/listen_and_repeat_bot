import os
import logging
import emoji


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.getLevelName(os.environ.get("LOGLEVEL", "WARNING"))
)
logger = logging.getLogger(__name__)


class Parsers:
    def __init__(self):
        self.__functions = {}

    def register(self, func):
        self.__functions[func.__name__] = func

    def run(self, parser):
        return self.__functions[parser]

    def len(self):
        return len(self.__functions)

parsers = Parsers()



@parsers.register
def parser_default(message_data):
    message_data_lines = message_data.split("\n")
    data = {
        "question": message_data_lines[0],
        "answers": [ el.strip() for el in message_data_lines[1].split("/") ],
        "examples": message_data_lines[2:]
    }
    
    return data


@parsers.register
def parser_english_expressions(message_data):
    message_data_raw = emoji.replace_emoji(message_data)
    message_data_lines = [el.strip() for el in message_data_raw.split("\n") if len(el)]

    if len(message_data_lines) < 4 or message_data_lines[2] != "Example:":
        logger.warning("Message format is broken, skip it")
        return None

    if len(message_data_lines[1]) >= 90:
        logger.warning("Too long answer, skip the sample")
        return None

    data = {
        "question": message_data_lines[0],
        "answers": message_data_lines[1:2],
        "examples": message_data_lines[3:4]
    }
    return data
