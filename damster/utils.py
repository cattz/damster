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

    stdoutHandler = logging.StreamHandler(sys.stdout)
    stdoutHandler.setLevel(logging.DEBUG)
    stdoutHandler.addFilter(LogFilter())
    stdoutHandler.setFormatter(formatter)
    stderrHandler = logging.StreamHandler(sys.stderr)
    stderrHandler.setLevel(logging.ERROR)
    stderrHandler.setFormatter(formatter)
    logger.propagate = 0
    logger.addHandler(stdoutHandler)
    logger.addHandler(stderrHandler)
    logger.setLevel(log_level)
    return logger


def get_config():
    config = ConfigParser(interpolation=ExtendedInterpolation())
    defaults = pkg_resources.resource_filename('metco', 'defaults.cfg')
    config.read_file(open(defaults))
    config.read(['custom.cfg', os.path.expanduser('~/.config/damster.cfg')])
    return config
