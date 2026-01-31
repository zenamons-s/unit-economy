import sqlite3

from database.db_manager import ActualData, Company, db_manager


def test_save_actuals_inserts_correct_column_count(tmp_path):
    db_path = tmp_path / "actuals.db"
    db_manager.set_db_path(str(db_path))
    db_manager.initialize_database()

    company_id = db_manager.create_company(Company(name="TestCo"))
    actual = ActualData(
        company_id=company_id,
        year=2024,
        month_number=1,
        actual_mrr=1000.0,
        actual_total_revenue=1000.0,
        actual_total_costs=600.0,
        actual_burn_rate=600.0,
        actual_runway=10.0,
    )

    actual_id = db_manager.save_actual_data(actual)

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM actual_data WHERE id = ?", (actual_id,))
        count = cursor.fetchone()[0]
    finally:
        conn.close()

    assert count == 1
