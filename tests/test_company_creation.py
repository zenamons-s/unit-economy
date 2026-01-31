import sqlite3

import pytest

from database.db_manager import Company, db_manager


def _setup_db(tmp_path):
    db_path = tmp_path / "company_creation.db"
    db_manager.set_db_path(str(db_path))
    db_manager.initialize_database()
    return db_path


def test_create_company_persists(tmp_path):
    db_path = _setup_db(tmp_path)

    company_id = db_manager.create_company(Company(name="PersistCo"))

    assert company_id is not None

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT id, name FROM companies WHERE id = ?", (company_id,)
        ).fetchone()

    assert row is not None
    assert row[1] == "PersistCo"


def test_company_list_includes_new_company(tmp_path):
    _setup_db(tmp_path)

    db_manager.create_company(Company(name="ListedCo"))
    companies = db_manager.get_all_companies()

    assert any(company.name == "ListedCo" for company in companies)


def test_initialize_does_not_delete_companies(tmp_path):
    _setup_db(tmp_path)

    company_id = db_manager.create_company(Company(name="StayCo"))
    db_manager.initialize_database()

    company = db_manager.get_company(company_id)
    assert company is not None
    assert company.name == "StayCo"


def test_duplicate_name_user_friendly_error(tmp_path):
    _setup_db(tmp_path)

    db_manager.create_company(Company(name="DuplicateCo"))

    with pytest.raises(ValueError, match="уже существует"):
        db_manager.create_company(Company(name="DuplicateCo"))
