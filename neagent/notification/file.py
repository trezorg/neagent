import os

from .base import BaseNotifier


__all__ = (
    'FileNotifier',
)


class FileNotifier(BaseNotifier):

    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    async def notify(self, message):
        date = self.get_date_str()
        with open(os.path.expanduser(self.filename), 'a+') as fl:
            result = f'{date}\n{message}'.strip()
            fl.write(f'{result}\n')
