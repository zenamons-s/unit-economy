from database.db_manager import Company, db_manager


def _setup_db(tmp_path):
    db_path = tmp_path / "company.db"
    db_manager.set_db_path(str(db_path))
    db_manager.initialize_database()
    return db_path


def test_create_company_persists_in_db(tmp_path):
    _setup_db(tmp_path)
    company_id = db_manager.create_company(
        Company(name="Persist Co", stage="seed")
    )
    assert company_id is not None
    with db_manager.get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    assert count == 1


def test_get_companies_returns_new_company(tmp_path):
    _setup_db(tmp_path)
    db_manager.create_company(Company(name="Visible Co", stage="pre_seed"))
    companies = db_manager.get_all_companies()
    assert any(company.name == "Visible Co" for company in companies)


def test_init_does_not_delete_companies(tmp_path):
    _setup_db(tmp_path)
    db_manager.create_company(Company(name="Stable Co", stage="growth"))
    db_manager.initialize_database()
    with db_manager.get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    assert count == 1
