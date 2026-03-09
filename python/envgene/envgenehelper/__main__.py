import sys
from .logger import logger

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, ReferenceError):
        logger.critical(f"{exc_type.__name__}: {exc_value}")
        return
    else:
        logger.critical("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception