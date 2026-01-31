from collections.abc import Mapping

from database.db_manager import Company, db_manager
from services.core.pre_seed_advisor import pre_seed_advisor


def _setup_company(tmp_path, name="Test Co", stage="pre_seed"):
    original_path = db_manager.db_path
    db_path = tmp_path / "pre_seed.db"
    db_manager.set_db_path(str(db_path))
    db_manager.initialize_database()
    company_id = db_manager.create_company(Company(name=name, stage=stage))
    return original_path, company_id


def test_analyze_company_returns_dict_and_has_company_name(tmp_path):
    original_path, company_id = _setup_company(tmp_path)
    try:
        analysis = pre_seed_advisor.analyze_company(company_id)
        assert isinstance(analysis, dict)
        assert "company_name" in analysis
        assert analysis["company_name"] == "Test Co"
    finally:
        db_manager.set_db_path(original_path)


def test_company_data_loader_returns_mapping_not_int(tmp_path):
    original_path, company_id = _setup_company(tmp_path, name="Loader Co")
    try:
        company_data = pre_seed_advisor.get_company_data(company_id)
        assert isinstance(company_data, Mapping)
        assert not isinstance(company_data, int)
        assert company_data["id"] == company_id
    finally:
        db_manager.set_db_path(original_path)
