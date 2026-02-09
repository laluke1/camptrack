import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional

# Path: ~/.camptrack/logs/app.log
LOG_DIR = Path("~/.camptrack/logs").expanduser()
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s:%(lineno)d | "
    "%(funcName)s() | %(message)s"
)

def init_logging(
    console_level: Optional[int] = None,
    file_level: int = logging.DEBUG
) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(LOG_FORMAT)

    # File handler (always enabled)
    # Keep 7 days of logs, rotating at midnight
    file_handler = TimedRotatingFileHandler(
        LOG_FILE,
        when='midnight',                    # Rotate at midnight
        interval=1,                         # Every day
        backupCount=7,                      # Keeping only last 7 days of logs
        encoding='utf-8'
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)
    file_handler.suffix = '%Y-%m-%d'        # Add date for previous days logs
    root_logger.addHandler(file_handler)

    # Console handler (optional, for debugging)
    if console_level is not None:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
