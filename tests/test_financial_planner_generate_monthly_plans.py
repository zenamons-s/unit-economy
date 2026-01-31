import math
from datetime import date, datetime

from database.db_manager import Company, FinancialPlan, db_manager
from services.financial_system.financial_planner import FinancialPlanner


def test_financial_planner_has_generate_monthly_plans():
    planner = FinancialPlanner()
    assert callable(getattr(planner, "generate_monthly_plans", None))


def test_generate_monthly_plans_returns_12_months(tmp_path):
    db_path = tmp_path / "planner.db"
    db_manager.set_db_path(str(db_path))
    db_manager.initialize_database()

    company_id = db_manager.create_company(Company(name="Planner Co"))
    plan_id = db_manager.create_financial_plan(
        FinancialPlan(company_id=company_id, plan_name="Plan", plan_year=2025)
    )

    assumptions = {
        "growth": {
            "monthly_growth_rate": 0.1,
            "monthly_churn_rate": 0.02,
            "starting_mrr": 10000.0,
            "starting_customers": 50,
            "starting_cash": 25000.0,
        },
        "costs": {
            "salary_cost": 12000.0,
            "marketing_cost": 4000.0,
            "infrastructure_cost": 2000.0,
            "other_cost": 1500.0,
            "cac": 800.0,
        },
    }

    planner = FinancialPlanner()
    monthly_plans = planner.generate_monthly_plans(plan_id, assumptions)

    assert len(monthly_plans) == 12

    for month_index, plan in enumerate(monthly_plans, start=1):
        assert isinstance(plan, dict)
        assert plan.get("month_number") == month_index

        for value in plan.values():
            assert value is not None
            assert not isinstance(value, (datetime, date))
            if isinstance(value, float):
                assert not math.isnan(value)
