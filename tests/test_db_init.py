import sqlite3

from database import init_db
from database.db_manager import db_manager


def _get_tables(db_path: str) -> set[str]:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()
    return tables


def test_init_db_creates_tables(tmp_path):
    db_path = tmp_path / "init.db"
    init_db.init_database(str(db_path))

    tables = _get_tables(str(db_path))
    assert {"companies", "financial_plans", "monthly_plans", "actual_data"}.issubset(tables)
    assert {"benchmark_metrics", "app_settings"}.issubset(tables)


def test_reset_database_recreates_tables(tmp_path):
    db_path = tmp_path / "reset.db"
    db_manager.set_db_path(str(db_path))
    db_manager.initialize_database()
    db_manager.reset_database()

    tables = set(db_manager.list_tables())
    assert "companies" in tables
    assert "financial_plans" in tables
