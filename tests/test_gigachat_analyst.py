from datetime import date, datetime

from gigachat_analyst import AnalysisType, GigaChatAnalyst


def test_no_date_nameerror():
    analyst = GigaChatAnalyst()
    assert analyst._safe_json_serialize(date.today()) == str(date.today())


def test_json_serialization_handles_datetime():
    analyst = GigaChatAnalyst()
    context = {
        "company": {"company_name": "TestCo"},
        "metrics": {},
        "data_summary": {},
        "created_at": datetime(2024, 1, 1, 12, 0, 0),
    }

    prompt = analyst._generate_prompt(
        AnalysisType.FULL_BUSINESS_ANALYSIS, context, None, "ru"
    )

    assert "2024-01-01T12:00:00" in prompt
