import logging
import re
import sys
import time
from contextlib import contextmanager
from os import getenv
from envgene_shared.utils.logger import *


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