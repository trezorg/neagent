"""SQL queries"""
from typing import Iterable


__all__ = (
    'CREATE_TABLE_SQL',
    'prepare_select_query',
    'prepare_insert_query',
)


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY,
    base_link TEXT,
    link TEXT,
    added INTEGER
);
CREATE UNIQUE INDEX IF NOT EXISTS u_links ON links(base_link, link);
"""


def prepare_select_query(base_link: str, links: Iterable) -> str:
    links_req = '({})'.format(','.join(f"'{lnk}'" for lnk in links))
    query = """
        SELECT link FROM links WHERE base_link = '{0}' AND link IN {1}
    """.format(base_link, links_req)
    return query


def prepare_insert_query(base_link: str, links: Iterable) -> str:
    query = "INSERT INTO links(base_link, link, added) VALUES {0}".format(
        ', '.join(f"('{base_link}', '{link}', CURRENT_TIMESTAMP)"
                  for link in links))
    return query
