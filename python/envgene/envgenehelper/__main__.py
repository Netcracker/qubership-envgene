import sys
from .logger import logger

def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))
    logger.opt(exception=(exc_type, exc_value, exc_traceback)).error(
        f"Uncaught {exc_type.__name__}: {exc_value}"
    )
sys.excepthook = handle_exception