from importlib.resources import files
import os
import logging.config
import wbi
from wbi.configuration import Config

# The _version.py file is managed by setuptools-scm
#   and is not in version control.
try:
    from wbi._version import version as __version__  # type: ignore
except ModuleNotFoundError:
    # We're likely running as a source package without installation
    __version__ = "src"

_ROOT = os.path.abspath(os.path.dirname(__file__))

logging.config.dictConfig(
    {
        "version": 1,
        "formatters": {
            "standard": {
                "format": "(%(levelname)s) (%(filename)s) (%(asctime)s) %(message)s",
                "datefmt": "%d-%b-%y %H:%M:%S",
            }
        },
        "handlers": {
            "default": {
                "level": "NOTSET",
                "formatter": "standard",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {"": {"handlers": ["default"], "level": "INFO"}},
    }
)

config = Config("wbi", files(wbi) / "config.yaml")
