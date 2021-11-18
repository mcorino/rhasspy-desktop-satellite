"""This module contains the main function run by the CLI command
rhasspy-desktop-satellite.
"""
from json import JSONDecodeError
import signal
import sys

from daemon import DaemonContext

from rhasspy_desktop_satellite.about import PROJECT, VERSION
from rhasspy_desktop_satellite.config import ServerConfig, DEFAULT_CONFIG
from rhasspy_desktop_satellite.exceptions import ConfigurationFileNotFoundError, \
    NoDefaultAudioDeviceError, UnsupportedPlatformError
from rhasspy_desktop_satellite.logger import get_logger
from rhasspy_desktop_satellite.server import SatelliteServer

def main(verbose, version, config, daemon):
    """The main function run by the CLI command.

    Args:
        verbose (bool): Use verbose output if True.
        version (bool): Print version information and exit if True.
        config (str): Configuration file.
        daemon (bool): Run as a daemon if True.
    """
    server = None
    # Define signal handler to cleanly exit the program.
    def exit_process(signal_number, frame):
        # pylint: disable=no-member
        logger.info('Received %s signal. Exiting...',
                    signal.Signals(signal_number).name)
        if not server is None:
            server.stop()
        sys.exit(0)

    # Register signals.
    signal.signal(signal.SIGQUIT, exit_process)
    signal.signal(signal.SIGTERM, exit_process)

    try:

        logger = get_logger(verbose, daemon)
        logger.info('%s %s', PROJECT, VERSION)

        # Start the program as a daemon.
        if daemon:
            logger.debug('Starting daemon...')
            context = DaemonContext(files_preserve=[logger.handlers[0].socket])
            context.signal_map = {signal.SIGQUIT: exit_process,
                                  signal.SIGTERM: exit_process}
            context.open()

        if not version:
            if not config:
                logger.debug('Using default configuration file.')
                config = DEFAULT_CONFIG

            logger.debug('Creating SatelliteServer object...')
            server = SatelliteServer(ServerConfig.from_json_file(config),
                                     verbose,
                                     logger)

            server.start()
    except ConfigurationFileNotFoundError as error:
        logger.critical('Configuration file %s not found. Exiting...', error.filename)
        sys.exit(1)
    except JSONDecodeError as error:
        logger.critical('%s is not a valid JSON file. Parsing failed at line %s and column %s. Exiting...', config, error.lineno, error.colno)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info('Received SIGINT signal. Shutting down rhasspy-desktop-satellite...')
        server.stop()
        sys.exit(0)
    except NoDefaultAudioDeviceError as error:
        logger.critical('No default audio %s device available. Exiting...',
                        error.inout)
        sys.exit(1)
    except PermissionError as error:
        logger.critical('Can\'t read file %s. Make sure you have read permissions. Exiting...', error.filename)
        sys.exit(1)
    except UnsupportedPlatformError as error:
        # Don't use logger because this exception is thrown while logging.
        print('Error: {} is not a supported platform.'.format(error.platform))
        sys.exit(1)
