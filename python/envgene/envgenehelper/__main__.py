import sys
from .logger import logger

def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception