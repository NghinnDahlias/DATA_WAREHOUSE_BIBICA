"""Short, read-only consistent snapshots. Never import the parent project."""
import os
from contextlib import contextmanager

import psycopg
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row


def database_dsn():
    dsn = os.environ.get('BIBICA_DSN', 'postgresql://warehouse@127.0.0.1:55432/bibica_repo')
    if conninfo_to_dict(dsn).get('dbname') == 'warehouse':
        raise ValueError('BIBICA_DSN must point to the repository database, not the parent warehouse')
    return dsn


@contextmanager
def snapshot():
    with psycopg.connect(database_dsn(), connect_timeout=5, row_factory=dict_row) as connection:
        connection.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        connection.execute("SET LOCAL statement_timeout = '20s'")
        connection.execute("SET LOCAL lock_timeout = '3s'")
        connection.execute("SET LOCAL TIME ZONE 'Asia/Ho_Chi_Minh'")
        # The local PostgreSQL parallel plan reproduced non-repeatable filtered counts.
        # Keep each read statement serial until that engine/plan issue is resolved.
        connection.execute('SET LOCAL max_parallel_workers_per_gather=0')
        yield connection
