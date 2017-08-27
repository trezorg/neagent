import abc
from abc import ABC
from _datetime import datetime


class BaseNotifier(ABC):

    def __init__(self, *args, **kwargs):
        pass

    @staticmethod
    def get_date_str():
        return datetime.now().strftime('%Y-%m-%d %H-%M-%S')

    @abc.abstractmethod
    async def notify(self, message):
        pass
