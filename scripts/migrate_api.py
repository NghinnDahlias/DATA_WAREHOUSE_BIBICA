"""Apply only the additive API/DSS read models to an already loaded repo DW."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import psycopg
from src.api.db import database_dsn
from DW.etl.engine import ANALYZE_SQL

path = Path(__file__).resolve().parents[1] / 'DW/postgresql/tables/040_api_dss.sql'
with psycopg.connect(database_dsn(), connect_timeout=5) as connection:
    connection.execute('SELECT pg_advisory_xact_lock(4031262)')
    connection.execute("SET LOCAL lock_timeout='5s'")
    connection.execute(path.read_text(encoding='utf8'))
    connection.execute(ANALYZE_SQL)
print('API/DSS read models applied to repository database')
