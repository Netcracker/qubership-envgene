import logging
from os import getenv


# class CustomFormatter(logging.Formatter):
#     BLUE = "\x1b[34;20m"
#     WHITE = "\x1b[97;20m"
#     YELLOW = "\x1b[33;20m"
#     RED = "\x1b[31;20m"
#     BOLD_RED = "\x1b[31;1m"
#     RESET = "\x1b[0m"
#     BASE_FMT = "%(asctime)s [%(levelname)s] %(message)s [%(filename)s:%(lineno)d]"

#     def __init__(self):
#         super().__init__()
#         self.formatters = {
#             logging.DEBUG: logging.Formatter(self.BLUE + self.BASE_FMT + self.RESET),
#             logging.INFO: logging.Formatter(self.WHITE + self.BASE_FMT + self.RESET),
#             logging.WARNING: logging.Formatter(self.YELLOW + self.BASE_FMT + self.RESET),
#             logging.ERROR: logging.Formatter(self.RED + self.BASE_FMT + self.RESET),
#             logging.CRITICAL: logging.Formatter(self.BOLD_RED + self.BASE_FMT + self.RESET),
#         }

#     def format(self, record):
#         formatter = self.formatters.get(record.levelno, self.formatters[logging.INFO])
#         return formatter.format(record)

BASE_FMT = "%(asctime)s [%(levelname)s] %(message)s [%(filename)s:%(lineno)d]"

logger = logging.getLogger("envgene")
logger.propagate = False

log_level_str = getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)
logger.setLevel(log_level)

if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    handler.setFormatter(CustomFormatter())
    logger.addHandler(handler)
