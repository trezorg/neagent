"""Parse config files."""

import os
import logging
import argparse

import yaml
from colorama import Fore

from .utils import print_color_line

DEFAULT_CONFIG_FILENAME = 'neagent.yml'
DEFAULT_CONFIGS = [
    os.path.expanduser("~/{0}".format(DEFAULT_CONFIG_FILENAME)),
    os.path.join(os.path.curdir, DEFAULT_CONFIG_FILENAME)
]
MAIN_OPTIONS = (
    'timeout',
    'daemon',
    'database',
    'stdout',
    'verbose',
    'link',
)

TELEGRAM_OPTIONS = (
    'bot',
    'cid',
)

logging.basicConfig()
logger = logging.getLogger('neagent')
logger.setLevel(logging.DEBUG)


def filter_config_files(*args):
    for filename in args:
        if filename and os.path.isfile(filename):
            yield filename


def _read_config(filename):
    try:
        fln = open(filename, encoding='utf-8')
        return yaml.load(fln.read())
    except Exception as err:
        logger.error(err)
        return {}


def _meld_configs(result, *options):
    result = result or {}
    for option in options:
        option = {k: v for k, v in option.items() if v}
        for key, value in option.items():
            if isinstance(value, (list, tuple)):
                values = result.get(key, [])
                values.extend(value)
                result[key] = list(set(values))
            elif isinstance(value, dict):
                values = result.get(key, {})
                values.update(value)
                result[key] = values
            else:
                result[key] = value
    return result


def read_configs(*args):
    result = {}
    for filename in args:
        config = _read_config(filename)
        result = _meld_configs(result, config)
    return result


def _check_absent_options(options, names):
    return [name for name in names if name not in options]


def check_options(options):
    command = options.get('command', '')
    required_options_names = MAIN_OPTIONS
    if command == 'telegram':
        required_options_names += TELEGRAM_OPTIONS
    absent_options = _check_absent_options(options, required_options_names)
    if absent_options:
        print_color_line(
            'Absent parameters: {0}.\nYou should set them either in the'
            ' config file or in the command line.\n'.format(absent_options),
            Fore.RED)
        return False
    return True


def check_existing_file(filename):
    """Check config existence."""
    if not os.path.isfile(filename):
        raise argparse.ArgumentTypeError(
            'Filename is not exists: {0}'.format(filename))
    return filename


def check_writable_file(filename):
    """Check writable file."""
    try:
        with open(os.path.expanduser(filename), 'a+'):
            pass
    except IOError:
        raise argparse.ArgumentTypeError(
            'Filename is not not writable: {0}'.format(filename))
    return filename
