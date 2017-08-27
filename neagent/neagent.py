#! /usr/bin/env python3
"""NeAgent helper."""

import asyncio
import signal
import logging
from itertools import chain
from logging.handlers import SysLogHandler
from functools import partial

import aiohttp
import aioodbc
from lxml import (
    html,
    cssselect,
)
from daemons import daemonizer
from colorama import init as colorama_init

from .utils import prepare_dsn
from .args import prepare_options
from .sql import (
    CREATE_TABLE_SQL,
    prepare_select_query,
    prepare_insert_query,
)
from .notification import (
    TelegramNotifier,
    StdOutNotifier,
    FileNotifier,
)

PID = '/tmp/neagent.pid'
HEADERS = {
    'Accept': ('text/html,application/xhtml+xml,'
               'application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'),
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                   '(KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'),
}

logger = logging.getLogger(__name__)


async def _create_table(loop, db_name):
    dsn = prepare_dsn(db_name)
    conn = await aioodbc.connect(dsn=dsn, loop=loop, autocommit=True)
    cursor = await conn.cursor()
    await cursor.execute(CREATE_TABLE_SQL)
    await cursor.close()
    await conn.close()


async def _store_db(loop, base_link, links, db_name):
    dsn = prepare_dsn(db_name)
    conn = await aioodbc.connect(dsn=dsn, loop=loop, autocommit=True)
    cursor = await conn.cursor()
    query = prepare_select_query(base_link, links)
    res = await cursor.execute(query)
    stored_links = (lnk.link for lnk in await res.fetchall())
    new_links = sorted(set(links) - set(stored_links))
    if new_links:
        query = prepare_insert_query(base_link, new_links)
        await cursor.execute(query)
    await cursor.close()
    await conn.close()
    return sorted(new_links)


async def _get_content(session, link):
    async with session.get(link, headers=HEADERS) as resp:
        content = await resp.read()
        return content.decode('utf-8', errors='ignore')


async def _get_page_links(session, link):
    page = await _get_content(session, link)
    doc_html = html.fromstring(page)
    select = cssselect.CSSSelector(".imd_photo a")
    return (el.get('href') for el in select(doc_html))


async def _get_pages(session, link):
    page = await _get_content(session, link)
    doc_html = html.fromstring(page)
    select = cssselect.CSSSelector(".page_numbers a")
    return chain((el.get('href') for el in select(doc_html)), (link,))


async def _get_links(link):
    async with aiohttp.ClientSession() as session:
        page_links = set(await _get_pages(session, link))
        logger.debug('Got {0} page{1}...'.format(
            len(page_links), '' if len(page_links) == 1 else 's'))
        all_page_links = [
            await _get_page_links(session, link) for link in page_links]
        links = sorted(set(chain(*all_page_links)))
        logger.debug('Got {0} link{1}...'.format(
            len(links), '' if len(links) == 1 else 's'))
        return links


async def _notify(notifiers, new_links):
    result = f'{chr(10).join(new_links)}' if new_links else ''
    for notifier in notifiers:
        logger.info(f'Processing notifier {notifier.__class__.__name__}')
        await notifier.notify(result)


async def _process_loop(args, loop):
    link = args['link']
    timeout = args['timeout']
    database = args['database']
    await _create_table(loop, database)
    notifiers = list(_prepare_notifiers(args))
    while True:
        try:
            links = await _get_links(link)
            new_links = await _store_db(loop, link, links, database)
        except aiohttp.client_exceptions.ClientError:
            logger.exception(f'Cannot open page: {link}')
        except Exception as _:
            logger.exception(f'Cannot store new links for: {link}')
        else:
            await _notify(notifiers, new_links)
        finally:
            await asyncio.sleep(timeout)


def _prepare_notifiers(args):
    if args['stdout'] and not args['daemon']:
        yield StdOutNotifier()
    if args.get('command') == 'telegram':
        yield TelegramNotifier(args['bot'], args['cid'])
    if args.get('file'):
        yield FileNotifier(args['file'])


def _prepare_logging(daemon, level=logging.INFO):
    syslog_handler = SysLogHandler(address='/dev/log')
    handlers = (syslog_handler,) if daemon else \
        (logging.StreamHandler(), syslog_handler,)
    logging.basicConfig(level=level, handlers=handlers)


def _stop(loop, *_):
    logger.debug('Closing application...')
    for task in asyncio.Task.all_tasks():
        task.cancel()
    logger.debug('Closing loop...')
    loop.stop()


def _start(args):
    """Point of start."""
    level = logging.DEBUG if args['verbose'] else logging.INFO
    _prepare_logging(args['daemon'], level=level)
    logger.debug('Starting application...')
    loop = asyncio.get_event_loop()
    for sig_name in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(
            getattr(signal, sig_name), partial(_stop, loop))
    asyncio.ensure_future(_process_loop(args, loop), loop=loop)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        _stop(loop)


def main():
    """Enter point."""
    args = prepare_options()
    if not args:
        return
    colorama_init()
    if not args['daemon']:
        _start(args)
    else:
        daemonizer.run(pidfile=PID)(_start)(args)


if __name__ == '__main__':
    main()
