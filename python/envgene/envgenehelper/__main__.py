import sys
import traceback
from .logger import logger

def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error("Uncaught exception:\n" + "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
sys.excepthook = handle_exception