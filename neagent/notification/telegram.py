from urllib.parse import quote

import aiohttp

from .base import BaseNotifier


__all__ = (
    'TelegramNotifier',
)


class TelegramNotifier(BaseNotifier):

    def __init__(self, token, chat_id):
        super().__init__()
        self.base_ulr = \
            f'https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}'

    def get_bot_link(self, message):
        result = quote(message.replace('\n', '\n\n'))
        return f'{self.base_ulr}&text={result}'

    async def notify(self, message):
        if not message:
            return
        link = self.get_bot_link(message)
        async with aiohttp.ClientSession() as session:
            await session.get(link)
