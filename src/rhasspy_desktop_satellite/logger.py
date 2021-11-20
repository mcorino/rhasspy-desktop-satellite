"""This module contains helper functions to log messages from Rhasspy Desktop
Satellite."""
import logging
from logging.handlers import SysLogHandler
import sys

import colorlog

from rhasspy_desktop_satellite.exceptions import UnsupportedPlatformError

DAEMON_FORMAT = '{}[%(process)d]: %(message)s'
INTERACTIVE_FORMAT = '%(asctime)s %(log_color)s%(levelname)-8s%(reset)s %(message)s'
LOG_COLORS = {'DEBUG':    'white',
              'INFO':     'green',
              'WARNING':  'yellow',
              'ERROR':    'red',
              'CRITICAL': 'bold_red'}
LOGGER_NAME = 'rhasspy-desktop-satellite'

def get_domain_socket():
    """Get the default domain socket for syslog on this platform."""
    if sys.platform.startswith('linux'):  # Linux
        return '/dev/log'
    if sys.platform.startswith('darwin'):  # macOS
        return '/var/run/syslog'
    # Unsupported platform
    raise UnsupportedPlatformError(sys.platform)


def get_logger(verbose, debug):
    """Return a Logger object with the right level, formatter and handler."""

    handler = colorlog.StreamHandler(stream=sys.stdout)
    formatter = colorlog.ColoredFormatter(INTERACTIVE_FORMAT,
                                          log_colors=LOG_COLORS)
    logger = colorlog.getLogger(LOGGER_NAME)

    if debug:
        logger.setLevel(logging.DEBUG)
    elif verbose:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
