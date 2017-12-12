"""Utils."""
from colorama import Fore

__all__ = (
    'print_color_line',
    'prepare_dsn',
)


def print_color_line(text, color, new_line=True):
    """Print function."""
    message = '{0}{1}{2}'.format(color, text, Fore.RESET)
    print(message, **({} if new_line else {'end': ' '}))


def prepare_dsn(db_name):
    """Help Dsn function."""
    return ('Driver=SQLite3;SERVER=localhost;Database={};'
            'Trusted_connection=yes').format(db_name)
