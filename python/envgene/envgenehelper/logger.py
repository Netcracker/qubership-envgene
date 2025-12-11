from os import getenv
from loguru import logger
import sys

log_level_str = getenv("LOG_LEVEL", "INFO").upper()
fmt = "<level>{time:YYYY-MM-DD HH:mm:ss,SSS} [{level: <8}] {message} [{name}:{line}]</level>"

logger.remove()

logger.add(
    sys.stdout,
    level=log_level_str,
    colorize=True,
    format=fmt
)

logger = logger.bind(name="envgene")
