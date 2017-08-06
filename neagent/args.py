"""Args module."""

import argparse

DESCRIPTION_TEXT = """
    Allows to get new records form neagent.by site by a link that set
    in commmand line
"""


def prepare_parser():
    """Handle the command line arguments."""
    parser = argparse.ArgumentParser(
        prog="neagent",
        description="\n".join(
            [s.lstrip() for s in DESCRIPTION_TEXT.splitlines()]),
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument(
        '-t',
        '--timeout',
        required=False,
        action='store',
        dest='timeout',
        type=int,
        default=60 * 5,
        help='Request timeout'
    )

    parser.add_argument(
        '-f',
        '--file',
        required=False,
        action='store',
        dest='file',
        type=str,
        default='~/neagent.txt',
        help='Result file'
    )

    parser.add_argument(
        '-d',
        '--daemon',
        required=False,
        action='store_true',
        dest='daemon',
        default=False,
        help='Daemonized mode'
    )

    parser.add_argument(
        '-v',
        '--verbose',
        required=False,
        action='store_true',
        dest='verbose',
        default=False,
        help='Verbose mode'
    )

    parser.add_argument(
        '-l',
        '--link',
        required=True,
        action='store',
        dest='link',
        type=str,
        help='Request link'
    )
    return parser
