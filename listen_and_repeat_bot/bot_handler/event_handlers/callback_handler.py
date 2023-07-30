import logging


logger = logging.getLogger(__name__)


class CallbackRouting():
    """
    USAGE:
        place decorator before function (0 - unique func number):
        
        @callback_routing.register(0)
        def helloworld(update, context, *args):
            logger.debug("helloworld is called")

    """

    def __init__(self): 
        self.__functions = {}

    def handle(self, update, context):
        callback_args = update.callback_query.data.split(",")
        update.callback_query.answer()
        func_id = int(callback_args[0])
        func_args = callback_args[1:]
        self._route(func_id)(update, context, *func_args)

    def _route(self, func_id):
        return self.__functions[func_id]

    def register(self, func_id):
        def _register_by_id(func):
            self.__functions[func_id] = func
        return _register_by_id

    def len(self):
        return len(self.__functions)


callback_routing = CallbackRouting()