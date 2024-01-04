import logging
import inspect

class CustomLogger(logging.Logger):
    def findCaller(self, stack_info=False, stacklevel=1):
        frame = inspect.currentframe().f_back
        code = frame.f_globals.get('__code__')
        if code:
            return code.co_filename, frame.f_lineno, code.co_name
        else:
            return super().findCaller(stack_info, stacklevel)

def setup_logger(name, log_level=logging.DEBUG):
    logger = CustomLogger(name, log_level)
    formatter = logging.Formatter('%(asctime)s|%(name)s|%(levelname)s|%(filename)s:%(lineno)d || ==> %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger