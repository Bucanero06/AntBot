import inspect
import logging
import sys
from datetime import datetime


# DEFAULT LOGGING VALUES
DEFAULT_LOGGIN_VALUES = dict(
    RESET=0,
    DEBUG=10,
    INFO=20,
    REMARKS=25,
    WARNING=30,
    UNKNOWN=35,
    ERROR=40,
    CRITICAL=50
)

REMARKS = DEFAULT_LOGGIN_VALUES["REMARKS"]
UNKNOWN = DEFAULT_LOGGIN_VALUES["UNKNOWN"]


def remarks(self, message, *args, **kws):
    if self.isEnabledFor(REMARKS):
        self._log(REMARKS, message, args, **kws)


def unknown(self, message, *args, **kws):
    if self.isEnabledFor(UNKNOWN):
        self._log(UNKNOWN, message, args, **kws)


# Add the custom levels and methods to the Logger class

logging.addLevelName(REMARKS, "REMARKS")
logging.Logger.remarks = remarks

logging.addLevelName(UNKNOWN, "UNKNOWN")
logging.Logger.unknown = unknown


class ColoredLogger(logging.Formatter):
    """Custom logger formatter to add colors to log messages"""

    def format(self, record):
        COLOR_CODES = {
            "DEBUG": "\033[92m",  # Green
            "INFO": "\033[94m",  # Blue
            "REMARKS": "\033[95m",  # Purple
            "WARNING": "\033[93m",  # Yellow
            "UNKNOWN": "\033[96m",  # Cyan (for unknown messages)
            "ERROR": "\033[91m",  # Red
            "CRITICAL": "\033[41m",  # Background Red (for critical messages)
            "RESET": "\033[0m"
        }

        log_time = datetime.utcnow().isoformat() + "Z"
        log_level = record.levelname
        log_message = record.getMessage()
        log_name = record.name

        color_code = COLOR_CODES.get(log_level, COLOR_CODES["RESET"])
        colored_log_level = color_code + log_level + COLOR_CODES["RESET"]

        return f"{log_time} [{colored_log_level}] {log_name}: {log_message}"


def setup_logger(name, level=logging.DEBUG):
    # Create logger instance
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create console handler and set formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredLogger())

    # Add console handler to the logger
    logger.addHandler(console_handler)

    return logger


def get_caller_logger():
    # Get the name of the script or module that called the current function
    caller_frame = inspect.stack()[1]
    caller_module = inspect.getmodule(caller_frame[0])
    caller_name = caller_module.__name__.split('.')[-1]

    # Set up the logger with the name of the calling script or module
    return setup_logger(caller_name)


# Setup a logger
logger = setup_logger(__name__.split('.')[-1])
