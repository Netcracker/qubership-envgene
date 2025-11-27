from os import getenv
from loguru import logger
import sys

log_level_str = getenv("ENVGENE_LOG_LEVEL", "INFO").upper()
fmt = "<level>{time:YYYY-MM-DD HH:mm:ss,SSS} [{level: <8}] {message} [{name}:{line}]</level>"

LEVEL_COLORS = {
    "DEBUG": "<grey>{message}</grey>",
    "INFO": "<white>{message}</white>",
    "WARNING": "<yellow>{message}</yellow>",
    "ERROR": "<red>{message}</red>",
    "CRITICAL": "<bold red>{message}</bold red>"
}

logger.remove()

logger.add(
    sys.stdout,
    level=log_level_str,
    colorize=True,
    format=fmt
)

logger = logger.bind(name="envgene")
