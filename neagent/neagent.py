#! /usr/bin/env python3
"""Neagent helper."""

import asyncio
import os
import signal
import logging
from datetime import datetime
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

from .args import prepare_parser
from .sql import (
    CREATE_TABLE_SQL,
    prepare_select_query,
    prepare_insert_query,
)

DB = os.path.expanduser('~/neagent.db')
PID = '/tmp/neagent.pid'
DSN = ('Driver=SQLite3;SERVER=localhost;'
       'Database={};Trusted_connection=yes'.format(DB))
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


def _prepare_logging(daemon, level=logging.INFO):
    stream_handler = logging.StreamHandler()
    syslog_handler = SysLogHandler(address='/dev/log')
    handlers = (syslog_handler,) if daemon else \
        (stream_handler, syslog_handler,)
    logging.basicConfig(level=level, handlers=handlers)


async def _create_table(loop):
    conn = await aioodbc.connect(dsn=DSN, loop=loop, autocommit=True)
    cursor = await conn.cursor()
    await cursor.execute(CREATE_TABLE_SQL)
    await cursor.close()
    await conn.close()


async def _store_db(loop, base_link, links):
    conn = await aioodbc.connect(dsn=DSN, loop=loop, autocommit=True)
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


def _process_result(args, result):
    if not args.daemon:
        print(result)
    with open(os.path.expanduser(args.file), 'a+') as fl:
        fl.write(f'{result}\n')


async def _process_loop(args, loop):
    link = args.link
    timeout = args.timeout
    await _create_table(loop)
    while True:
        cur_date = datetime.now().strftime('%Y-%m-%d %H-%M-%S')
        try:
            links = await _get_links(link)
            new_links = await _store_db(loop, link, links)
        except aiohttp.client_exceptions.ClientError:
            logger.exception(f'Cannot open page: {link}')
        except Exception as _:
            logger.exception(f'Cannot store new links: {link}')
        else:
            result = f'{cur_date}\n{chr(10).join(new_links)}' \
                if new_links else cur_date
            _process_result(args, result)
        finally:
            await asyncio.sleep(timeout)


def _stop(loop, *_):
    logger.debug('Closing application...')
    for task in asyncio.Task.all_tasks():
        task.cancel()
    logger.debug('Closing loop...')
    loop.stop()


def _start(args):
    """Point of start."""
    level = logging.DEBUG if args.verbose else logging.INFO
    _prepare_logging(args.daemon, level=level)
    logger.debug('Starting application...')
    loop = asyncio.get_event_loop()
    for sig_name in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(
            getattr(signal, sig_name),  partial(_stop, loop))
    asyncio.ensure_future(_process_loop(args, loop), loop=loop)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        _stop(loop)


def main():
    """Enter point."""
    args = prepare_parser().parse_args()
    if not args.daemon:
        _start(args)
    else:
        daemonizer.run(pidfile=PID)(_start)(args)


if __name__ == '__main__':
    main()
