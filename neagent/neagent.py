"""Neagent helper."""
import asyncio
import os
from datetime import datetime
from itertools import chain

import aiohttp
import aioodbc
from lxml import html, cssselect
from daemons import daemonizer

from .args import prepare_parser

DB = os.path.expanduser('~/neagent.db')
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


async def _create_table(loop):
    conn = await aioodbc.connect(dsn=DSN, loop=loop, autocommit=True)
    cursor = await conn.cursor()
    await cursor.execute("""
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY,
            base_link TEXT,
            link TEXT
        );
        CREATE UNIQUE INDEX IF NOT EXISTS u_links ON links(base_link, link);
    """)
    await cursor.close()
    await conn.close()


async def _store_db(loop, base_link, links):
    conn = await aioodbc.connect(dsn=DSN, loop=loop, autocommit=True)
    cursor = await conn.cursor()
    links_req = '({})'.format(','.join(f"'{lnk}'" for lnk in links))
    query = """
        SELECT link FROM links WHERE base_link = '{0}' AND link IN {1}
    """.format(base_link, links_req)
    res = await cursor.execute(query)
    stored_links = (lnk.link for lnk in await res.fetchall())
    new_links = sorted(set(links) - set(stored_links))
    if new_links:
        query = "INSERT INTO links(base_link, link) VALUES {0}".format(
            ', '.join(f"('{base_link}', '{link}')" for link in new_links))
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
    dochtml = html.fromstring(page)
    select = cssselect.CSSSelector(".imd_photo a")
    return (el.get('href') for el in select(dochtml))


async def _get_pages(session, link):
    page = await _get_content(session, link)
    dochtml = html.fromstring(page)
    select = cssselect.CSSSelector(".page_numbers a")
    return chain((el.get('href') for el in select(dochtml)), (link,))


async def _get_links(link):
    async with aiohttp.ClientSession() as session:
        page_links = set(await _get_pages(session, link))
        all_page_links = [
            await _get_page_links(session, link) for link in page_links]
        return sorted(set(chain(*all_page_links)))


async def _get_new_links(link, loop):
    await _create_table(loop)
    links = await _get_links(link)
    new_links = await _store_db(loop, link, links)
    return new_links


async def _process_loop(args, loop):
    await _create_table(loop)
    link = args.link
    timeout = args.timeout
    while True:
        links = await _get_links(link)
        new_links = await _store_db(loop, link, links)
        cur_date = datetime.now().strftime('%Y-%m-%d %H-%M-%S')
        result = '{}\n{}'.format(cur_date, '\n'.join(new_links)) if new_links \
            else cur_date
        if not args.daemon:
            print(result)
        with open(os.path.expanduser(args.file), 'a+') as fl:
            fl.write(f'{result}\n')
        await asyncio.sleep(timeout)


def _start(args):
    """Point of start."""
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(_process_loop(args, loop), loop=loop)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.stop()


def main():
    """Enter point."""
    args = prepare_parser().parse_args()
    if not args.daemon:
        _start(args)
    else:
        daemonizer.run(pidfile="/tmp/neagent.pid")(_start)(args)


if __name__ == '__main__':
    main()
