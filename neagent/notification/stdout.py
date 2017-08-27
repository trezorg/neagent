from .base import BaseNotifier


__all__ = (
    'StdOutNotifier',
)


class StdOutNotifier(BaseNotifier):

    def __init__(self):
        super().__init__()

    async def notify(self, message):
        date = self.get_date_str()
        print(f'{date}\n{message}'.strip())
