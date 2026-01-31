from datetime import date

from gigachat_analyst import GigaChatAnalyst


def test_no_date_nameerror():
    analyst = GigaChatAnalyst()
    assert analyst._safe_json_serialize(date.today()) == str(date.today())
