from os import getenv
import logging

class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = u'[%(asctime)s] [%(levelname)-8s] %(message)s [%(filename)s:%(lineno)d]'

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# create logger with 'spam_application'
logger = logging.getLogger("envgene")
logger.setLevel(logging.INFO)
# create console handler with a higher log level
ch = logging.StreamHandler()
# get logging level from env var
log_level_str = getenv('ENVGENE_LOG_LEVEL', 'INFO').upper()
log_level = getattr(logging, log_level_str, logging.INFO)
ch.setLevel(log_level)
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)
