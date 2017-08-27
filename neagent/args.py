"""Args module."""

import os
import argparse

from .config import (
    filter_config_files,
    DEFAULT_CONFIGS,
    check_options,
    check_writable_file,
    check_existing_file,
    read_configs,
)

DESCRIPTION_TEXT = """
    Allows to get new records from neagent.by site by a link that set
    in the command line or settings file(default ~/neagent.yml)
"""

DEFAULT_TIMEOUT = 60 * 5
DEFAULT_STDOUT = False
DEFAULT_DAEMON = False
DEFAULT_VERBOSE = False


def prepare_parser():
    """Handle the command line arguments."""
    parser = argparse.ArgumentParser(
        prog="neagent",
        description="\n".join(
            [s.lstrip() for s in DESCRIPTION_TEXT.splitlines()]),
        formatter_class=argparse.RawDescriptionHelpFormatter)

    subparsers = parser.add_subparsers(dest='command')
    parser_telegram = subparsers.add_parser(
        'telegram', help='Send results to telegram bot')
    telegram_group = parser_telegram.add_argument_group(
        'telegram', 'Telegram bot settings')

    parser.add_argument(
        '-v',
        '--verbose',
        required=False,
        action='store_true',
        dest='verbose',
        default=None,
        help='Verbose mode'
    )

    parser.add_argument(
        '-db',
        '--database',
        required=False,
        action='store',
        dest='database',
        type=str,
        default=os.path.expanduser('~/neagent.db'),
        help='Verbose mode'
    )

    parser.add_argument(
        '-d',
        '--daemon',
        required=False,
        action='store_true',
        dest='daemon',
        default=None,
        help='Daemon mode'
    )

    parser.add_argument(
        '-s',
        '--stdout',
        required=False,
        action='store_true',
        dest='stdout',
        default=None,
        help='Print results in stdout'
    )

    parser.add_argument(
        '-f',
        '--file',
        required=False,
        action='store',
        dest='file',
        type=str,
        help='Result file'
    )

    parser.add_argument(
        '-t',
        '--timeout',
        required=False,
        action='store',
        dest='timeout',
        type=int,
        help='Request timeout'
    )

    parser.add_argument(
        '-l',
        '--link',
        required=False,
        action='store',
        dest='link',
        type=str,
        help='Request link'
    )

    parser.add_argument(
        '-c',
        '--config',
        required=False,
        action='store',
        dest='config',
        type=check_existing_file,
        help='Config file'
    )

    telegram_group.add_argument(
        '-b',
        '--bot',
        required=False,
        action='store',
        dest='bot',
        type=str,
        help='Telegram bot token'
    )

    telegram_group.add_argument(
        '-i',
        '--cid',
        required=False,
        action='store',
        dest='cid',
        type=str,
        help='Telegram chat id'
    )

    return parser


def prepare_options():
    """Parse arguments."""
    parser = prepare_parser()
    args_options = {
        k: v for k, v in vars(parser.parse_args()).items() if v is not None
    }
    allowed_configs = DEFAULT_CONFIGS + [args_options.get("config")]
    config_files = list(filter_config_files(*allowed_configs))
    options = read_configs(*config_files)
    for key, value in args_options.items():
        if value is not None:
            options[key] = value
    options.update(args_options)
    if options.get('timeout') is None:
        options['timeout'] = DEFAULT_TIMEOUT
    if options.get('verbose') is None:
        options['verbose'] = DEFAULT_VERBOSE
    if options.get('daemon') is None:
        options['daemon'] = DEFAULT_DAEMON
    if options.get('stdout') is None:
        options['stdout'] = DEFAULT_STDOUT
    if not check_options(options):
        parser.print_help()
        return
    if options.get('file'):
        check_writable_file(options['file'])
    check_writable_file(options['database'])
    return options
