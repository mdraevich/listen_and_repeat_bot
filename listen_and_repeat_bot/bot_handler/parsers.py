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
