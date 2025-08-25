"""Helpers for use in Blender add-ons. No add-on speciffic functions are expected."""

from datetime import datetime
from pathlib import Path
from typing import Any

ADDON_DIR = Path(__file__).parent.resolve()
LOG_ADDON_NAME: str = __package__.rsplit(".", 1)[-1]

ASSETS_DIR = ADDON_DIR.joinpath("assets")


class TermColors:
    """Blender terminal colorize helper."""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"

    ENDC = "\033[0m"

    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def log(msg: str, *args: Any, msg_color: str = TermColors.OKCYAN) -> None:
    """Print a log message with the addon name."""
    time_str = datetime.now().strftime("%H:%M:%S") + " "
    compiled_msg = f"{time_str}{msg_color}{LOG_ADDON_NAME}{TermColors.ENDC}: {msg}"
    print(compiled_msg, *args, flush=True)


def log_warn(msg: str, *args: Any) -> None:
    """Print a warning log message with the addon name."""
    log(msg, *args, msg_color=TermColors.WARNING)


def log_err(msg: str, *args: Any) -> None:
    """Print a error log message with the addon name."""
    log(msg, *args, msg_color=TermColors.FAIL)


def log_line_number() -> None:
    """Print a log message with a line number."""
    import inspect  # pylint: disable=import-outside-toplevel

    caller = inspect.stack()[1]
    module = inspect.getmodule(caller.frame)
    module_name = module.__name__ if module else "unknown"
    log(f"{module_name}: {caller.lineno}")
