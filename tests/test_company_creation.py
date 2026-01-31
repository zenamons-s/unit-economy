import pytest

from database.db_manager import Company, db_manager


def _setup_db(tmp_path):
    db_path = tmp_path / "company_creation.db"
    db_manager.set_db_path(str(db_path))
    db_manager.initialize_database()
    return db_path


def test_create_company_persists_and_listed(tmp_path):
    _setup_db(tmp_path)

    company_id = db_manager.create_company(Company(name="PersistCo"))
    companies = db_manager.get_all_companies()

    assert company_id is not None
    assert any(company.name == "PersistCo" for company in companies)


def test_company_not_deleted_on_reinitialize(tmp_path):
    _setup_db(tmp_path)

    company_id = db_manager.create_company(Company(name="StayCo"))
    db_manager.initialize_database()

    company = db_manager.get_company(company_id)
    assert company is not None
    assert company.name == "StayCo"


def test_create_company_handles_duplicate_name(tmp_path):
    _setup_db(tmp_path)

    db_manager.create_company(Company(name="DuplicateCo"))

    with pytest.raises(ValueError, match="уже существует"):
        db_manager.create_company(Company(name="DuplicateCo"))
