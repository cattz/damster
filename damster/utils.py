import logging
import os
import sys
import pkg_resources
import arrow
from arrow.parser import ParserError
from configparser import ConfigParser, ExtendedInterpolation
import re

NON_ASCII = re.compile(r'[^\x00-\x7f]')


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
    log_level = levels[os.environ.get('DAMSTER_LOGLEVEL', 'INFO')]
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


log = initialize_logger(__name__)


def get_config(config_file):
    config = ConfigParser(interpolation=ExtendedInterpolation())
    defaults = pkg_resources.resource_filename('damster', 'defaults.cfg')
    cwd = os.getcwd()
    config_files_list = [defaults, os.path.expanduser('~/.config/damster.cfg'), os.path.join(cwd, 'damster.cfg')]
    if config_file:
        config_file_abs = os.path.join(cwd, config_file)
        if os.path.isfile(config_file_abs):
            config_files_list.append(config_file_abs)
        else:
            log.error('Can not read config file "{}"'.format(config_file_abs))
            sys.exit(-1)
    config.read(config_files_list)
    return config


# TODO: Make this use global time zone
def time_to_excel(tm, tzinfo='Europe/Amsterdam'):
    try:
        if type(tm) != arrow.arrow.Arrow:
            tm = arrow.get(tm).replace(tzinfo=tzinfo)
        temp = arrow.get('1899-12-30').replace(tzinfo=tzinfo)  # Note, not 31st Dec but 30th!
        delta = arrow.get(tm) - temp
    except ParserError:
        return ''
    return str(float(delta.days) + (float(delta.seconds) / 86400))


def time_delta(t1, t2, excel=True):
    try:
        at1 = arrow.get(t1)
        at2 = arrow.get(t2)
        delta = at2 - at1
        if excel:
            delta = str(float(delta.days) + (float(delta.seconds) / 86400))
        return delta
    except ParserError:
        if excel:
            return '0'
        return 0


def quoted(it):
    return '"{}"'.format(it)


def replace_non_ascii(s, replacement=''):
    return re.sub(NON_ASCII, replacement, s)
