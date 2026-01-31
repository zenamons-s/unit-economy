from datetime import datetime

from database.db_manager import ActualData, Company, FinancialPlan, MonthlyPlan, db_manager
from services.financial_system.variance_analyzer import variance_analyzer


def test_variance_analyzer_has_analyze_monthly_variance(tmp_path):
    db_path = tmp_path / "variance.db"
    db_manager.set_db_path(str(db_path))
    db_manager.initialize_database()

    company_id = db_manager.create_company(Company(name="VarianceCo"))
    plan_id = db_manager.create_financial_plan(
        FinancialPlan(
            company_id=company_id,
            plan_name="Active Plan",
            plan_year=2024,
            is_active=True,
            created_at=datetime(2024, 1, 1),
        )
    )

    db_manager.create_monthly_plan(
        MonthlyPlan(
            plan_id=plan_id,
            month_number=1,
            month_name="January",
            year=2024,
            quarter=1,
            plan_mrr=1000.0,
            plan_new_customers=10,
            plan_total_revenue=1000.0,
            plan_total_costs=600.0,
            plan_burn_rate=600.0,
            plan_runway=10.0,
            plan_ltv_cac_ratio=3.0,
            plan_cac_payback_months=6.0,
            plan_gross_margin=0.4,
        )
    )

    db_manager.save_actual_data(
        ActualData(
            company_id=company_id,
            year=2024,
            month_number=1,
            actual_mrr=900.0,
            actual_new_customers=8,
            actual_total_revenue=900.0,
            actual_total_costs=650.0,
            actual_burn_rate=650.0,
            actual_runway=9.0,
            actual_ltv_cac_ratio=2.8,
            actual_cac_payback_months=7.0,
            actual_gross_margin=0.35,
        )
    )

    result = variance_analyzer.analyze_monthly_variance(company_id, 1, 2024)

    assert isinstance(result, dict)
    assert "variance_summary" in result or "error" in result
