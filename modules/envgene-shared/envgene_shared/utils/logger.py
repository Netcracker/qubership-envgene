import logging
import re
import sys
import time
from contextlib import contextmanager
from os import getenv


class CustomFormatter(logging.Formatter):
    BLUE = "\x1b[34;20m"
    WHITE = "\x1b[97;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
    BOLD_GREEN = "\x1b[32;1m"
    RESET = "\x1b[0m"
    BASE_FMT = "%(asctime)s [%(levelname)s] %(message)s [%(filename)s:%(lineno)d]"

    def __init__(self):
        super().__init__()
        self.formatters = {
            logging.DEBUG: logging.Formatter(self.BLUE + self.BASE_FMT + self.RESET),
            logging.INFO: logging.Formatter(self.WHITE + self.BASE_FMT + self.RESET),
            logging.WARNING: logging.Formatter(self.YELLOW + self.BASE_FMT + self.RESET),
            logging.ERROR: logging.Formatter(self.RED + self.BASE_FMT + self.RESET),
            logging.CRITICAL: logging.Formatter(self.BOLD_RED + self.BASE_FMT + self.RESET),
        }

    def format(self, record):
        formatter = self.formatters.get(record.levelno, self.formatters[logging.INFO])
        return formatter.format(record)

logger = logging.getLogger("envgene")
logger.propagate = False

log_level_str = getenv("ENVGENE_LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)
logger.setLevel(log_level)

if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    handler.setFormatter(CustomFormatter())
    logger.addHandler(handler)

_SECTION_ID_INVALID_CHARS = re.compile(r"[^a-zA-Z0-9_.-]")


@contextmanager
def log_section(section_id: str, header: str, collapsed: bool = True):
    section_id = _SECTION_ID_INVALID_CHARS.sub("_", section_id)
    collapsed_flag = "[collapsed=true]" if collapsed else ""
    sys.stdout.write(f"\x1b[0Ksection_start:{int(time.time())}:{section_id}{collapsed_flag}\r\x1b[0K{header}\n")
    sys.stdout.flush()
    try:
        yield
    finally:
        sys.stdout.write(f"\x1b[0Ksection_end:{int(time.time())}:{section_id}\r\x1b[0K\n")
        sys.stdout.flush()


def colorize(text: str, color: str) -> str:
    return f"{color}{text}{CustomFormatter.RESET}"


BANNER_WIDTH = 80


def banner(text: str) -> str:
    side = "=" * max(3, (BANNER_WIDTH - len(text) - 2) // 2)
    line = f"{side} {text} {side}"
    return line + "=" * max(0, BANNER_WIDTH - len(line))


def colorize_segment(text: str, segment: str, segment_color: str, base_color: str) -> str:
    idx = text.find(segment)
    if idx == -1:
        return colorize(text, base_color)
    before, after = text[:idx], text[idx + len(segment):]
    return f"{colorize(before, base_color)}{colorize(segment, segment_color)}{colorize(after, base_color)}"
