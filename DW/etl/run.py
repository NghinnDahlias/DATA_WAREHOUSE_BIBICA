"""Stable public ETL entry point; implementation is split into focused modules."""
from .engine import load_postgres
from .cli import main,dry_run

if __name__ == "__main__":
    raise SystemExit(main())
