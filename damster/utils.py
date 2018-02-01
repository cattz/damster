import logging
import os
import sys
import pkg_resources

from configparser import ConfigParser, ExtendedInterpolation


class LogFilter(logging.Filter):
    """
    Used by :func:`initialize_logger` to redirect errors to ``stderr``
    """
    def filter(self, rec):
        return rec.levelno in (logging.DEBUG, logging.INFO, logging.WARNING)


def initialize_logger(module_name):
    """
    Log initialization

    :param module_name: module name
    :return: logger object
    """

    levels = {'DEBUG': logging.DEBUG,
              'INFO': logging.INFO,
              'WARNING': logging.WARNING,
              'ERROR': logging.ERROR}
    log_level = levels[os.environ.get('bamboo_loglevel', 'DEBUG')]
    logger = logging.getLogger(module_name)

    log_fmt_string = '%(asctime)-19s %(name)s: [%(levelname)-7s] - %(message)s'
    formatter = logging.Formatter(log_fmt_string)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.addFilter(LogFilter())
    stdout_handler.setFormatter(formatter)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)
    stderr_handler.setFormatter(formatter)
    logger.propagate = 0
    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)
    logger.setLevel(log_level)
    return logger


def get_config():
    config = ConfigParser(interpolation=ExtendedInterpolation())
    defaults = pkg_resources.resource_filename('damster', 'defaults.cfg')
    config.read_file(open(defaults))
    config.read(['damster.cfg', os.path.expanduser('~/.config/damster.cfg')])
    return config
